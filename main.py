from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from dispatch import (
    close_completed_pallets,
    count_boxes_by_destination,
    decide_inbound,
    open_eligible_pallets,
)
from models import (
    Box,
    DispatcherState,
    Position,
    Shuttle,
    ShuttleTask,
    ShuttleTaskType,
    SimulationConfig,
    Silo,
    build_empty_silo,
)
from shuttle_runner import ShuttleStepResult, step_all_shuttles
from slot_heuristic import choose_store_slot_on_path
from state_loader import CsvLoadStats, preload_silo_from_csv


@dataclass
class SimulationState:
    # Global simulation container mutated tick by tick.
    config: SimulationConfig
    silo: Silo
    shuttles: List[Shuttle]
    dispatcher: DispatcherState = field(default_factory=DispatcherState)
    t: int = 0
    next_shuttle_index: int = 0
    initial_load_stats: Optional[CsvLoadStats] = None
    shipped_boxes_total: int = 0
    shipped_by_destination: Counter[str] = field(default_factory=Counter)
    shipped_pallets_total: int = 0


def build_initial_state(
    config: Optional[SimulationConfig] = None,
    csv_path: Optional[str] = None,
    strict_positions: bool = True,
) -> SimulationState:
    # Build a full empty grid plus one shuttle per (aisle, y).
    cfg = config or SimulationConfig()
    silo = build_empty_silo(cfg)
    shuttles = _build_shuttles(cfg)
    state = SimulationState(config=cfg, silo=silo, shuttles=shuttles)

    # Optional startup preload from snapshot CSV.
    if csv_path:
        state.initial_load_stats = preload_silo_from_csv(
            csv_path=csv_path,
            silo=state.silo,
            strict_positions=strict_positions,
        )

    return state


def run_tick(state: SimulationState, inbound_box: Optional[Box]) -> List[ShuttleStepResult]:
    """
    Backward-compatible single-inbound tick.
    """
    inbound_boxes: List[Box] = []
    if inbound_box is not None:
        inbound_boxes.append(inbound_box)
    return run_tick_batch(state, inbound_boxes)


def run_tick_batch(
    state: SimulationState,
    inbound_boxes: Iterable[Box],
) -> List[ShuttleStepResult]:
    """
    Single global-tick owner.

    Ordered phases:
    1) pallet check
    2) inbound decision + task creation (for all inbound events in this tick)
    3) shuttle step
    4) t += 1
    """
    # Phase 1: pallet state maintenance and activation.
    # Close finished pallets first, then open new eligible ones from current silo state.
    close_completed_pallets(state.dispatcher)
    all_boxes = _iter_silo_boxes(state.silo)
    available = count_boxes_by_destination(all_boxes)
    open_eligible_pallets(state.dispatcher, available, state.config)

    # Phase 2: inbound is known at x=0, create executable task.
    # Inbound can only be assigned to shuttles that are available at x=0.
    # We also reserve slots already committed by active/queued tasks so new
    # assignments in this tick do not collide with future planned placements/picks.
    reserved_store_slots, reserved_pick_slots = _collect_reserved_slots(state.shuttles)
    ready_shuttles = get_ready_shuttles_for_inbound(state)
    inbound_list = list(inbound_boxes)
    for shuttle, inbound_box in zip(ready_shuttles, inbound_list):
        _assign_task_from_inbound(
            state,
            shuttle,
            inbound_box,
            reserved_store_slots,
            reserved_pick_slots,
        )

    # For remaining ready shuttles with no inbound assigned this tick, try to
    # run outbound work (or relocate if blocked).
    for shuttle in ready_shuttles[len(inbound_list) :]:
        _assign_non_inbound_task(
            state,
            shuttle,
            reserved_store_slots,
            reserved_pick_slots,
        )

    # Phase 3: run one second of shuttle execution.
    results = step_all_shuttles(state.shuttles, state.silo, state.config)
    _update_shipping_counters(state, results)
    _apply_completed_shipments(state, results)

    # Phase 4: advance global time exactly once.
    state.t += 1
    return results


def _assign_task_from_inbound(
    state: SimulationState,
    shuttle: Shuttle,
    inbound_box: Box,
    reserved_store_slots: set[Position],
    reserved_pick_slots: set[Position],
) -> None:
    # Decide immediately at x=0 whether this inbound is cross-dock or store-path.
    decision = decide_inbound(inbound_box, state.dispatcher)
    if decision is None:
        return

    if decision.should_cross_dock:
        # Fast path: destination already has active pallet, so stay at head.
        shuttle.enqueue(
            ShuttleTask(
                task_type=ShuttleTaskType.INBOUND_CROSS_DOCK,
                inbound_box=inbound_box,
                drop_to_head=True,
            )
        )
        return

    # Store-path: choose outbound target and slot according to corridor rules.
    # Outbound target is selected before store slot so storage can be "on the way".
    pick_slot = _find_nearest_outbound_pick_slot(
        silo=state.silo,
        lane_aisle=shuttle.aisle,
        lane_y=shuttle.y,
        active_destinations=set(state.dispatcher.active_pallets.keys()),
        blocked_positions=reserved_pick_slots,
    )
    if pick_slot is None:
        # No shippable target in this lane right now.
        return

    outbound_x = pick_slot[2]
    store_decision = choose_store_slot_on_path(
        silo=state.silo,
        inbound_box=inbound_box,
        lane_aisle=shuttle.aisle,
        lane_y=shuttle.y,
        outbound_x=outbound_x,
        blocked_positions=reserved_store_slots,
    )
    if store_decision is None:
        # No legal storage position was found under corridor policies.
        return

    pick_slot_obj = state.silo.get_slot(pick_slot)
    outbound_box = pick_slot_obj.box if pick_slot_obj is not None else None
    # Enqueue one fully defined store-and-pick cycle.
    reserved_store_slots.add(store_decision.position)
    reserved_pick_slots.add(pick_slot)
    shuttle.enqueue(
        ShuttleTask(
            task_type=ShuttleTaskType.INBOUND_STORE_AND_PICK,
            inbound_box=inbound_box,
            outbound_box=outbound_box,
            store_slot=store_decision.position,
            pick_slot=pick_slot,
            drop_to_head=True,
        )
    )


def _assign_non_inbound_task(
    state: SimulationState,
    shuttle: Shuttle,
    reserved_store_slots: set[Position],
    reserved_pick_slots: set[Position],
) -> None:
    pick_slot = _find_nearest_outbound_pick_slot(
        silo=state.silo,
        lane_aisle=shuttle.aisle,
        lane_y=shuttle.y,
        active_destinations=set(state.dispatcher.active_pallets.keys()),
        blocked_positions=reserved_pick_slots,
    )
    if pick_slot is None:
        return

    pick_slot_obj = state.silo.get_slot(pick_slot)
    if pick_slot_obj is None or pick_slot_obj.box is None:
        return

    # If outbound target is in z=2 and z=1 is occupied, relocate blocker first.
    if pick_slot[4] == 2:
        front_slot_pos: Position = (
            pick_slot[0],
            pick_slot[1],
            pick_slot[2],
            pick_slot[3],
            1,
        )
        front_slot = state.silo.get_slot(front_slot_pos)
        if front_slot is not None and front_slot.box is not None:
            relocation = choose_store_slot_on_path(
                silo=state.silo,
                inbound_box=front_slot.box,
                lane_aisle=shuttle.aisle,
                lane_y=shuttle.y,
                outbound_x=pick_slot[2],
                blocked_positions=reserved_store_slots,
            )
            if relocation is None:
                return

            reserved_store_slots.add(relocation.position)
            reserved_pick_slots.add(front_slot_pos)
            shuttle.enqueue(
                ShuttleTask(
                    task_type=ShuttleTaskType.RELOCATE,
                    inbound_box=front_slot.box,
                    store_slot=relocation.position,
                    pick_slot=front_slot_pos,
                    drop_to_head=False,
                )
            )
            return

    # Normal outbound-only extraction to x=0.
    reserved_pick_slots.add(pick_slot)
    shuttle.enqueue(
        ShuttleTask(
            task_type=ShuttleTaskType.OUTBOUND_ONLY,
            outbound_box=pick_slot_obj.box,
            pick_slot=pick_slot,
            drop_to_head=True,
        )
    )


def _find_nearest_outbound_pick_slot(
    silo: Silo,
    lane_aisle: int,
    lane_y: int,
    active_destinations: set[str],
    blocked_positions: set[Position],
) -> Optional[Position]:
    # Scan the shuttle lane and keep only boxes for active pallet destinations.
    candidates: List[Position] = []
    for position, slot in silo.slots.items():
        aisle, _side, _x, y, _z = position
        if aisle != lane_aisle or y != lane_y:
            continue
        if slot.box is None:
            continue
        if slot.box.destination not in active_destinations:
            continue
        if position in blocked_positions:
            continue
        candidates.append(position)

    if not candidates:
        return None
    # Stable nearest-by-x tie break, then full position tuple.
    candidates.sort(key=lambda p: (p[2], p))
    return candidates[0]


def _iter_silo_boxes(silo: Silo) -> Iterable[Box]:
    # Utility used by dispatch to build destination inventory counters.
    for slot in silo.slots.values():
        if slot.box is not None:
            yield slot.box


def _pick_next_shuttle(state: SimulationState) -> Shuttle:
    # Deterministic round-robin assignment for inbound events.
    if not state.shuttles:
        raise ValueError("No shuttles configured.")
    idx = state.next_shuttle_index % len(state.shuttles)
    shuttle = state.shuttles[idx]
    state.next_shuttle_index = (idx + 1) % len(state.shuttles)
    return shuttle


def _build_shuttles(config: SimulationConfig) -> List[Shuttle]:
    # Build one shuttle per (aisle, y) as discussed in the model assumptions.
    shuttles: List[Shuttle] = []
    for aisle in range(1, config.aisles + 1):
        for y in range(1, config.y_levels + 1):
            shuttles.append(
                Shuttle(
                    shuttle_id=f"A{aisle}-Y{y}",
                    aisle=aisle,
                    y=y,
                )
            )
    return shuttles


def get_ready_shuttles_for_inbound(state: SimulationState) -> List[Shuttle]:
    """
    Shuttles that are allowed to receive a new inbound this tick.

    Rule: shuttle must be available at x=0 and have no pending work.
    """
    ready: List[Shuttle] = []
    for shuttle in state.shuttles:
        if shuttle.active_task is not None:
            continue
        if shuttle.queue:
            continue
        if shuttle.current_x != 0:
            continue
        ready.append(shuttle)
    return ready


def _collect_reserved_slots(shuttles: List[Shuttle]) -> tuple[set[Position], set[Position]]:
    reserved_store: set[Position] = set()
    reserved_pick: set[Position] = set()
    for shuttle in shuttles:
        if shuttle.active_task is not None:
            if shuttle.active_task.store_slot is not None:
                reserved_store.add(shuttle.active_task.store_slot)
            if shuttle.active_task.pick_slot is not None:
                reserved_pick.add(shuttle.active_task.pick_slot)
        for queued_task in shuttle.queue:
            if queued_task.store_slot is not None:
                reserved_store.add(queued_task.store_slot)
            if queued_task.pick_slot is not None:
                reserved_pick.add(queued_task.pick_slot)
    return reserved_store, reserved_pick


def _update_shipping_counters(
    state: SimulationState,
    results: List[ShuttleStepResult],
) -> None:
    """
    Count shipped boxes and completed pallets (12 shipped boxes per destination).
    """
    for result in results:
        if not result.finished_task:
            continue
        if result.shipped_destination is None:
            continue
        destination = result.shipped_destination
        state.shipped_boxes_total += 1
        state.shipped_by_destination[destination] += 1
        # Each new multiple of 12 means one more fully shipped pallet.
        if state.shipped_by_destination[destination] % state.config.pallet_size == 0:
            state.shipped_pallets_total += 1


def get_shipped_pallets_total(state: SimulationState) -> int:
    return state.shipped_pallets_total


def _apply_completed_shipments(
    state: SimulationState,
    results: List[ShuttleStepResult],
) -> None:
    for result in results:
        if not result.finished_task:
            continue
        destination = result.shipped_destination
        if destination is None:
            continue
        pallet = state.dispatcher.active_pallets.get(destination)
        if pallet is None:
            continue
        box_id = result.completed_box_id or f"{destination}-t{state.t:05d}-{result.shuttle_id}"
        if box_id not in pallet.shipped_box_ids:
            pallet.shipped_box_ids.append(box_id)

