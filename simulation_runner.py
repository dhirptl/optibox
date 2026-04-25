from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from inbound_generator import InboundBoxGenerator
from main import SimulationState, build_initial_state, run_tick_batch
from models import SimulationConfig
from shuttle_runner import ShuttleStepResult


@dataclass(frozen=True)
class SimulationRunMetrics:
    full_pallets_out_of_8: int
    pallets_completed: int
    avg_time_per_pallet: float


@dataclass(frozen=True)
class SimulationRunResult:
    duration_seconds: int
    events: List[dict]
    timeline: List[dict]
    metrics: SimulationRunMetrics
    final_metrics: SimulationRunMetrics


def run_simulation(
    ticks: int,
    config: Optional[SimulationConfig] = None,
    csv_path: Optional[str] = None,
    inbound_seed: Optional[int] = 42,
    inbound_per_tick: int = 1,
    print_every_tick: bool = True,
) -> SimulationState:
    """
    Convenience runner that wires:
    - initial state build (+ optional CSV preload)
    - inbound generation
    - per-tick execution
    - console printing for each move/progress event
    """
    if ticks < 0:
        raise ValueError("ticks must be >= 0")
    if inbound_per_tick < 1:
        raise ValueError("inbound_per_tick must be >= 1")

    state = build_initial_state(config=config, csv_path=csv_path, strict_positions=True)
    generator = InboundBoxGenerator(seed=inbound_seed)

    if state.initial_load_stats is not None:
        stats = state.initial_load_stats
        print(
            f"[init] loaded_rows={stats.rows_total} "
            f"placed_boxes={stats.placed_boxes} empty_rows={stats.rows_empty}"
        )

    for _ in range(ticks):
        inbound_boxes = generator.next_boxes(inbound_per_tick)
        inbound_id = ",".join(box.box_id for box in inbound_boxes)
        inbound_destination = ",".join(box.destination for box in inbound_boxes)

        results = run_tick_batch(state, inbound_boxes)

        if not print_every_tick:
            continue

        print(
            f"[t={state.t:05d}] inbound={inbound_id} "
            f"dest={inbound_destination}"
        )
        for result in results:
            if result.notes == "idle":
                continue
            print(
                f"  shuttle={result.shuttle_id} "
                f"task={result.task_type} "
                f"started={result.started_task} "
                f"finished={result.finished_task} "
                f"remaining={result.remaining_seconds} "
                f"state={result.notes}"
            )

    return state


def run_simulation_for_playback(
    ticks: int,
    config: Optional[SimulationConfig] = None,
    csv_path: Optional[str] = None,
    inbound_seed: Optional[int] = 42,
    inbound_per_tick: int = 1,
) -> SimulationRunResult:
    if ticks < 0:
        raise ValueError("ticks must be >= 0")
    if inbound_per_tick < 1:
        raise ValueError("inbound_per_tick must be >= 1")

    state = build_initial_state(config=config, csv_path=csv_path, strict_positions=True)
    generator = InboundBoxGenerator(seed=inbound_seed)
    events: List[dict] = []
    timeline: List[dict] = []
    completed_pallet_count = 0
    completed_durations: List[int] = []
    opened_at_tick_by_destination: Dict[str, int] = {}
    completed_pallets_by_destination: Dict[str, int] = {}
    reported_full_slots: set[tuple[int, int, str]] = set()
    previous_occupancy = _build_silo_occupancy_snapshot(state)

    initial_pallet_slots = _build_pallet_slots(state)
    initial_metrics = _build_metrics(
        completed_pallet_count,
        completed_durations,
        _count_full_slots(initial_pallet_slots),
    )
    timeline.append(
        {
            "t": 0,
            "metrics": initial_metrics,
            "pallet_slots": initial_pallet_slots,
            "shuttles": _build_shuttle_snapshot(state),
            "grid_changes": [],
            "action_message": "Awaiting simulation start...",
            "event_count": 0,
        }
    )

    for _ in range(ticks):
        inbound_boxes = generator.next_boxes(inbound_per_tick)
        results = run_tick_batch(state, inbound_boxes)
        tick = state.t

        for inbound_box in inbound_boxes:
            events.append(
                {
                    "t": tick,
                    "type": "inbound",
                    "message": f"Inbound {inbound_box.box_id} -> {inbound_box.destination}",
                    "destination": inbound_box.destination,
                }
            )
        _append_task_events(events, tick, results)

        active_destinations = sorted(state.dispatcher.active_pallets.keys())
        for destination in active_destinations:
            opened_at_tick_by_destination.setdefault(destination, max(0, tick - 1))

        for destination, shipped_count in state.shipped_by_destination.items():
            completed_now = shipped_count // state.config.pallet_size
            completed_before = completed_pallets_by_destination.get(destination, 0)
            if completed_now > completed_before:
                new_completions = completed_now - completed_before
                for _ in range(new_completions):
                    completed_pallet_count += 1
                    started_tick = opened_at_tick_by_destination.get(destination, tick)
                    completed_durations.append(max(1, tick - started_tick))
                    events.append(
                        {
                            "t": tick,
                            "type": "pallet_ready",
                            "message": f"Pallet {destination} full ({state.config.pallet_size}/{state.config.pallet_size}) -> SHIP",
                            "destination": destination,
                        }
                    )
                completed_pallets_by_destination[destination] = completed_now
                opened_at_tick_by_destination[destination] = tick

        pallet_slots = _build_pallet_slots(state)
        for slot in pallet_slots:
            if slot["filled"] == slot["capacity"]:
                destination = slot["destination"]
                if destination is None:
                    continue
                slot_key = (slot["robot_id"], slot["slot_id"], destination)
                if slot_key in reported_full_slots:
                    continue
                reported_full_slots.add(slot_key)
                events.append(
                    {
                        "t": tick,
                        "type": "pallet_slot_full",
                        "message": f"R{slot['robot_id']} S{slot['slot_id']:02d}: {slot['filled']}/{slot['capacity']} -> SHIP",
                        "destination": destination,
                    }
                )

        current_full_slots = _count_full_slots(pallet_slots)
        metrics = _build_metrics(
            completed_pallet_count,
            completed_durations,
            current_full_slots,
        )
        current_occupancy = _build_silo_occupancy_snapshot(state)
        grid_changes = _build_grid_changes(previous_occupancy, current_occupancy)
        previous_occupancy = current_occupancy
        timeline.append(
            {
                "t": tick,
                "metrics": metrics,
                "pallet_slots": pallet_slots,
                "shuttles": _build_shuttle_snapshot(state),
                "grid_changes": grid_changes,
                "action_message": _pick_action_message(results),
                "event_count": len(events),
            }
        )

    final_pallet_slots = _build_pallet_slots(state)
    final_full_slots = _count_full_slots(final_pallet_slots)
    final_metrics = _build_metrics(
        completed_pallet_count,
        completed_durations,
        final_full_slots,
    )
    if timeline:
        timeline[-1]["final_metrics"] = final_metrics

    serializable_final = SimulationRunMetrics(
        full_pallets_out_of_8=final_metrics["full_pallets_out_of_8"],
        pallets_completed=final_metrics["pallets_completed"],
        avg_time_per_pallet=final_metrics["avg_time_per_pallet"],
    )
    return SimulationRunResult(
        duration_seconds=ticks,
        events=events,
        timeline=timeline,
        metrics=serializable_final,
        final_metrics=serializable_final,
    )


def write_simulation_log(path: str, payload: SimulationRunResult) -> None:
    serializable = {
        "duration_seconds": payload.duration_seconds,
        "metrics": {
            "full_pallets_out_of_8": payload.metrics.full_pallets_out_of_8,
            "pallets_completed": payload.metrics.pallets_completed,
            "avg_time_per_pallet": payload.metrics.avg_time_per_pallet,
        },
        "final_metrics": {
            "full_pallets_out_of_8": payload.final_metrics.full_pallets_out_of_8,
            "pallets_completed": payload.final_metrics.pallets_completed,
            "avg_time_per_pallet": payload.final_metrics.avg_time_per_pallet,
        },
        "events": payload.events,
        "timeline": payload.timeline,
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(serializable, file, indent=2)


def _append_task_events(events: List[dict], tick: int, results: List[ShuttleStepResult]) -> None:
    for result in results:
        if result.notes == "idle":
            continue
        if result.started_task and result.task_type is not None:
            events.append(
                {
                    "t": tick,
                    "type": "task_started",
                    "message": f"{result.shuttle_id} started {result.task_type}",
                    "shuttle_id": result.shuttle_id,
                    "task_type": result.task_type,
                }
            )
        if result.finished_task and result.task_type is not None:
            completion_message = f"{result.shuttle_id} finished {result.task_type}"
            if result.completed_destination:
                completion_message += f" for {result.completed_destination}"
            events.append(
                {
                    "t": tick,
                    "type": "task_finished",
                    "message": completion_message,
                    "shuttle_id": result.shuttle_id,
                    "task_type": result.task_type,
                    "destination": result.completed_destination,
                    "box_id": result.completed_box_id,
                }
            )


def _build_pallet_slots(state: SimulationState) -> List[dict]:
    active_destinations = sorted(state.dispatcher.active_pallets.keys())
    slots: List[dict] = []
    for idx in range(8):
        destination = active_destinations[idx] if idx < len(active_destinations) else None
        filled = 0
        if destination is not None:
            pallet = state.dispatcher.active_pallets.get(destination)
            if pallet is not None:
                filled = min(state.config.pallet_size, len(pallet.shipped_box_ids))
        slots.append(
            {
                "slot_id": (idx % 4) + 1,
                "robot_id": 1 if idx < 4 else 2,
                "destination": destination,
                "filled": filled,
                "capacity": state.config.pallet_size,
            }
        )
    return slots


def _build_shuttle_snapshot(state: SimulationState) -> List[dict]:
    return [
        {
            "shuttle_id": shuttle.shuttle_id,
            "aisle": shuttle.aisle,
            "y": shuttle.y,
            "x": shuttle.current_x,
            "task_type": shuttle.active_task.task_type.value if shuttle.active_task else None,
        }
        for shuttle in state.shuttles
    ]


def _build_metrics(
    completed_pallet_count: int,
    completed_durations: List[int],
    current_full_slots: int,
) -> dict:
    avg_time = float(sum(completed_durations) / len(completed_durations)) if completed_durations else 0.0
    return {
        "full_pallets_out_of_8": current_full_slots,
        "pallets_completed": completed_pallet_count,
        "avg_time_per_pallet": round(avg_time, 2),
    }


def _count_full_slots(pallet_slots: List[dict]) -> int:
    return sum(
        1
        for slot in pallet_slots
        if slot["destination"] is not None and slot["filled"] == slot["capacity"] == 12
    )


def _build_silo_occupancy_snapshot(state: SimulationState) -> Dict[str, Optional[dict]]:
    snapshot: Dict[str, Optional[dict]] = {}
    for box_id, position in state.silo.box_position.items():
        slot = state.silo.get_slot(position)
        if slot is None or slot.box is None:
            continue
        snapshot[_format_position(position)] = {
            "box_id": box_id,
            "source": slot.box.source,
            "destination": slot.box.destination,
            "bulk": slot.box.bulk_number,
        }
    return snapshot


def _build_grid_changes(
    previous: Dict[str, Optional[dict]],
    current: Dict[str, Optional[dict]],
) -> List[dict]:
    changes: List[dict] = []
    for position in sorted(set(previous.keys()) | set(current.keys())):
        before = previous.get(position)
        after = current.get(position)
        if before == after:
            continue
        changes.append(
            {
                "position": position,
                "before": before,
                "after": after,
            }
        )
    return changes


def _format_position(position: tuple[int, int, int, int, int]) -> str:
    aisle, side, x, y, z = position
    return (
        f"{aisle:02d}"
        f"{side:02d}"
        f"{x:03d}"
        f"{y:02d}"
        f"{z:02d}"
    )


def _pick_action_message(results: List[ShuttleStepResult]) -> str:
    for result in results:
        if result.finished_task and result.task_type:
            return f"{result.shuttle_id} finished {result.task_type}"
    for result in results:
        if result.started_task and result.task_type:
            return f"{result.shuttle_id} started {result.task_type}"
    for result in results:
        if result.task_type:
            return f"{result.shuttle_id} running {result.task_type}"
    return "Awaiting simulation start..."


if __name__ == "__main__":
    run_simulation(
        ticks=20,
        csv_path="silo-semi-empty.csv",
        inbound_seed=7,
        print_every_tick=True,
    )
