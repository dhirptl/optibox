from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from models import Box, Position, Silo


@dataclass(frozen=True)
class CsvLoadStats:
    rows_total: int
    rows_with_box: int
    rows_empty: int
    placed_boxes: int
    skipped_unknown_positions: int


def load_silo_from_csv(
    csv_path: str,
    silo: Silo,
    strict_positions: bool = True,
) -> CsvLoadStats:
    """
    Load warehouse state from CSV into an existing Silo.

    Expected columns:
    - posicion: 11-digit position code (AA SS XXX YY ZZ)
    - etiqueta: 20-digit box id (optional/empty means no box in that slot)
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    rows_total = 0
    rows_with_box = 0
    rows_empty = 0
    placed_boxes = 0
    skipped_unknown_positions = 0

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"posicion", "etiqueta"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(
                f"CSV must contain columns {sorted(required)}; got {reader.fieldnames}"
            )

        for row in reader:
            rows_total += 1
            pos_code = (row.get("posicion") or "").strip()
            box_id = (row.get("etiqueta") or "").strip()

            position = parse_position_code(pos_code)
            slot = silo.get_slot(position)
            if slot is None:
                if strict_positions:
                    raise ValueError(f"Position {pos_code} not present in current silo.")
                skipped_unknown_positions += 1
                continue

            if not box_id:
                rows_empty += 1
                continue

            rows_with_box += 1
            box = Box.parse_box_id(box_id)
            # CSV is initial state, so each filled row should map to one placement.
            silo.place_box(position, box)
            placed_boxes += 1

    return CsvLoadStats(
        rows_total=rows_total,
        rows_with_box=rows_with_box,
        rows_empty=rows_empty,
        placed_boxes=placed_boxes,
        skipped_unknown_positions=skipped_unknown_positions,
    )


def parse_position_code(code: str) -> Position:
    """
    Parse 11-digit position code:
    - 2 digits aisle
    - 2 digits side
    - 3 digits x
    - 2 digits y
    - 2 digits z
    Example: 01010010101 -> (1, 1, 1, 1, 1)
    """
    value = code.strip()
    if len(value) != 11 or not value.isdigit():
        raise ValueError(f"Invalid position code '{code}'. Expected exactly 11 digits.")

    aisle = int(value[0:2])
    side = int(value[2:4])
    x = int(value[4:7])
    y = int(value[7:9])
    z = int(value[9:11])
    return (aisle, side, x, y, z)


def preload_silo_from_csv(
    csv_path: str,
    silo: Silo,
    strict_positions: bool = True,
) -> CsvLoadStats:
    """
    Alias for readability at call sites.
    """
    return load_silo_from_csv(
        csv_path=csv_path,
        silo=silo,
        strict_positions=strict_positions,
    )
