"""Run a matched development grid over paired-PPI block sizes on one seed block."""

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
BLOCK_SIZES = (5, 10, 20, 40)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs/pprm_block_grid_development")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=20372023)
    parser.add_argument("--n", type=int, default=1600)
    parser.add_argument("--d", type=int, default=16)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()

    for block_size in BLOCK_SIZES:
        labels_per_block = block_size // 5
        config = HardBudgetConfig(
            n=args.n,
            d=args.d,
            seeds=args.seeds,
            seed_offset=args.seed_offset,
            budget_rate=0.20,
            q_min=0.10,
            q_max=0.80,
            common_eprocess_bound=True,
            pprm_block_size=block_size,
            pprm_labels_per_block=labels_per_block,
            pprm_max_reliance=1.0,
            pprm_initial_reliance=1.0,
            device=args.device,
            scenario_subset=SCENARIOS,
            method_subset=("uniform_proxy", "uniform_proxy_frozen", "pprm_block_adaptive"),
        )
        output = args.output_root / f"block_{block_size:02d}"
        run_hard_budget(config, output)
        print(f"completed block_size={block_size} output={output}", flush=True)


if __name__ == "__main__":
    main()
