from __future__ import annotations

from inbound_generator import InboundBoxGenerator
from main import build_initial_state, run_tick


def main() -> None:
    # 1) Build state from current warehouse snapshot.
    state = build_initial_state(csv_path="silo-semi-empty.csv")

    # 2) Generate one inbound box.
    generator = InboundBoxGenerator(seed=7)
    inbound_box = generator.next_box()

    # 3) Execute exactly one tick.
    results = run_tick(state, inbound_box)

    # 4) Print concise summary.
    print(f"time={state.t}")
    print(f"inbound_box={inbound_box.box_id} destination={inbound_box.destination}")

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
