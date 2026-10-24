"""Independent-seed confirmation for the frozen intervention sensitivity winner."""

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
from .closed_loop_intervention import _calibration, _evaluate_methods, _paired_contrasts
from .intervention_sensitivity import scenario_schedules
from .promotion_timing import _generate_costs

SEED_OFFSET = 52_102_626
FROZEN_DESIGN = {
    "query_rate": 0.8,
    "budget_rate": 0.4,
    "label_price": 0.01,
    "promotion_cost": 0.05,
    "rollback_cost": 0.05,
}
CONTROL_SCENARIOS = (
    "no_benefit",
    "persistent_benefit",
    "shadow_only_benefit",
    "late_benefit",
    "weak_persistent_benefit",
)


def run_confirmation(
    output_dir: str | Path,
    *,
    seeds: int = 2000,
    seed_offset: int = SEED_OFFSET,
    horizon: int = 800,
    device: str = "cuda",
    bootstrap_replicates: int = 10_000,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    if seeds < 2:
        raise ValueError("seeds must be at least two")
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 100:
        raise ValueError("horizon must be an integer of at least 100")
    if device not in {"cpu", "cuda"}:
        raise ValueError("device must be cpu or cuda")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable")
    if bootstrap_replicates < 100:
        raise ValueError("bootstrap_replicates must be at least 100")

    schedules = scenario_schedules(horizon)
    schedules["weak_persistent_benefit"] = np.concatenate(
        (np.full(horizon, 0.10), np.full(horizon, 0.08))
    )
    scenario_names = tuple(dict.fromkeys((*CONTROL_SCENARIOS, *schedules.keys())))
    selected_scenarios = {name: schedules[name] for name in scenario_names}

    generator = torch.Generator(device=device)
    metric_groups = []
    for scenario_index, (scenario, benefit) in enumerate(selected_scenarios.items()):
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
            mean_realized_net_utility=("realized_net_utility", "mean"),
            mean_labels=("labels_queried", "mean"),
            maximum_labels=("labels_queried", "max"),
            budget_respected=("budget_respected", "all"),
        )
        .reset_index()
    )
    contrasts = _paired_contrasts(metrics, bootstrap_replicates)
    calibration = _calibration(metrics, 0.05)
    reversal_metrics = metrics[metrics.scenario.str.startswith("reversal_")].copy()
    pivot = reversal_metrics.pivot(
        index=["scenario", "seed"], columns="method", values="expected_net_utility"
    ).reset_index()
    pivot["replicate"] = pivot["seed"] - pivot.groupby("scenario")["seed"].transform("min")
    pivot["rollback_vs_promotion_only"] = pivot["promotion_rollback"] - pivot["promotion_only"]
    pivot["rollback_vs_continue"] = pivot["promotion_rollback"] - pivot["continue"]
    macro_by_seed = pivot.groupby("replicate", sort=True)[
        ["rollback_vs_promotion_only", "rollback_vs_continue"]
    ].mean()
    macro_rows = []
    for index, contrast in enumerate(macro_by_seed.columns):
        samples = macro_by_seed[contrast].to_numpy(dtype=float)
        rng = np.random.default_rng(seed_offset + 7_001 * (index + 1))
        draws = rng.integers(0, len(samples), size=(bootstrap_replicates, len(samples)))
        interval = np.quantile(samples[draws].mean(axis=1), (0.025, 0.975))
        macro_rows.append(
            {
                "contrast": contrast,
                "mean_difference": float(samples.mean()),
                "seed_cluster_ci95_low": float(interval[0]),
                "seed_cluster_ci95_high": float(interval[1]),
                "seed_clusters": len(samples),
                "reversal_profiles": reversal_metrics.scenario.nunique(),
            }
        )
    macro = pd.DataFrame(macro_rows)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "summary.csv", index=False)
    contrasts.to_csv(output / "paired_utility_contrasts.csv", index=False)
    macro.to_csv(output / "reversal_macro_contrasts.csv", index=False)
    calibration.to_csv(output / "error_calibration.csv", index=False)
    source_paths = {
        "intervention_confirmation.py": Path(__file__),
        "intervention_sensitivity.py": Path(__file__).with_name("intervention_sensitivity.py"),
        "closed_loop_intervention.py": Path(__file__).with_name("closed_loop_intervention.py"),
        "controller.py": Path(__file__).with_name("controller.py"),
        "eprocess.py": Path(__file__).with_name("eprocess.py"),
        "promotion_timing.py": Path(__file__).with_name("promotion_timing.py"),
    }
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "independent-seed confirmation of one frozen development-selected design",
        "seeds_per_scenario": seeds,
        "seed_offset": seed_offset,
        "horizon_per_phase": horizon,
        "device_requested": device,
        "frozen_design": FROZEN_DESIGN,
        "control_scenarios": list(CONTROL_SCENARIOS),
        "reversal_scenarios": [name for name in selected_scenarios if name.startswith("reversal_")],
        "methods": ["continue", "unconditional_promote", "promotion_only", "promotion_rollback"],
        "alpha_total": 0.05,
        "alpha_each_gate": 0.025,
        "calibration_family_cells": len(calibration),
        "calibration_ci": "exact one-sided Clopper-Pearson with Bonferroni family correction",
        "utility_ci": "paired seed-cluster bootstrap, descriptive across six reversal profiles",
        "bootstrap_replicates": bootstrap_replicates,
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            name: hashlib.sha256(path.read_bytes()).hexdigest()
            for name, path in source_paths.items()
        },
        "environment": environment(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return metrics, summary, contrasts, macro, calibration, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/intervention_confirmation")
    parser.add_argument("--seeds", type=int, default=2000)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--horizon", type=int, default=800)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    args = parser.parse_args()
    _metrics, _summary, _contrasts, macro, calibration, manifest = run_confirmation(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        device=args.device,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(macro.to_string(index=False))
    print(calibration.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
