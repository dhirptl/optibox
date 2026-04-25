from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from models import Box, Position, Silo


@dataclass(frozen=True)
class StoreSlotDecision:
    """
    Result of selecting where to store inbound box during store-and-pick cycle.
    """

    position: Position
    reason: str


def choose_store_slot_on_path(
    silo: Silo,
    inbound_box: Box,
    lane_aisle: int,
    lane_y: int,
    outbound_x: int,
) -> Optional[StoreSlotDecision]:
    """
    Corridor storage policy for one shuttle lane.

    Priority:
    1) On-path same-destination stacking:
       If we encounter z=2 with same destination and z=1 is empty, store at z=1.
    2) On-path nearest valid z=2 empty slot.
    3) If nothing exists on-path, allow overshoot (x > outbound_x) and apply
       the same two priorities in that area.

    Important restriction:
    - Never place at z=1 in front of a different destination box at z=2.
    """
    # Step 1: try "smart stacking" first to reduce future relocations.
    # If we can place at z=1 in front of same-destination z=2, we do it.
    same_destination_stack = _find_on_path_same_destination_stack_slot(
        silo=silo,
        inbound_box=inbound_box,
        lane_aisle=lane_aisle,
        lane_y=lane_y,
        outbound_x=outbound_x,
    )
    if same_destination_stack is not None:
        return StoreSlotDecision(
            position=same_destination_stack,
            reason="on_path_same_destination_stack_at_z1",
        )

    # Step 2: fallback behavior if no same-destination stack slot exists.
    # Place in nearest legal z=2 location along the same path.
    z2_slot = _find_nearest_on_path_empty_z2_slot(
        silo=silo,
        lane_aisle=lane_aisle,
        lane_y=lane_y,
        outbound_x=outbound_x,
    )
    if z2_slot is not None:
        return StoreSlotDecision(
            position=z2_slot,
            reason="fallback_empty_z2_on_path",
        )

    # Step 3: worst-case fallback (overshoot).
    # Search after outbound_x with the same rules:
    #   (a) same-destination stack at z=1, else
    #   (b) nearest empty z=2.
    overshoot_stack = _find_overshoot_same_destination_stack_slot(
        silo=silo,
        inbound_box=inbound_box,
        lane_aisle=lane_aisle,
        lane_y=lane_y,
        outbound_x=outbound_x,
    )
    if overshoot_stack is not None:
        return StoreSlotDecision(
            position=overshoot_stack,
            reason="overshoot_same_destination_stack_at_z1",
        )

    overshoot_z2_slot = _find_nearest_overshoot_empty_z2_slot(
        silo=silo,
        lane_aisle=lane_aisle,
        lane_y=lane_y,
        outbound_x=outbound_x,
    )
    if overshoot_z2_slot is not None:
        return StoreSlotDecision(
            position=overshoot_z2_slot,
            reason="overshoot_fallback_empty_z2",
        )

    # No legal slot found on-path or after outbound_x.
    return None


def _find_on_path_same_destination_stack_slot(
    silo: Silo,
    inbound_box: Box,
    lane_aisle: int,
    lane_y: int,
    outbound_x: int,
) -> Optional[Position]:
    # Walk from head (x=1) to outbound target and pick earliest valid stack slot.
    for x in _on_path_x_values(outbound_x):
        for side in (1, 2):
            z2_pos: Position = (lane_aisle, side, x, lane_y, 2)
            z1_pos: Position = (lane_aisle, side, x, lane_y, 1)

            z2_slot = silo.get_slot(z2_pos)
            z1_slot = silo.get_slot(z1_pos)
            if z2_slot is None or z1_slot is None:
                continue
            # z=2 must already contain a box (same destination target).
            if z2_slot.box is None:
                continue
            if z2_slot.box.destination != inbound_box.destination:
                continue
            # To stack at z=1, the front position must be empty.
            if not z1_slot.is_empty:
                continue
            return z1_pos
    return None


def _find_nearest_on_path_empty_z2_slot(
    silo: Silo,
    lane_aisle: int,
    lane_y: int,
    outbound_x: int,
) -> Optional[Position]:
    candidates: List[Tuple[int, Position]] = []
    for x in _on_path_x_values(outbound_x):
        for side in (1, 2):
            z1_pos: Position = (lane_aisle, side, x, lane_y, 1)
            z2_pos: Position = (lane_aisle, side, x, lane_y, 2)
            z1_slot = silo.get_slot(z1_pos)
            z2_slot = silo.get_slot(z2_pos)
            if z1_slot is None or z2_slot is None:
                continue
            # To place at z=2, front slot z=1 must be empty.
            if not z1_slot.is_empty:
                continue
            # And z=2 itself must be empty.
            if not z2_slot.is_empty:
                continue
            candidates.append((x, z2_pos))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][1]


def _find_overshoot_same_destination_stack_slot(
    silo: Silo,
    inbound_box: Box,
    lane_aisle: int,
    lane_y: int,
    outbound_x: int,
) -> Optional[Position]:
    for x in _overshoot_x_values(silo, outbound_x):
        for side in (1, 2):
            z2_pos: Position = (lane_aisle, side, x, lane_y, 2)
            z1_pos: Position = (lane_aisle, side, x, lane_y, 1)
            z2_slot = silo.get_slot(z2_pos)
            z1_slot = silo.get_slot(z1_pos)
            if z2_slot is None or z1_slot is None:
                continue
            if z2_slot.box is None:
                continue
            if z2_slot.box.destination != inbound_box.destination:
                continue
            if not z1_slot.is_empty:
                continue
            return z1_pos
    return None


def _find_nearest_overshoot_empty_z2_slot(
    silo: Silo,
    lane_aisle: int,
    lane_y: int,
    outbound_x: int,
) -> Optional[Position]:
    candidates: List[Tuple[int, Position]] = []
    for x in _overshoot_x_values(silo, outbound_x):
        for side in (1, 2):
            z1_pos: Position = (lane_aisle, side, x, lane_y, 1)
            z2_pos: Position = (lane_aisle, side, x, lane_y, 2)
            z1_slot = silo.get_slot(z1_pos)
            z2_slot = silo.get_slot(z2_pos)
            if z1_slot is None or z2_slot is None:
                continue
            if not z1_slot.is_empty:
                continue
            if not z2_slot.is_empty:
                continue
            candidates.append((x, z2_pos))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][1]


def _on_path_x_values(outbound_x: int) -> range:
    # Path is always from head toward outbound pick location.
    # If outbound_x is invalid (<1), return an empty range.
    if outbound_x < 1:
        return range(1, 1)
    return range(1, outbound_x + 1)


def _overshoot_x_values(silo: Silo, outbound_x: int) -> range:
    max_x = max((position[2] for position in silo.slots.keys()), default=0)
    start_x = max(1, outbound_x + 1)
    if start_x > max_x:
        return range(1, 1)
    return range(start_x, max_x + 1)
