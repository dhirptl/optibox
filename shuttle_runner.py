from __future__ import annotations

from dataclasses import dataclass
from math import pi, sin
from typing import List, Optional

from models import Box, Position, Shuttle, ShuttleTask, ShuttleTaskType, Silo, SimulationConfig


@dataclass(frozen=True)
class ShuttleStepResult:
    shuttle_id: str
    started_task: bool
    finished_task: bool
    remaining_seconds: int
    task_type: Optional[str]
    shipped_destination: Optional[str]
    completed_box_id: Optional[str]
    completed_destination: Optional[str]
    current_x: int
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
    completed_box_id: Optional[str] = None
    completed_destination: Optional[str] = None

    # If shuttle is idle and has pending work, start exactly one task.
    if shuttle.active_task is None and shuttle.queue:
        shuttle.active_task = shuttle.queue.pop(0)
        shuttle.is_idle = False
        started_task = True
        shuttle.carrying = _get_task_primary_carry(shuttle.active_task)
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
            shipped_destination=None,
            completed_box_id=None,
            completed_destination=None,
            current_x=shuttle.current_x,
            notes="idle",
        )

    # Consume exactly one simulation second from task duration.
    if shuttle.active_task.remaining_seconds > 0:
        shuttle.active_task.remaining_seconds -= 1
        shuttle.current_x = _estimate_shuttle_x(shuttle.active_task)

    # When remaining time reaches zero, apply end-of-task state transitions.
    if shuttle.active_task.remaining_seconds == 0:
        completed_task = shuttle.active_task
        completed_destination = _task_destination(completed_task, silo)
        completed_box_id = _task_box_id(completed_task, silo)
        _finalize_task_effects(shuttle, silo)
        shuttle.active_task = None
        shuttle.is_idle = True
        shuttle.carrying = None
        finished_task = True
        return ShuttleStepResult(
            shuttle_id=shuttle.shuttle_id,
            started_task=started_task,
            finished_task=finished_task,
            remaining_seconds=0,
            task_type=completed_task.task_type.value,
            shipped_destination=_get_shipped_destination(completed_task),
            completed_box_id=completed_box_id,
            completed_destination=completed_destination,
            current_x=shuttle.current_x,
            notes="task_completed",
        )

    return ShuttleStepResult(
        shuttle_id=shuttle.shuttle_id,
        started_task=started_task,
        finished_task=finished_task,
        remaining_seconds=shuttle.active_task.remaining_seconds,
        task_type=shuttle.active_task.task_type.value,
        shipped_destination=None,
        completed_box_id=None,
        completed_destination=None,
        current_x=shuttle.current_x,
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
    task.total_seconds = task.remaining_seconds


def _estimate_task_seconds(
    shuttle: Shuttle,
    task: ShuttleTask,
    handling_seconds: int,
) -> int:
    """
    Estimate full duration with updated timing rules:
    - Inbound pick + store: handling + store_x
    - Stored pick + deliver to x=0: handling + pick_x
    - Instant cross-dock at x=0: 20 seconds fixed
    """
    if task.task_type == ShuttleTaskType.INBOUND_CROSS_DOCK:
        return handling_seconds * 2
    if task.task_type == ShuttleTaskType.RELOCATE:
        if task.pick_slot is not None and task.store_slot is not None:
            return handling_seconds + abs(task.store_slot[2] - task.pick_slot[2])
        return handling_seconds

    total = 0
    has_rule_applied = False

    # Rule 1: take inbound at x=0 and store at x=store_x.
    if task.inbound_box is not None and task.store_slot is not None:
        store_x = task.store_slot[2]
        total += handling_seconds + store_x
        has_rule_applied = True

    # Rule 2: pick a stored box at x=pick_x and deliver to x=0.
    if task.pick_slot is not None and task.drop_to_head:
        pick_x = task.pick_slot[2]
        total += handling_seconds + pick_x
        has_rule_applied = True

    # Outbound-only fallback if used without inbound in same task.
    if task.pick_slot is not None and task.inbound_box is None and task.drop_to_head:
        pick_x = task.pick_slot[2]
        total = handling_seconds + pick_x
        has_rule_applied = True

    if has_rule_applied:
        return max(total, handling_seconds)

    # Safety fallback for any task shape not covered above.
    current_x = shuttle.current_x
    if task.drop_to_head:
        return handling_seconds + abs(current_x - 0)
    return handling_seconds


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


def _get_shipped_destination(task: ShuttleTask) -> Optional[str]:
    """
    Return shipped destination when a completed task actually ships a box
    to head/pallet. Non-shipping tasks return None.
    """
    if task.task_type == ShuttleTaskType.INBOUND_CROSS_DOCK:
        return task.inbound_box.destination if task.inbound_box is not None else None
    if task.task_type in {
        ShuttleTaskType.INBOUND_STORE_AND_PICK,
        ShuttleTaskType.OUTBOUND_ONLY,
    }:
        if task.drop_to_head and task.outbound_box is not None:
            return task.outbound_box.destination
    return None


def _get_task_primary_carry(task: ShuttleTask) -> Optional[Box]:
    """
    Best-effort payload marker for frontend state.
    """
    if task.task_type in {
        ShuttleTaskType.INBOUND_CROSS_DOCK,
        ShuttleTaskType.INBOUND_STORE_AND_PICK,
        ShuttleTaskType.RELOCATE,
    }:
        return task.inbound_box
    if task.task_type == ShuttleTaskType.OUTBOUND_ONLY:
        return task.outbound_box
    return None


def _task_destination(task: ShuttleTask, silo: Silo) -> Optional[str]:
    if task.inbound_box is not None and task.task_type == ShuttleTaskType.INBOUND_CROSS_DOCK:
        return task.inbound_box.destination
    if task.outbound_box is not None:
        return task.outbound_box.destination
    if task.pick_slot is not None:
        pick_slot = silo.get_slot(task.pick_slot)
        if pick_slot is not None and pick_slot.box is not None:
            return pick_slot.box.destination
    return None


def _task_box_id(task: ShuttleTask, silo: Silo) -> Optional[str]:
    if task.inbound_box is not None and task.task_type == ShuttleTaskType.INBOUND_CROSS_DOCK:
        return task.inbound_box.box_id
    if task.outbound_box is not None:
        return task.outbound_box.box_id
    if task.pick_slot is not None:
        pick_slot = silo.get_slot(task.pick_slot)
        if pick_slot is not None and pick_slot.box is not None:
            return pick_slot.box.box_id
    return None


def _estimate_shuttle_x(task: ShuttleTask) -> int:
    if task.total_seconds <= 0:
        return 0
    if task.task_type == ShuttleTaskType.INBOUND_CROSS_DOCK:
        return 0

    target_x = 0
    if task.store_slot is not None:
        target_x = max(target_x, task.store_slot[2])
    if task.pick_slot is not None:
        target_x = max(target_x, task.pick_slot[2])
    if target_x <= 0:
        return 0

    elapsed = task.total_seconds - task.remaining_seconds
    ratio = min(1.0, max(0.0, elapsed / task.total_seconds))
    # Smooth out-and-back motion so UI can animate meaningful X movement.
    return int(round(target_x * sin(pi * ratio)))

