from flask import Flask, request, jsonify
from flask_cors import CORS

import initial_state_generator

OUTPUT_PATH = "frontend/public/data/silo_setup.csv"

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})


@app.route("/api/randomize", methods=["POST"])
def randomize():
    data = request.get_json(silent=True) or {}
    num_boxes = data.get("num_boxes")
    if not isinstance(num_boxes, int) or isinstance(num_boxes, bool):
        return jsonify({"error": "num_boxes must be an integer"}), 400
    try:
        stats = initial_state_generator.create_initial_state_csv(
            num_boxes, OUTPUT_PATH
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({
        "success": True,
        "num_boxes": stats["num_boxes"],
        "csv_path": stats["filename"],
        "fill_pct": stats["fill_pct"],
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    initial_state_generator.create_initial_state_csv(0, OUTPUT_PATH)
    return jsonify({"success": True})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=8000, debug=True)
