from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from inbound_generator import InboundBoxGenerator
from main import (
    SimulationState,
    build_initial_state,
    get_ready_shuttles_for_inbound,
    get_shipped_pallets_total,
    run_tick_batch,
)
from models import Position, Silo, Shuttle


def export_frontend_timeline(
    ticks: int,
    csv_path: str = "silo-semi-empty.csv",
    inbound_seed: int = 7,
    output_json_path: str = "frontend_timeline.json",
) -> Path:
    if ticks < 0:
        raise ValueError("ticks must be >= 0")

    state = build_initial_state(csv_path=csv_path)
    generator = InboundBoxGenerator(seed=inbound_seed)
    timeline: List[Dict[str, Any]] = []

    for _ in range(ticks):
        ready_shuttles = get_ready_shuttles_for_inbound(state)
        inbound_boxes = generator.next_boxes(len(ready_shuttles))
        run_tick_batch(state, inbound_boxes)
        timeline.append(_snapshot_tick_y1(state))

    payload = {
        "ticks_requested": ticks,
        "ticks_completed": state.t,
        "total_pallets_shipped": get_shipped_pallets_total(state),
        "timeline": timeline,
    }

    output_path = Path(output_json_path)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path.resolve()


def _snapshot_tick_y1(state: SimulationState) -> Dict[str, Any]:
    return {
        "time": state.t,
        "silo_y1_boxes": _silo_y1_boxes(state.silo),
        "carriers_y1": _carriers_y1(state.shuttles),
        "pallets": _pallet_status(state),
    }


def _silo_y1_boxes(silo: Silo) -> List[Dict[str, Any]]:
    boxes: List[Dict[str, Any]] = []
    for position, slot in silo.slots.items():
        if position[3] != 1:
            continue
        if slot.box is None:
            continue
        boxes.append(
            {
                "position": _position_to_code(position),
                "box_id": slot.box.box_id,
                "destination": slot.box.destination,
            }
        )
    boxes.sort(key=lambda item: item["position"])
    return boxes


def _carriers_y1(shuttles: List[Shuttle]) -> List[Dict[str, Any]]:
    carriers: List[Dict[str, Any]] = []
    for shuttle in shuttles:
        if shuttle.y != 1:
            continue
        carrying_box_id = shuttle.carrying.box_id if shuttle.carrying is not None else None
        carrying_destination = (
            shuttle.carrying.destination if shuttle.carrying is not None else None
        )
        active_task_type = (
            shuttle.active_task.task_type.value if shuttle.active_task is not None else None
        )
        active_remaining_seconds = (
            shuttle.active_task.remaining_seconds if shuttle.active_task is not None else 0
        )
        carriers.append(
            {
                "shuttle_id": shuttle.shuttle_id,
                "aisle": shuttle.aisle,
                "y": shuttle.y,
                "current_x": shuttle.current_x,
                "is_idle": shuttle.is_idle,
                "active_task_type": active_task_type,
                "active_task_remaining_seconds": active_remaining_seconds,
                "carrying_box_id": carrying_box_id,
                "carrying_destination": carrying_destination,
            }
        )
    carriers.sort(key=lambda item: item["shuttle_id"])
    return carriers


def _position_to_code(position: Position) -> str:
    aisle, side, x, y, z = position
    return f"{aisle:02d}{side:02d}{x:03d}{y:02d}{z:02d}"


def _pallet_status(state: SimulationState) -> List[Dict[str, Any]]:
    """
    Per-tick pallet fullness by destination.
    - filled_boxes: current progress in the active pallet (0..11)
    - completed_pallets: total full pallets shipped for this destination
    """
    pallet_size = state.config.pallet_size
    statuses: List[Dict[str, Any]] = []
    for destination in sorted(state.dispatcher.active_pallets.keys()):
        shipped = state.shipped_by_destination.get(destination, 0)
        statuses.append(
            {
                "destination": destination,
                "filled_boxes": shipped % pallet_size,
                "completed_pallets": shipped // pallet_size,
                "pallet_size": pallet_size,
            }
        )
    return statuses


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export frontend JSON timeline for Y=1 state by tick."
    )
    parser.add_argument("--ticks", type=int, default=100, help="Number of ticks to simulate.")
    parser.add_argument(
        "--csv-path",
        type=str,
        default="silo-semi-empty.csv",
        help="Initial silo CSV snapshot path.",
    )
    parser.add_argument(
        "--inbound-seed",
        type=int,
        default=7,
        help="Random seed for inbound generator.",
    )
    parser.add_argument(
        "--output-json-path",
        type=str,
        default="frontend_timeline.json",
        help="Output JSON file path for frontend.",
    )
    return parser


if __name__ == "__main__":
    args = _build_arg_parser().parse_args()
    output = export_frontend_timeline(
        ticks=args.ticks,
        csv_path=args.csv_path,
        inbound_seed=args.inbound_seed,
        output_json_path=args.output_json_path,
    )
    print(f"output_json={output}")
