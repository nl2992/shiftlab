"""Run a paired decision-harm monitor grid at one fixed total label-dollar cap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget

HORIZONS = (1000, 1800, 2600)
SEED_OFFSET = 56_100_000
SCENARIO_CELLS = (
    ("stationary", "stationary", 0.5),
    ("benign_nuisance", "benign_nuisance", 0.5),
    ("boundary_early", "boundary_local_harm", 0.35),
    ("boundary_late", "boundary_local_harm", 0.65),
    ("recurring_regimes", "recurring_regimes", 0.5),
    ("harmful_adaptation", "harmful_adaptation", 0.5),
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/fixed_dollar_horizon_grid_development")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--budget-dollars", type=float, default=720.0)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    if args.seeds < 1 or args.budget_dollars <= 0:
        parser.error("seeds and budget-dollars must be positive")

    frozen = {
        "experiment": "fixed_dollar_horizon_decision_harm_monitor_development_grid",
        "seed_offset": args.seed_offset,
        "seeds_per_cell": args.seeds,
        "seed_range": [args.seed_offset, args.seed_offset + args.seeds - 1],
        "n": 4000,
        "monitor_start": 1000,
        "monitor_horizons": list(HORIZONS),
        "fixed_label_dollar_cap": args.budget_dollars,
        "budget_rate_for_query_design": 0.20,
        "q_min": 0.20,
        "q_max": 0.80,
        "alpha": 0.05,
        "harm_margin": 0.10,
        "scenarios": [
            {"cell": cell, "scenario": scenario, "change_fraction": change_fraction}
            for cell, scenario, change_fraction in SCENARIO_CELLS
        ],
        "methods": ["uniform_proxy", "pprm_block_adaptive"],
        "eventwise_monitors": ["fixed_mixture", "predictable_variance", "PM-EB"],
        "block_monitor": "fixed 10% PPI CM-EB / positive-betting mixture",
        "block_design": {"size": 20, "labels_per_block": 4, "reliance_cap": 0.1},
        "device_requested": args.device,
        "status": "development grid; all cellwise contrasts are descriptive; no winner selection",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    config_path = args.output / "grid_config.json"
    if config_path.exists() and json.loads(config_path.read_text(encoding="utf-8")) != frozen:
        raise ValueError(f"output already has a different frozen grid config: {config_path}")
    config_path.write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")

    for horizon in HORIZONS:
        for cell_name, scenario_name, change_fraction in SCENARIO_CELLS:
            config = HardBudgetConfig(
                n=4000,
                d=16,
                seeds=args.seeds,
                seed_offset=args.seed_offset,
                alpha=0.05,
                harm_margin=0.10,
                budget_rate=0.20,
                budget_dollars=args.budget_dollars,
                monitor_horizon_events=horizon,
                q_min=0.20,
                q_max=0.80,
                common_eprocess_bound=True,
                change_fraction=change_fraction,
                pprm_block_size=20,
                pprm_labels_per_block=4,
                pprm_max_reliance=0.10,
                pprm_initial_reliance=0.10,
                device=args.device,
                scenario_subset=(scenario_name,),
                method_subset=("uniform_proxy", "pprm_block_adaptive"),
                monitor_comparators=("variance_adaptive", "pm_eb"),
            )
            output = args.output / f"horizon_{horizon:04d}" / cell_name
            metrics_path = output / "metrics" / "hard_budget_comparison.parquet"
            if metrics_path.exists():
                raise FileExistsError(f"refusing to overwrite completed grid cell: {output}")
            print(
                f"starting horizon={horizon} cell={cell_name} seeds={args.seeds} device={args.device}",
                flush=True,
            )
            run_hard_budget(config, output)


if __name__ == "__main__":
    main()
