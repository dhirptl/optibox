from __future__ import annotations

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
    Single global-tick owner.

    Ordered phases:
    1) pallet check
    2) inbound decision + task creation
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
    # We only enqueue tasks that are fully decided and executable.
    if inbound_box is not None:
        assigned_shuttle = _pick_next_shuttle(state)
        _assign_task_from_inbound(state, assigned_shuttle, inbound_box)

    # Phase 3: run one second of shuttle execution.
    results = step_all_shuttles(state.shuttles, state.silo, state.config)

    # Phase 4: advance global time exactly once.
    state.t += 1
    return results


def _assign_task_from_inbound(
    state: SimulationState,
    shuttle: Shuttle,
    inbound_box: Box,
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
    )
    if store_decision is None:
        # No legal storage position was found under corridor policies.
        return

    pick_slot_obj = state.silo.get_slot(pick_slot)
    outbound_box = pick_slot_obj.box if pick_slot_obj is not None else None
    # Enqueue one fully defined store-and-pick cycle.
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


def _find_nearest_outbound_pick_slot(
    silo: Silo,
    lane_aisle: int,
    lane_y: int,
    active_destinations: set[str],
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

