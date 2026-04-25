from __future__ import annotations

from simulation_runner import run_simulation


def main() -> None:
    state = run_simulation(
        ticks=100,
        csv_path="silo-semi-empty.csv",
        inbound_seed=7,
        print_every_tick=False,
    )
    print(f"completed_seconds={state.t}")


if __name__ == "__main__":
    main()
