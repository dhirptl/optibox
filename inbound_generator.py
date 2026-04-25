from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from models import Box


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
    destination_pool: List[str] = field(init=False)
    _rng: random.Random = field(init=False, repr=False)
    _bulk_counter: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if len(self.source_code) != 7 or not self.source_code.isdigit():
            raise ValueError("source_code must be exactly 7 digits.")
        if self.destination_count < 1:
            raise ValueError("destination_count must be >= 1.")
        if self.destination_count > 100_000_000:
            raise ValueError("destination_count cannot exceed 100,000,000.")
        if self.start_bulk_number < 0:
            raise ValueError("start_bulk_number must be >= 0.")
        if self.start_bulk_number > 99_999:
            raise ValueError("start_bulk_number must be <= 99999.")

        self._rng = random.Random(self.seed)
        self._bulk_counter = self.start_bulk_number
        self.destination_pool = self._build_destination_pool(self.destination_count)

    def next_box(self) -> Box:
        """
        Build one new inbound box.
        """
        if self._bulk_counter > 99_999:
            raise ValueError("Bulk number overflow: reached 99999.")

        destination = self._rng.choice(self.destination_pool)
        bulk_number = f"{self._bulk_counter:05d}"
        box_id = f"{self.source_code}{destination}{bulk_number}"
        self._bulk_counter += 1
        return Box.parse_box_id(box_id)

    def next_boxes(self, n: int) -> List[Box]:
        if n < 0:
            raise ValueError("n must be >= 0.")
        return [self.next_box() for _ in range(n)]

    @staticmethod
    def _build_destination_pool(count: int) -> List[str]:
        # Use deterministic canonical 8-digit codes: 00000000, 00000001, ...
        return [f"{i:08d}" for i in range(count)]
