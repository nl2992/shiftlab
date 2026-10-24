"""Independent large-sample null calibration for the frozen intervention gates."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ..data.gpu.environment import environment
from .closed_loop_intervention import _calibration, _evaluate_methods, benefit_schedule
from .intervention_confirmation import CONTROL_SCENARIOS, FROZEN_DESIGN
from .promotion_timing import _generate_costs

SEED_OFFSET = 62_102_626


def run_calibration_replication(
    output_dir: str | Path,
    *,
    seeds: int = 10_000,
    seed_offset: int = SEED_OFFSET,
    horizon: int = 800,
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    if seeds < 2:
        raise ValueError("seeds must be at least two")
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 100:
        raise ValueError("horizon must be an integer of at least 100")
    if device not in {"cpu", "cuda"}:
        raise ValueError("device must be cpu or cuda")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")

    schedules = {
        name: benefit_schedule(name, horizon)
        for name in CONTROL_SCENARIOS
        if name != "weak_persistent_benefit"
    }
    schedules["weak_persistent_benefit"] = np.concatenate(
        (np.full(horizon, 0.10), np.full(horizon, 0.08))
    )
    generator = torch.Generator(device=device)
    metric_groups = []
    for scenario_index, (scenario, benefit) in enumerate(schedules.items()):
        scenario_seed = seed_offset + scenario_index * 1_000_003
        incumbent, candidate = _generate_costs(
            benefit,
            seeds=seeds,
            seed=scenario_seed,
            device=device,
        )
        gains = incumbent.astype(float) - candidate.astype(float)
        generator.manual_seed(scenario_seed + 900_001)
        query_uniforms = (
            torch.rand((seeds, 2 * horizon), generator=generator, device=device).cpu().numpy()
        )
        rows = _evaluate_methods(
            scenario=scenario,
            budget_rate=FROZEN_DESIGN["budget_rate"],
            gains=gains,
            benefit=benefit,
            query_uniforms=query_uniforms,
            seed_offset=scenario_seed,
            query_rate=FROZEN_DESIGN["query_rate"],
            promotion_cost=FROZEN_DESIGN["promotion_cost"],
            rollback_cost=FROZEN_DESIGN["rollback_cost"],
            label_price=FROZEN_DESIGN["label_price"],
            alpha=0.05,
            horizon=horizon,
        )
        for column, value in FROZEN_DESIGN.items():
            rows[column] = value
        metric_groups.append(rows)

    metrics = pd.concat(metric_groups, ignore_index=True)
    if not metrics["budget_respected"].all():
        raise RuntimeError("a stream exceeded the hard label cap")
    summary = (
        metrics.groupby(["scenario", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            promotions=("promoted", "sum"),
            promotion_rate=("promoted", "mean"),
            rollbacks=("rolled_back", "sum"),
            rollback_rate=("rolled_back", "mean"),
            false_promotions=("false_promotion_under_null", "sum"),
            false_rollbacks=("false_rollback_under_null", "sum"),
            mean_expected_net_utility=("expected_net_utility", "mean"),
            mean_labels=("labels_queried", "mean"),
            maximum_labels=("labels_queried", "max"),
            budget_respected=("budget_respected", "all"),
        )
        .reset_index()
    )
    calibration = _calibration(metrics, 0.05)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    calibration.to_csv(output / "error_calibration.csv", index=False)
    source_paths = {
        "intervention_calibration_replication.py": Path(__file__),
        "intervention_confirmation.py": Path(__file__).with_name("intervention_confirmation.py"),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
        "controller.py": Path(__file__).with_name("controller.py"),
        "eprocess.py": Path(__file__).with_name("eprocess.py"),
        "promotion_timing.py": Path(__file__).with_name("promotion_timing.py"),
    }
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "independent fixed-size null-calibration replication; no parameter changes",
        "seeds_per_scenario": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "device_requested": device,
        "frozen_design": FROZEN_DESIGN,
        "control_scenarios": list(schedules),
        "calibration_family_cells": len(calibration),
        "calibration_ci": "exact one-sided Clopper-Pearson with Bonferroni family correction",
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in source_paths.items()
        },
        "environment": environment(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return metrics, summary, calibration, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/intervention_calibration_replication")
    parser.add_argument("--seeds", type=int, default=10_000)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=800)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, _summary, calibration, manifest = run_calibration_replication(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        device=args.device,
    )
    print(calibration.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
