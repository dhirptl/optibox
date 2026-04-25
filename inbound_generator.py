from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from models import Box


DEFAULT_DESTINATIONS: List[str] = [
    "01000110",
    "01001120",
    "01002130",
    "01003140",
    "01004150",
    "01005160",
    "01006170",
    "01007180",
    "01008190",
    "01009210",
    "01010220",
    "01011230",
    "01012240",
    "01013250",
    "01014260",
    "01015270",
    "01016280",
    "01017290",
    "01018310",
    "01019320",
]


@dataclass
class InboundBoxGenerator:
    """
    Generates inbound boxes with the challenge 20-digit format:
    - 7 digits source (static warehouse code)
    - 8 digits destination (sampled uniformly from a pool of 20 destinations)
    - 5 digits bulk number (unique incremental counter)
    """

    source_code: str = "3010028"
    destination_count: int = 20
    seed: Optional[int] = None
    start_bulk_number: int = 0
    bulk_counter_mode: str = "per_destination"
    destinations: Optional[List[str]] = None
    destination_pool: List[str] = field(init=False)
    _rng: random.Random = field(init=False, repr=False)
    _global_bulk_counter: int = field(init=False, repr=False)
    _bulk_counter_by_destination: Dict[str, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if len(self.source_code) != 7 or not self.source_code.isdigit():
            raise ValueError("source_code must be exactly 7 digits.")
        if self.start_bulk_number < 0:
            raise ValueError("start_bulk_number must be >= 0.")
        if self.start_bulk_number > 99_999:
            raise ValueError("start_bulk_number must be <= 99999.")
        if self.bulk_counter_mode not in {"global", "per_destination"}:
            raise ValueError("bulk_counter_mode must be 'global' or 'per_destination'.")

        self._rng = random.Random(self.seed)
        self.destination_pool = self._resolve_destination_pool()
        self._global_bulk_counter = self.start_bulk_number
        self._bulk_counter_by_destination = {
            destination: self.start_bulk_number for destination in self.destination_pool
        }

    def next_box(self) -> Box:
        """
        Build one new inbound box.
        """
        destination = self._rng.choice(self.destination_pool)
        bulk_number = self._next_bulk_number_for(destination)
        box_id = f"{self.source_code}{destination}{bulk_number}"
        return Box.parse_box_id(box_id)

    def next_boxes(self, n: int) -> List[Box]:
        if n < 0:
            raise ValueError("n must be >= 0.")
        return [self.next_box() for _ in range(n)]

    @staticmethod
    def _build_destination_pool(count: int) -> List[str]:
        # Use deterministic canonical 8-digit codes: 00000000, 00000001, ...
        return [f"{i:08d}" for i in range(count)]

    def _resolve_destination_pool(self) -> List[str]:
        if self.destinations is not None:
            pool = [d.strip() for d in self.destinations]
        else:
            # Default behavior: use the 20 specific challenge destinations.
            pool = list(DEFAULT_DESTINATIONS)

        if not pool:
            raise ValueError("destinations pool cannot be empty.")
        for destination in pool:
            if len(destination) != 8 or not destination.isdigit():
                raise ValueError(
                    f"Invalid destination '{destination}'. Expected exactly 8 digits."
                )

        # Keep backward compatibility: destination_count can still limit a custom pool.
        if self.destination_count < 1:
            raise ValueError("destination_count must be >= 1.")
        if self.destination_count > len(pool):
            raise ValueError(
                "destination_count cannot exceed available destination pool size."
            )
        return pool[: self.destination_count]

    def _next_bulk_number_for(self, destination: str) -> str:
        if self.bulk_counter_mode == "global":
            if self._global_bulk_counter > 99_999:
                raise ValueError("Bulk number overflow in global mode: reached 99999.")
            bulk_number = f"{self._global_bulk_counter:05d}"
            self._global_bulk_counter += 1
            return bulk_number

        # per_destination mode
        current = self._bulk_counter_by_destination[destination]
        if current > 99_999:
            raise ValueError(
                f"Bulk number overflow for destination {destination}: reached 99999."
            )
        bulk_number = f"{current:05d}"
        self._bulk_counter_by_destination[destination] = current + 1
        return bulk_number
