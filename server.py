import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from initial_state_generator import MAX_CAPACITY, create_initial_state_csv

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

OUTPUT_PATH = os.path.join("frontend", "public", "data", "silo_setup.csv")


@app.route("/api/randomize", methods=["POST"])
def randomize():
    data = request.get_json()
    if not data or "num_boxes" not in data:
        return jsonify({"error": "Missing num_boxes"}), 400

    num_boxes = data["num_boxes"]
    if not isinstance(num_boxes, int) or num_boxes < 0 or num_boxes > MAX_CAPACITY:
        return jsonify({"error": f"num_boxes must be 0-{MAX_CAPACITY}"}), 400

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
        return jsonify({"error": str(exc)}), 500


@app.route("/api/reset", methods=["POST"])
def reset():
    try:
        create_initial_state_csv(0, OUTPUT_PATH)
        return jsonify({"success": True})
    except Exception as exc:  # pragma: no cover - defensive catch for demo reliability
        return jsonify({"error": str(exc)}), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=8000, debug=True)
