from __future__ import annotations

from inbound_generator import InboundBoxGenerator
from main import build_initial_state, run_tick_batch


def main() -> None:
    # 1) Build state from current warehouse snapshot.
    state = build_initial_state(csv_path="silo-semi-empty.csv")

    # 2) Generate one inbound box per shuttle (default target: 32).
    generator = InboundBoxGenerator(seed=7)
    inbound_count = len(state.shuttles)
    inbound_boxes = generator.next_boxes(inbound_count)

    # 3) Execute exactly one tick with a batch of inbound boxes.
    results = run_tick_batch(state, inbound_boxes)

    # 4) Print concise summary + all active shuttle results.
    print(f"time={state.t}")
    print(f"inbound_count={inbound_count}")

    started = 0
    finished = 0
    active = 0
    for result in results:
        if result.started_task:
            started += 1
        if result.finished_task:
            finished += 1
        if result.notes != "idle":
            active += 1

    print(f"shuttles_active={active} started={started} finished={finished}")

    for result in results:
        if result.notes == "idle":
            continue
        print(
            f"shuttle={result.shuttle_id} task={result.task_type} "
            f"remaining={result.remaining_seconds} state={result.notes}"
        )


if __name__ == "__main__":
    main()
