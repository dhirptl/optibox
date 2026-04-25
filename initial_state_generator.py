import argparse
import csv
import os
import random
from typing import Dict, List, Tuple

SOURCE_CODE = "3055769"

DESTINATIONS = [
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

AISLES = 4
SIDES = 2
X_MAX = 60
Y_LEVELS = 8
Z_DEPTH = 2
MAX_CAPACITY = AISLES * SIDES * X_MAX * Y_LEVELS * Z_DEPTH

Position = Tuple[int, int, int, int, int]
Tunnel = Tuple[int, int, int, int]


def generate_box_code(destination: str) -> str:
    bulk = str(random.randint(10000, 99999))
    return f"{SOURCE_CODE}{destination}{bulk}"


def format_position(aisle: int, side: int, x: int, y: int, z: int) -> str:
    return f"{aisle:02d}{side:02d}{x:03d}{y:02d}{z:02d}"


def build_all_positions() -> List[Position]:
    positions: List[Position] = []
    for aisle in range(1, AISLES + 1):
        for side in range(1, SIDES + 1):
            for x in range(1, X_MAX + 1):
                for y in range(1, Y_LEVELS + 1):
                    for z in range(1, Z_DEPTH + 1):
                        positions.append((aisle, side, x, y, z))
    return positions


def build_tunnels() -> List[Tunnel]:
    tunnels: List[Tunnel] = []
    for aisle in range(1, AISLES + 1):
        for side in range(1, SIDES + 1):
            for x in range(1, X_MAX + 1):
                for y in range(1, Y_LEVELS + 1):
                    tunnels.append((aisle, side, x, y))
    return tunnels


def create_initial_state_csv(num_boxes: int, output_path: str) -> dict:
    if num_boxes < 0 or num_boxes > MAX_CAPACITY:
        raise ValueError(f"num_boxes must be between 0 and {MAX_CAPACITY}")

    tunnels = build_tunnels()
    random.shuffle(tunnels)

    filled: Dict[Position, str] = {}
    placed = 0

    for aisle, side, x, y in tunnels:
        if placed >= num_boxes:
            break

        # Always fill wall-adjacent depth first (Z=2), then aisle-adjacent (Z=1).
        for z in (2, 1):
            if placed >= num_boxes:
                break
            destination = random.choice(DESTINATIONS)
            filled[(aisle, side, x, y, z)] = generate_box_code(destination)
            placed += 1

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    all_positions = build_all_positions()

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["posicion", "etiqueta"])
        for position in all_positions:
            pos_code = format_position(*position)
            writer.writerow([pos_code, filled.get(position, "")])

    return {
        "num_boxes": placed,
        "filename": output_path,
        "fill_pct": (placed / MAX_CAPACITY) * 100,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-boxes", type=int, required=True)
    parser.add_argument("--output", default="frontend/public/data/silo_setup.csv")
    args = parser.parse_args()

    stats = create_initial_state_csv(args.num_boxes, args.output)
    print(
        f"✅ Generated {stats['num_boxes']} boxes in {stats['filename']} "
        f"({stats['fill_pct']:.1f}% full)"
    )
