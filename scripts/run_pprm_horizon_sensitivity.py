"""Evaluate a fixed PPI monitor over longer synthetic observation horizons."""

from __future__ import annotations

import argparse
from pathlib import Path

from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget

HORIZONS = (1600, 3200, 6400)
SCENARIOS = (
    "stationary",
    "benign_nuisance",
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs/pprm_horizon_development_v1")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=20372123)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()

    for n in HORIZONS:
        config = HardBudgetConfig(
            n=n,
            d=args.d,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            budget_rate=0.20,
            q_min=0.10,
            q_max=0.80,
            common_eprocess_bound=True,
            pprm_block_size=20,
            pprm_labels_per_block=4,
            pprm_max_reliance=0.10,
            pprm_initial_reliance=0.10,
            device=args.device,
            scenario_subset=SCENARIOS,
            method_subset=("uniform_proxy", "uniform_proxy_frozen", "pprm_block_adaptive"),
        )
        output = args.output_root / f"n_{n}"
        run_hard_budget(config, output)
        print(f"completed n={n} output={output}", flush=True)


if __name__ == "__main__":
    main()
