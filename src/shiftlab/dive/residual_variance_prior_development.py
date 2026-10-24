"""Development screen for fixed start-time priors on residual-variance harm."""

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
from .risk_proxy_monitor_grid import (
    START_PRIOR_SHAPES,
    RiskProxyMonitorGridConfig,
    _run_stream,
)

SEVERITIES = (1.5, 3.0, 4.5)
QUERY_RATES = (0.4, 0.8, 1.0)
PRIMARY_RATES = (0.8, 1.0)
SEED_OFFSET = 31_302_026
PRIOR_METHODS = tuple(START_PRIOR_SHAPES)
METHODS = ("fixed_mixture", *PRIOR_METHODS)


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
    template = next(s for s in SCENARIOS if s.name == "residual_variance")
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
        )
        .reset_index()
    )
    contrasts = _paired_contrasts(metrics, bootstrap_replicates)
    selection = _select_prior(summary)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "power_summary.csv", index=False)
    contrasts.to_csv(output / "paired_detection_contrasts.csv", index=False)
    selection.to_csv(output / "development_selection.csv", index=False)
    script = Path(__file__)
    monitor_script = script.with_name("risk_proxy_monitor_grid.py")
    prior_script = script.with_name("start_prior_sweep.py")
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "purpose": "development screen only; no null calibration or confirmatory inference",
        "scenario": "residual_variance / target_variance",
        "severities": list(SEVERITIES),
        "query_rates": list(QUERY_RATES),
        "primary_selection_rates": list(PRIMARY_RATES),
        "seeds_per_cell": seeds,
        "seed_range_inclusive": [seed_offset, seed_offset + seeds - 1],
        "n": n,
        "methods": list(METHODS),
        "prior_shapes": {key: list(START_PRIOR_SHAPES[key]) for key in PRIOR_METHODS},
        "planned_monitor_horizon": n - max(800, int(n * 0.25)),
        "selection_rule": "maximize macro detection averaged equally across severity x primary query-rate cells; tie-break on maximin detection across severity groups",
        "bootstrap_replicates": bootstrap_replicates,
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            script.name: hashlib.sha256(script.read_bytes()).hexdigest(),
            monitor_script.name: hashlib.sha256(monitor_script.read_bytes()).hexdigest(),
            prior_script.name: hashlib.sha256(prior_script.read_bytes()).hexdigest(),
        },
        "environment": environment(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return metrics, summary, selection, manifest


def _paired_contrasts(metrics: pd.DataFrame, bootstrap_replicates: int) -> pd.DataFrame:
    methods = ("fixed_mixture", "uniform_start_mixture") + tuple(
        name for name in PRIOR_METHODS if name != "uniform_start_mixture"
    )
    rows = []
    for (severity, query_rate), group in metrics.groupby(["severity", "query_rate"], sort=True):
        wide = group.pivot(index="seed", columns="method", values="detected")
        for candidate in methods[1:]:
            difference = (wide[candidate].astype(float) - wide[methods[0]].astype(float)).to_numpy()
            rng = np.random.default_rng(seed=31_302_026 + len(rows))
            sample = rng.integers(0, len(difference), size=(bootstrap_replicates, len(difference)))
            interval = np.quantile(difference[sample].mean(axis=1), [0.025, 0.975])
            rows.append(
                {
                    "severity": severity,
                    "query_rate": query_rate,
                    "candidate": candidate,
                    "reference": methods[0],
                    "paired_detection_difference": float(difference.mean()),
                    "seed_cluster_ci95_low": float(interval[0]),
                    "seed_cluster_ci95_high": float(interval[1]),
                    "candidate_only": int((wide[candidate] & ~wide[methods[0]]).sum()),
                    "reference_only": int((~wide[candidate] & wide[methods[0]]).sum()),
                    "seed_clusters": len(difference),
                }
            )
    return pd.DataFrame(rows)


def _select_prior(summary: pd.DataFrame) -> pd.DataFrame:
    selection_rows = []
    primary = summary[summary.query_rate.isin(PRIMARY_RATES)]
    for method in PRIOR_METHODS:
        grouped = (
            primary[primary.method.eq(method)].groupby("severity", sort=True).detection_rate.mean()
        )
        selection_rows.append(
            {
                "method": method,
                "macro_detection_primary_rates": float(grouped.mean()),
                "maximin_severity_detection": float(grouped.min()),
                "selection_cells": int(primary[primary.method.eq(method)].shape[0]),
                "selected": False,
            }
        )
    frame = pd.DataFrame(selection_rows)
    winner = frame.sort_values(
        ["macro_detection_primary_rates", "maximin_severity_detection", "method"],
        ascending=[False, False, True],
    ).index[0]
    frame.loc[winner, "selected"] = True
    return frame.sort_values(
        ["macro_detection_primary_rates", "maximin_severity_detection", "method"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/residual_variance_prior_development")
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=SEED_OFFSET)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    args = parser.parse_args()
    _metrics, summary, selection, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        device=args.device,
        bootstrap_replicates=args.bootstrap_replicates,
    )
    print(selection.to_string(index=False))
    print(summary.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
