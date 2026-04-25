from __future__ import annotations

from pathlib import Path

from inbound_generator import InboundBoxGenerator
from main import build_initial_state, get_ready_shuttles_for_inbound, run_tick_batch


def main() -> None:
    output_path = Path("simulation_100s.log")
    state = build_initial_state(csv_path="silo-semi-empty.csv")
    generator = InboundBoxGenerator(seed=7)

    with output_path.open("w", encoding="utf-8") as f:
        if state.initial_load_stats is not None:
            stats = state.initial_load_stats
            f.write(
                f"[init] loaded_rows={stats.rows_total} "
                f"placed_boxes={stats.placed_boxes} "
                f"empty_rows={stats.rows_empty}\n"
            )

        for _ in range(100):
            ready_shuttles = get_ready_shuttles_for_inbound(state)
            inbound_count = len(ready_shuttles)
            inbound_boxes = generator.next_boxes(inbound_count)
            results = run_tick_batch(state, inbound_boxes)

            f.write(
                f"[t={state.t:05d}] inbound_count={inbound_count}\n"
            )
            for i, inbound_box in enumerate(inbound_boxes, start=1):
                f.write(
                    f"  inbound_{i:02d}={inbound_box.box_id} "
                    f"dest={inbound_box.destination}\n"
                )
            for result in results:
                f.write(
                    f"  shuttle={result.shuttle_id} "
                    f"task={result.task_type} "
                    f"started={result.started_task} "
                    f"finished={result.finished_task} "
                    f"remaining={result.remaining_seconds} "
                    f"state={result.notes}\n"
                )

        f.write(f"[done] completed_seconds={state.t}\n")

    print(f"log_file={output_path.resolve()}")


if __name__ == "__main__":
    main()
