from __future__ import annotations

from typing import Optional

from inbound_generator import InboundBoxGenerator
from main import SimulationState, build_initial_state, run_tick
from models import SimulationConfig


def run_simulation(
    ticks: int,
    config: Optional[SimulationConfig] = None,
    csv_path: Optional[str] = None,
    inbound_seed: Optional[int] = 42,
    print_every_tick: bool = True,
) -> SimulationState:
    """
    Convenience runner that wires:
    - initial state build (+ optional CSV preload)
    - inbound generation
    - per-tick execution
    - console printing for each move/progress event
    """
    if ticks < 0:
        raise ValueError("ticks must be >= 0")

    state = build_initial_state(config=config, csv_path=csv_path, strict_positions=True)
    generator = InboundBoxGenerator(seed=inbound_seed)

    if state.initial_load_stats is not None:
        stats = state.initial_load_stats
        print(
            f"[init] loaded_rows={stats.rows_total} "
            f"placed_boxes={stats.placed_boxes} empty_rows={stats.rows_empty}"
        )

    for _ in range(ticks):
        inbound_box = generator.next_box()
        inbound_id = inbound_box.box_id
        inbound_destination = inbound_box.destination

        results = run_tick(state, inbound_box)

        if not print_every_tick:
            continue

        print(
            f"[t={state.t:05d}] inbound={inbound_id} "
            f"dest={inbound_destination}"
        )
        for result in results:
            if result.notes == "idle":
                continue
            print(
                f"  shuttle={result.shuttle_id} "
                f"task={result.task_type} "
                f"started={result.started_task} "
                f"finished={result.finished_task} "
                f"remaining={result.remaining_seconds} "
                f"state={result.notes}"
            )

    return state


if __name__ == "__main__":
    run_simulation(
        ticks=20,
        csv_path="silo-semi-empty.csv",
        inbound_seed=7,
        print_every_tick=True,
    )
