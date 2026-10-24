"""Fresh-seed development screen for multi-timescale predictable betting."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.gpu.environment import environment
from ..decision_harm_experiment import SCENARIOS
from .risk_proxy_monitor_grid import RiskProxyMonitorGridConfig, _run_stream

SEVERITIES = (1.5, 3.0, 4.5)
QUERY_RATES = (0.8, 1.0)
SEED_OFFSET = 31_303_026
METHODS = (
    "fixed_mixture",
    "predictable_kelly",
    "uniform_start_mixture",
    "discounted_start_mixture",
)


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 60,
    seed_offset: int = SEED_OFFSET,
    n: int = 2400,
    device: str = "cuda",
    bootstrap_replicates: int = 10_000,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    config = RiskProxyMonitorGridConfig(
        n=n,
        alternative_seeds=seeds,
        seed_offset=seed_offset,
        device=device,
    ).validate()
    template = next(scenario for scenario in SCENARIOS if scenario.name == "residual_variance")
    rows = []
    for severity in SEVERITIES:
        scenario = replace(template, severity=severity)
        for seed in range(seed_offset, seed_offset + seeds):
            for query_rate in QUERY_RATES:
                rows.extend(
                    {**row, "severity": severity}
                    for row in _run_stream(scenario, seed, query_rate, config, methods=METHODS)
                )

    metrics = pd.DataFrame(rows)
    summary = (
        metrics.groupby(["severity", "query_rate", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            material_harm_streams=("material_harm", "sum"),
            detections=("detected", "sum"),
            detection_rate=("detected", "mean"),
            pre_onset_alarms=("false_alarm", "sum"),
            mean_delay_when_detected=("detection_delay", "mean"),
            mean_excess_cost=("expected_excess_cost_mean", "mean"),
            mean_estimator_rmse=("estimator_rmse", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_spend=("realized_label_spend", "mean"),
            mean_events_processed=("events_processed", "mean"),
            budget_respected=("budget_respected", "all"),
        )
        .reset_index()
    )
    contrasts = _paired_contrasts(metrics, bootstrap_replicates)
    aggregate = _aggregate_contrasts(metrics, bootstrap_replicates)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "power_summary.csv", index=False)
    contrasts.to_csv(output / "paired_cell_contrasts.csv", index=False)
    aggregate.to_csv(output / "paired_macro_contrasts.csv", index=False)

    script = Path(__file__)
    monitor_script = script.with_name("risk_proxy_monitor_grid.py")
    eprocess_script = script.with_name("eprocess.py")
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "development-only alternative comparison; no null calibration or confirmation",
        "scenario": "residual_variance / target_variance",
        "severities": list(SEVERITIES),
        "query_rates": list(QUERY_RATES),
        "seeds_per_cell": seeds,
        "seed_range_inclusive": [seed_offset, seed_offset + seeds - 1],
        "n": n,
        "methods": list(METHODS),
        "discounted_half_lives": [16.0, 64.0, 256.0],
        "start_count": 8,
        "start_weights": "uniform, fixed before each stream",
        "half_life_weights": "uniform, fixed before each stream",
        "stake_rule": "clip(max(0, discounted_mean) / max(discounted_second_moment, tiny), 0, 0.5); both moments use only earlier normalized increments",
        "primary_contrasts": [
            ["discounted_start_mixture", "fixed_mixture"],
            ["discounted_start_mixture", "uniform_start_mixture"],
        ],
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            script.name: hashlib.sha256(script.read_bytes()).hexdigest(),
            monitor_script.name: hashlib.sha256(monitor_script.read_bytes()).hexdigest(),
            eprocess_script.name: hashlib.sha256(eprocess_script.read_bytes()).hexdigest(),
        },
        "environment": environment(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return metrics, summary, aggregate, manifest


def _paired_contrasts(metrics: pd.DataFrame, bootstrap_replicates: int) -> pd.DataFrame:
    rows = []
    pairs = (
        ("discounted_start_mixture", "fixed_mixture"),
        ("discounted_start_mixture", "uniform_start_mixture"),
        ("discounted_start_mixture", "predictable_kelly"),
    )
    for (severity, query_rate), group in metrics.groupby(["severity", "query_rate"], sort=True):
        wide = group.pivot(index="seed", columns="method", values="detected")
        for candidate, reference in pairs:
            difference = (wide[candidate].astype(float) - wide[reference].astype(float)).to_numpy()
            rng = np.random.default_rng(31_303_026 + len(rows))
            sample = rng.integers(0, len(difference), size=(bootstrap_replicates, len(difference)))
            interval = np.quantile(difference[sample].mean(axis=1), [0.025, 0.975])
            rows.append(
                {
                    "severity": severity,
                    "query_rate": query_rate,
                    "candidate": candidate,
                    "reference": reference,
                    "paired_detection_difference": float(difference.mean()),
                    "seed_cluster_ci95_low": float(interval[0]),
                    "seed_cluster_ci95_high": float(interval[1]),
                    "candidate_only": int((wide[candidate] & ~wide[reference]).sum()),
                    "reference_only": int((~wide[candidate] & wide[reference]).sum()),
                    "seed_clusters": len(difference),
                }
            )
    return pd.DataFrame(rows)


def _aggregate_contrasts(metrics: pd.DataFrame, bootstrap_replicates: int) -> pd.DataFrame:
    primary = metrics.pivot(
        index=["seed", "severity", "query_rate"], columns="method", values="detected"
    )
    rows = []
    for reference in ("fixed_mixture", "uniform_start_mixture", "predictable_kelly"):
        paired_by_seed = (
            (primary["discounted_start_mixture"].astype(float) - primary[reference].astype(float))
            .groupby(level="seed")
            .mean()
        )
        differences = paired_by_seed.to_numpy(dtype=float)
        rng = np.random.default_rng(31_303_026 + len(rows))
        sample = rng.integers(0, len(differences), size=(bootstrap_replicates, len(differences)))
        interval = np.quantile(differences[sample].mean(axis=1), [0.025, 0.975])
        rows.append(
            {
                "candidate": "discounted_start_mixture",
                "reference": reference,
                "paired_macro_detection_difference": float(differences.mean()),
                "seed_cluster_ci95_low": float(interval[0]),
                "seed_cluster_ci95_high": float(interval[1]),
                "positive_seed_clusters": int((differences > 0).sum()),
                "negative_seed_clusters": int((differences < 0).sum()),
                "tied_seed_clusters": int((differences == 0).sum()),
                "seed_clusters": len(differences),
                "cells_per_seed": primary.shape[0] // len(differences),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/residual_variance_discounted_betting")
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    args = parser.parse_args()
    _metrics, summary, aggregate, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        device=args.device,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(aggregate.to_string(index=False))
    print(summary.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
