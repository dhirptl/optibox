from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from models import Box, DispatcherState, Pallet, SimulationConfig


@dataclass(frozen=True)
class InboundDecision:
    """
    Decision produced when an inbound box is known at x=0.
    """

    should_cross_dock: bool
    destination: str
    reason: str


def count_boxes_by_destination(boxes: Iterable[Box]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for box in boxes:
        counts[box.destination] = counts.get(box.destination, 0) + 1
    return counts


def open_eligible_pallets(
    state: DispatcherState,
    available_by_destination: Dict[str, int],
    config: SimulationConfig,
) -> None:
    """
    Open pallets for destinations that have enough available inventory.

    Rules:
    - Each pallet requires `config.pallet_size` boxes.
    - No more than `config.max_active_pallets` active pallets at once.
    - Opening a pallet reserves `pallet_size` boxes for that destination.
    """
    active_count = len(state.active_pallets)
    if active_count >= config.max_active_pallets:
        return

    for destination in sorted(available_by_destination.keys()):
        if len(state.active_pallets) >= config.max_active_pallets:
            break
        if destination in state.active_pallets:
            continue

        already_reserved = state.reserved_inventory_by_destination.get(destination, 0)
        free_boxes = available_by_destination[destination] - already_reserved
        if free_boxes < config.pallet_size:
            continue

        state.active_pallets[destination] = Pallet(destination=destination)
        state.reserved_inventory_by_destination[destination] = (
            already_reserved + config.pallet_size
        )


def close_completed_pallets(state: DispatcherState) -> None:
    """
    Remove completed pallets from active set and release reservation counter.
    """
    completed_destinations = [
        destination
        for destination, pallet in state.active_pallets.items()
        if pallet.is_complete
    ]

    for destination in completed_destinations:
        state.active_pallets.pop(destination, None)
        state.reserved_inventory_by_destination.pop(destination, None)


def has_active_pallet_for_destination(
    state: DispatcherState,
    destination: str,
) -> bool:
    pallet = state.active_pallets.get(destination)
    return pallet is not None and pallet.is_active and not pallet.is_complete


def decide_inbound(
    inbound_box: Optional[Box],
    state: DispatcherState,
) -> Optional[InboundDecision]:
    """
    Decide intercept behavior once inbound details are known at x=0.

    If there is an active pallet for the inbound destination, the box should be
    cross-docked immediately at x=0; otherwise it should follow store-path flow.
    """
    if inbound_box is None:
        return None

    destination = inbound_box.destination
    if has_active_pallet_for_destination(state, destination):
        return InboundDecision(
            should_cross_dock=True,
            destination=destination,
            reason="active_pallet_for_destination",
        )

    return InboundDecision(
        should_cross_dock=False,
        destination=destination,
        reason="no_active_pallet_for_destination",
    )
