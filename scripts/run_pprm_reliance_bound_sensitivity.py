"""Test how a tighter preregistered PPI reliance cap changes power and precision."""

from __future__ import annotations

import argparse
from pathlib import Path

from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget

SCENARIOS = (
    "stationary",
    "benign_nuisance",
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
RELIANCE_CAPS = (0.1, 0.25, 0.5, 1.0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs/pprm_reliance_bound_development_v1")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=20372023)
    parser.add_argument("--n", type=int, default=1600)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--block-size", type=int, default=20)
    parser.add_argument("--labels-per-block", type=int, default=4)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    if not 1 <= args.labels_per_block < args.block_size:
        parser.error("require 1 <= --labels-per-block < --block-size")

    for reliance_cap in RELIANCE_CAPS:
        name = f"eta_{reliance_cap:.2f}".replace(".", "p")
        config = HardBudgetConfig(
            n=args.n,
            d=args.d,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            budget_rate=0.20,
            q_min=0.10,
            q_max=0.80,
            common_eprocess_bound=True,
            pprm_block_size=args.block_size,
            pprm_labels_per_block=args.labels_per_block,
            pprm_max_reliance=reliance_cap,
            pprm_initial_reliance=reliance_cap,
            device=args.device,
            scenario_subset=SCENARIOS,
            method_subset=("uniform_proxy", "uniform_proxy_frozen", "pprm_block_adaptive"),
        )
        output = args.output_root / name
        run_hard_budget(config, output)
        print(f"completed max_reliance={reliance_cap:g} output={output}", flush=True)


if __name__ == "__main__":
    main()
