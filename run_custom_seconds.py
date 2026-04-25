from __future__ import annotations

from pathlib import Path
from typing import Literal

from inbound_generator import InboundBoxGenerator
from main import build_initial_state, get_ready_shuttles_for_inbound, run_tick_batch


def run_custom_seconds(
    ticks: int,
    csv_path: str = "silo-semi-empty.csv",
    inbound_seed: int = 7,
    output_log_path: str = "simulation_custom.log",
    detail: Literal["full", "active_only", "summary"] = "summary",
    max_log_lines: int = 20_000,
) -> Path:
    if ticks < 0:
        raise ValueError("ticks must be >= 0")
    if max_log_lines < 1:
        raise ValueError("max_log_lines must be >= 1")

    output_path = Path(output_log_path)
    state = build_initial_state(csv_path=csv_path)
    generator = InboundBoxGenerator(seed=inbound_seed)
    lines_written = 0
    stopped_early = False

    with output_path.open("w", encoding="utf-8") as f:
        if state.initial_load_stats is not None:
            stats = state.initial_load_stats
            f.write(
                f"[init] loaded_rows={stats.rows_total} "
                f"placed_boxes={stats.placed_boxes} "
                f"empty_rows={stats.rows_empty}\n"
            )
            lines_written += 1

        for _ in range(ticks):
            if lines_written >= max_log_lines:
                stopped_early = True
                break

            ready_shuttles = get_ready_shuttles_for_inbound(state)
            inbound_count = len(ready_shuttles)
            inbound_boxes = generator.next_boxes(inbound_count)
            results = run_tick_batch(state, inbound_boxes)

            if detail == "summary":
                active = sum(1 for r in results if r.notes != "idle")
                started = sum(1 for r in results if r.started_task)
                finished = sum(1 for r in results if r.finished_task)
                f.write(
                    f"[t={state.t:05d}] inbound_count={inbound_count} "
                    f"active={active} started={started} finished={finished}\n"
                )
                lines_written += 1
                continue

            f.write(f"[t={state.t:05d}] inbound_count={inbound_count}\n")
            lines_written += 1
            for i, inbound_box in enumerate(inbound_boxes, start=1):
                if lines_written >= max_log_lines:
                    stopped_early = True
                    break
                f.write(
                    f"  inbound_{i:02d}={inbound_box.box_id} "
                    f"dest={inbound_box.destination}\n"
                )
                lines_written += 1
            if stopped_early:
                break

            for result in results:
                if detail == "active_only" and result.notes == "idle":
                    continue
                if lines_written >= max_log_lines:
                    stopped_early = True
                    break
                f.write(
                    f"  shuttle={result.shuttle_id} "
                    f"task={result.task_type} "
                    f"started={result.started_task} "
                    f"finished={result.finished_task} "
                    f"remaining={result.remaining_seconds} "
                    f"state={result.notes}\n"
                )
                lines_written += 1
            if stopped_early:
                break

        if stopped_early:
            f.write(
                f"[done] stopped_early=true reason=max_log_lines "
                f"completed_seconds={state.t} lines_written={lines_written}\n"
            )
        else:
            f.write(
                f"[done] stopped_early=false completed_seconds={state.t} "
                f"lines_written={lines_written}\n"
            )

    return output_path.resolve()


if __name__ == "__main__":
    # Change this value to simulate any number of seconds.
    TICKS = 100
    # Choose "summary" for compact output, "active_only" or "full" for detail.
    DETAIL = "summary"
    log_file = run_custom_seconds(
        ticks=TICKS,
        detail=DETAIL,
        max_log_lines=20_000,
    )
    print(f"log_file={log_file}")
