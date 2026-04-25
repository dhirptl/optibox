import csv
import random
import argparse
import os
from typing import List, Tuple

SOURCE_CODE = "3055769"

DESTINATIONS = [
    "01000110", "01001120", "01002130", "01003140", "01004150",
    "01005160", "01006170", "01007180", "01008190", "01009210",
    "01010220", "01011230", "01012240", "01013250", "01014260",
    "01015270", "01016280", "01017290", "01018310", "01019320",
]

AISLES = 4
SIDES = 2
X_MAX = 60
Y_LEVELS = 8
Z_DEPTH = 2
MAX_CAPACITY = AISLES * SIDES * X_MAX * Y_LEVELS * Z_DEPTH  # 7680


def generate_box_code(destination: str) -> str:
    bulk = random.randint(10000, 99999)
    return f"{SOURCE_CODE}{destination}{bulk}"


def format_position(aisle: int, side: int, x: int, y: int, z: int) -> str:
    return f"{aisle:02d}{side:02d}{x:03d}{y:02d}{z:02d}"


def build_all_positions() -> List[Tuple[int, int, int, int, int]]:
    positions = []
    for aisle in range(1, AISLES + 1):
        for side in range(1, SIDES + 1):
            for x in range(1, X_MAX + 1):
                for y in range(1, Y_LEVELS + 1):
                    for z in range(1, Z_DEPTH + 1):
                        positions.append((aisle, side, x, y, z))
    return positions


def build_tunnels() -> List[Tuple[int, int, int, int]]:
    tunnels = []
    for aisle in range(1, AISLES + 1):
        for side in range(1, SIDES + 1):
            for x in range(1, X_MAX + 1):
                for y in range(1, Y_LEVELS + 1):
                    tunnels.append((aisle, side, x, y))
    return tunnels


def create_initial_state_csv(num_boxes: int, output_path: str) -> dict:
    if not (0 <= num_boxes <= MAX_CAPACITY):
        raise ValueError(
            f"num_boxes must be between 0 and {MAX_CAPACITY}, got {num_boxes}"
        )

    tunnels = build_tunnels()
    random.shuffle(tunnels)

    placed: dict = {}
    remaining = num_boxes
    for (aisle, side, x, y) in tunnels:
        if remaining <= 0:
            break
        destination = random.choice(DESTINATIONS)
        placed[(aisle, side, x, y, 2)] = generate_box_code(destination)
        remaining -= 1
        if remaining <= 0:
            break
        destination = random.choice(DESTINATIONS)
        placed[(aisle, side, x, y, 1)] = generate_box_code(destination)
        remaining -= 1

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["posicion", "etiqueta"])
        for (aisle, side, x, y, z) in build_all_positions():
            posicion = format_position(aisle, side, x, y, z)
            etiqueta = placed.get((aisle, side, x, y, z), "")
            writer.writerow([posicion, etiqueta])

    fill_pct = (num_boxes / MAX_CAPACITY) * 100
    return {
        "num_boxes": num_boxes,
        "filename": output_path,
        "fill_pct": fill_pct,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate initial silo state CSV for OPTIBOX simulator."
    )
    parser.add_argument(
        "--num-boxes",
        type=int,
        required=True,
        help=f"Number of boxes to place (0-{MAX_CAPACITY}).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="frontend/public/data/silo_setup.csv",
        help="Output CSV path.",
    )
    args = parser.parse_args()

    stats = create_initial_state_csv(args.num_boxes, args.output)
    print(
        f"Generated {stats['num_boxes']} boxes "
        f"({stats['fill_pct']:.2f}% full) -> {stats['filename']}"
    )


if __name__ == "__main__":
    main()
