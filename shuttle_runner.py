from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from models import Position, Shuttle, ShuttleTask, ShuttleTaskType, Silo, SimulationConfig


@dataclass(frozen=True)
class ShuttleStepResult:
    shuttle_id: str
    started_task: bool
    finished_task: bool
    remaining_seconds: int
    task_type: Optional[str]
    notes: str


def step_shuttle(
    shuttle: Shuttle,
    silo: Silo,
    config: SimulationConfig,
) -> ShuttleStepResult:
    """
    Advance one shuttle by one simulation tick.

    Important:
    - This function never advances global time.
    - It only mutates shuttle/task/silo state for the current tick.
    """
    started_task = False
    finished_task = False

    # If shuttle is idle and has pending work, start exactly one task.
    if shuttle.active_task is None and shuttle.queue:
        shuttle.active_task = shuttle.queue.pop(0)
        shuttle.is_idle = False
        started_task = True
        _initialize_task_duration(shuttle, config)

    # Nothing to execute this tick.
    if shuttle.active_task is None:
        shuttle.is_idle = True
        return ShuttleStepResult(
            shuttle_id=shuttle.shuttle_id,
            started_task=started_task,
            finished_task=finished_task,
            remaining_seconds=0,
            task_type=None,
            notes="idle",
        )

    # Consume exactly one simulation second from task duration.
    if shuttle.active_task.remaining_seconds > 0:
        shuttle.active_task.remaining_seconds -= 1

    # When remaining time reaches zero, apply end-of-task state transitions.
    if shuttle.active_task.remaining_seconds == 0:
        completed_task = shuttle.active_task
        _finalize_task_effects(shuttle, silo)
        shuttle.active_task = None
        shuttle.is_idle = True
        finished_task = True
        return ShuttleStepResult(
            shuttle_id=shuttle.shuttle_id,
            started_task=started_task,
            finished_task=finished_task,
            remaining_seconds=0,
            task_type=completed_task.task_type.value,
            notes="task_completed",
        )

    return ShuttleStepResult(
        shuttle_id=shuttle.shuttle_id,
        started_task=started_task,
        finished_task=finished_task,
        remaining_seconds=shuttle.active_task.remaining_seconds,
        task_type=shuttle.active_task.task_type.value,
        notes="task_in_progress",
    )


def step_all_shuttles(
    shuttles: List[Shuttle],
    silo: Silo,
    config: SimulationConfig,
) -> List[ShuttleStepResult]:
    """
    Deterministic per-tick processing for all shuttles.
    Caller should pass shuttles in a stable order.
    """
    return [step_shuttle(shuttle, silo, config) for shuttle in shuttles]


def _initialize_task_duration(shuttle: Shuttle, config: SimulationConfig) -> None:
    task = shuttle.active_task
    if task is None:
        return

    task.remaining_seconds = _estimate_task_seconds(
        shuttle=shuttle,
        task=task,
        handling_seconds=config.handling_seconds,
    )


def _estimate_task_seconds(
    shuttle: Shuttle,
    task: ShuttleTask,
    handling_seconds: int,
) -> int:
    """
    Estimate full duration using (handling + distance) per movement leg.
    """
    current_x = shuttle.current_x
    total = 0

    if task.task_type == ShuttleTaskType.INBOUND_CROSS_DOCK:
        # Both operations happen at x=0.
        return handling_seconds * 2

    # Start from head if we need inbound pickup at x=0.
    if task.inbound_box is not None:
        total += _leg_seconds(current_x=current_x, target_x=0, handling_seconds=handling_seconds)
        current_x = 0

    # Leg: head/current -> storage point (drop inbound).
    if task.store_slot is not None:
        store_x = task.store_slot[2]
        total += _leg_seconds(current_x=current_x, target_x=store_x, handling_seconds=handling_seconds)
        current_x = store_x

    # Leg: storage/current -> outbound pick point.
    if task.pick_slot is not None:
        pick_x = task.pick_slot[2]
        total += _leg_seconds(current_x=current_x, target_x=pick_x, handling_seconds=handling_seconds)
        current_x = pick_x

    # Final leg: outbound/current -> head for shipping.
    if task.drop_to_head:
        total += _leg_seconds(current_x=current_x, target_x=0, handling_seconds=handling_seconds)

    # Keep a minimum positive duration to avoid zero-time tasks.
    return max(total, handling_seconds)


def _leg_seconds(current_x: int, target_x: int, handling_seconds: int) -> int:
    return handling_seconds + abs(target_x - current_x)


def _finalize_task_effects(shuttle: Shuttle, silo: Silo) -> None:
    task = shuttle.active_task
    if task is None:
        return

    # In this simplified runner, physical box mutations are applied at
    # completion time to keep the tick contract straightforward and deterministic.
    if task.store_slot is not None and task.inbound_box is not None:
        silo.place_box(task.store_slot, task.inbound_box)

    if task.pick_slot is not None:
        # Box is removed from silo because it is now considered picked for shipping.
        _ = silo.remove_box(task.pick_slot)

    # Most cycles end by returning to head.
    shuttle.current_x = 0 if task.drop_to_head else shuttle.current_x

