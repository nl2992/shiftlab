"""Matched residual-variance comparison of fixed and start-time e-mixtures."""

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
QUERY_RATES = (0.2, 0.4, 0.8, 1.0)
METHODS = ("fixed_mixture", "uniform_start_mixture", "late_start_mixture")
BOOTSTRAP_REPLICATES = 10_000


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 60,
    seed_offset: int = 31_202_026,
    n: int = 2400,
    device: str = "cuda",
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
            false_escalations=("false_alarm", "sum"),
            mean_delay_when_detected=("detection_delay", "mean"),
            mean_excess_cost=("expected_excess_cost_mean", "mean"),
            mean_estimator_rmse=("estimator_rmse", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_realized_label_spend=("realized_label_spend", "mean"),
            mean_events_processed=("events_processed", "mean"),
        )
        .reset_index()
    )
    paired = _paired_start_contrasts(metrics)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "power_summary.csv", index=False)
    paired.to_csv(output / "paired_detection_contrasts.csv", index=False)
    script = Path(__file__)
    monitor_script = script.with_name("risk_proxy_monitor_grid.py")
    prior_script = script.with_name("start_prior_sweep.py")
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "design": {
            "purpose": "diagnostic comparison of previously calibrated fixed start priors on residual-variance harm",
            "severities": list(SEVERITIES),
            "query_rates": list(QUERY_RATES),
            "seeds_per_cell": seeds,
            "seed_range_inclusive": [seed_offset, seed_offset + seeds - 1],
            "n": n,
            "methods": list(METHODS),
            "device": config.device,
            "starts": "eight fixed positions over planned monitor horizon; selected before outcomes",
            "weights": {
                "uniform_start_mixture": "Beta(1,1) mass over eight equal-width horizon bins",
                "late_start_mixture": "Beta(2,1) mass over eight equal-width horizon bins",
            },
            "note": "The fixed convex mixtures preserve the bounded-mean e-process guarantee under its original conditional-mean and support assumptions. This alternative-only grid is not a new null calibration.",
        },
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
    return metrics, summary, paired, manifest


def _paired_start_contrasts(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (severity, query_rate), group in metrics.groupby(["severity", "query_rate"], sort=True):
        wide = group.pivot(index="seed", columns="method", values="detected")
        for candidate in METHODS[1:]:
            paired = wide[["fixed_mixture", candidate]].dropna()
            difference = (
                paired[candidate].astype(float) - paired["fixed_mixture"].astype(float)
            ).to_numpy()
            rng = np.random.default_rng(31_202_026 + len(rows))
            indices = rng.integers(0, len(difference), size=(BOOTSTRAP_REPLICATES, len(difference)))
            low, high = np.quantile(difference[indices].mean(axis=1), [0.025, 0.975])
            rows.append(
                {
                    "severity": severity,
                    "query_rate": query_rate,
                    "candidate": candidate,
                    "candidate_detection_rate": float(paired[candidate].mean()),
                    "fixed_detection_rate": float(paired.fixed_mixture.mean()),
                    "paired_detection_difference": float(difference.mean()),
                    "seed_cluster_ci95_low": float(low),
                    "seed_cluster_ci95_high": float(high),
                    "candidate_only": int((paired[candidate] & ~paired.fixed_mixture).sum()),
                    "fixed_only": int((~paired[candidate] & paired.fixed_mixture).sum()),
                    "seed_clusters": len(difference),
                    "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/residual_variance_start_prior")
    parser.add_argument("--seeds", type=int, default=60)
    parser.add_argument("--seed-offset", type=int, default=31_202_026)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, summary, paired, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        device=args.device,
    )
    print(summary.to_string(index=False))
    print(paired.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
