import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from initial_state_generator import MAX_CAPACITY, create_initial_state_csv
from simulation_runner import run_simulation_for_playback, write_simulation_log

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(REPO_ROOT, "frontend", "public", "data", "silo_setup.csv")
SIMULATION_LOG_PATH = os.path.join(REPO_ROOT, "simulation_log.json")


def error_response(message: str, status_code: int):
    return jsonify({"success": False, "error": message}), status_code


def parse_num_boxes(value) -> int:
    if isinstance(value, bool):
        raise ValueError("num_boxes must be an integer")
    if isinstance(value, int):
        num_boxes = value
    elif isinstance(value, str) and value.strip():
        try:
            num_boxes = int(value)
        except ValueError as exc:
            raise ValueError("num_boxes must be an integer") from exc
    else:
        raise ValueError("num_boxes must be an integer")

    if num_boxes < 0 or num_boxes > MAX_CAPACITY:
        raise ValueError(f"num_boxes must be between 0 and {MAX_CAPACITY}")
    return num_boxes


def parse_optional_int(value, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = int(value)
        except ValueError as exc:
            raise ValueError(f"{field} must be an integer") from exc
    else:
        raise ValueError(f"{field} must be an integer")

    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return parsed


@app.route("/api/randomize", methods=["POST"])
def randomize():
    if not request.is_json:
        return error_response("Content-Type must be application/json", 400)

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "num_boxes" not in data:
        return error_response("Missing num_boxes", 400)

    try:
        num_boxes = parse_num_boxes(data["num_boxes"])
    except ValueError as exc:
        return error_response(str(exc), 400)

    try:
        stats = create_initial_state_csv(num_boxes, OUTPUT_PATH)
        return jsonify(
            {
                "success": True,
                "num_boxes": stats["num_boxes"],
                "csv_path": stats["filename"],
                "fill_pct": stats["fill_pct"],
            }
        )
    except Exception as exc:  # pragma: no cover - defensive catch for demo reliability
        return error_response(str(exc), 500)


@app.route("/api/reset", methods=["POST"])
def reset():
    try:
        create_initial_state_csv(0, OUTPUT_PATH)
        return jsonify({"success": True})
    except Exception as exc:  # pragma: no cover - defensive catch for demo reliability
        return error_response(str(exc), 500)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/run-simulation", methods=["POST"])
def run_simulation():
    if not request.is_json:
        return error_response("Content-Type must be application/json", 400)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response("Request body must be a JSON object", 400)

    try:
        ticks = parse_optional_int(data.get("ticks", 3600), "ticks", 0, 3600)
        inbound_seed = parse_optional_int(data.get("inbound_seed", 42), "inbound_seed", 0, 1_000_000)
        inbound_per_tick = parse_optional_int(data.get("inbound_per_tick", 1), "inbound_per_tick", 1, 64)
        if "num_boxes" in data:
            num_boxes = parse_num_boxes(data["num_boxes"])
            create_initial_state_csv(num_boxes, OUTPUT_PATH)

        playback = run_simulation_for_playback(
            ticks=ticks,
            csv_path=OUTPUT_PATH,
            inbound_seed=inbound_seed,
            inbound_per_tick=inbound_per_tick,
        )
        write_simulation_log(SIMULATION_LOG_PATH, playback)
        return jsonify(
            {
                "success": True,
                "duration_seconds": playback.duration_seconds,
                "inbound_per_tick": inbound_per_tick,
                "metrics": {
                    "full_pallets_out_of_8": playback.metrics.full_pallets_out_of_8,
                    "pallets_completed": playback.metrics.pallets_completed,
                    "avg_time_per_pallet": playback.metrics.avg_time_per_pallet,
                },
                "final_metrics": {
                    "full_pallets_out_of_8": playback.final_metrics.full_pallets_out_of_8,
                    "pallets_completed": playback.final_metrics.pallets_completed,
                    "avg_time_per_pallet": playback.final_metrics.avg_time_per_pallet,
                },
                "events": playback.events,
                "timeline": playback.timeline,
                "log_path": SIMULATION_LOG_PATH,
            }
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:  # pragma: no cover - defensive catch for demo reliability
        return error_response(str(exc), 500)


if __name__ == "__main__":
    app.run(port=8000, debug=True)
