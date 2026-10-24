"""Compare a prespecified start-time e-process mixture under fixed-dollar horizons."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget

HORIZONS = (1000, 1800, 2600)
SEED_OFFSET = 57_100_000
SCENARIOS = (
    ("stationary", "stationary", 0.5),
    ("benign_nuisance", "benign_nuisance", 0.5),
    ("boundary_early", "boundary_local_harm", 0.35),
    ("boundary_late", "boundary_local_harm", 0.65),
    ("recurring_regimes", "recurring_regimes", 0.5),
    ("harmful_adaptation", "harmful_adaptation", 0.5),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/started_mixture_horizon_development")
    )
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--budget-dollars", type=float, default=720.0)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    if args.seeds < 1 or args.budget_dollars <= 0:
        parser.error("seeds and budget-dollars must be positive")

    config_record = {
        "experiment": "prespecified_start_time_mixture_fixed_dollar_horizon_development",
        "seeds_per_cell": args.seeds,
        "seed_offset": args.seed_offset,
        "seed_range": [args.seed_offset, args.seed_offset + args.seeds - 1],
        "n": 4000,
        "monitor_start": 1000,
        "horizons": list(HORIZONS),
        "budget_dollars": args.budget_dollars,
        "budget_rate": 0.20,
        "q_min": 0.20,
        "q_max": 0.80,
        "alpha": 0.05,
        "harm_margin": 0.10,
        "start_rule": "sorted unique {0, floor(H/4), floor(H/2), floor(3H/4)}; equal fixed weights",
        "scenario_cells": [
            {"cell": cell, "scenario": scenario, "change_fraction": fraction}
            for cell, scenario, fraction in SCENARIOS
        ],
        "method": "uniform_proxy; all eventwise monitors share labels and corrected estimates",
        "comparators": [
            "single full-stream fixed mixture",
            "four-start equal mixture",
            "predictable variance",
            "PM-EB",
        ],
        "device_requested": args.device,
        "status": "development only; no winner selection or novelty claim",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    config_path = args.output / "grid_config.json"
    if (
        config_path.exists()
        and json.loads(config_path.read_text(encoding="utf-8")) != config_record
    ):
        raise ValueError(f"output already has another frozen config: {config_path}")
    config_path.write_text(json.dumps(config_record, indent=2) + "\n", encoding="utf-8")

    for horizon in HORIZONS:
        for cell, scenario, fraction in SCENARIOS:
            output = args.output / f"horizon_{horizon:04d}" / cell
            metrics = output / "metrics" / "hard_budget_comparison.parquet"
            if metrics.exists():
                raise FileExistsError(f"refusing to overwrite existing cell: {output}")
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
                change_fraction=fraction,
                device=args.device,
                scenario_subset=(scenario,),
                method_subset=("uniform_proxy",),
                monitor_comparators=("variance_adaptive", "pm_eb"),
            )
            print(f"starting horizon={horizon} cell={cell} seeds={args.seeds}", flush=True)
            run_hard_budget(config, output)

    record = {
        "configuration": config_record,
        "configuration_sha256": sha256(config_path),
        "runner_sha256": sha256(Path(__file__)),
        "protocol_sha256": sha256(Path("docs/started_mixture_horizon_protocol.md")),
        "status": "all requested cells completed; analysis pending",
    }
    (args.output / "grid_manifest.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
