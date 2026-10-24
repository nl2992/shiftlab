"""Diagnose residual-variance monitor power over severity and label budgets.

This is a stress grid, not a calibrated or confirmatory experiment. Evaluator-only
proxy diagnostics are written to the output but never supplied to a monitor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from ..data.gpu.environment import environment
from ..decision_harm_experiment import SCENARIOS
from .risk_proxy_monitor_grid import (
    PROCESS_NAMES,
    RiskProxyMonitorGridConfig,
    _run_stream,
)

SEVERITIES = (0.75, 1.5, 2.25, 3.0, 4.5)
QUERY_RATES = (0.2, 0.4, 0.6, 0.8, 1.0)


def run_grid(
    output_dir: str | Path,
    *,
    seeds: int = 100,
    seed_offset: int = 31_102_026,
    n: int = 2400,
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
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
                for row in _run_stream(scenario, seed, query_rate, config):
                    rows.append({**row, "severity": severity})

    metrics = pd.DataFrame(rows)
    summary = (
        metrics.groupby(["severity", "query_rate", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            material_harm_streams=("material_harm", "sum"),
            detections=("detected", "sum"),
            detection_rate=("detected", "mean"),
            mean_delay_when_detected=("detection_delay", "mean"),
            mean_expected_excess_cost=("expected_excess_cost_mean", "mean"),
            mean_excess_over_margin=("offline_mean_margin_excess", "mean"),
            mean_centered_outcome_variance=("centered_paired_cost_variance", "mean"),
            mean_proxy_residual_mse=("offline_proxy_residual_mse", "mean"),
            mean_ppi_variance_approx=("offline_ppi_variance_approx", "mean"),
            mean_estimator_rmse=("estimator_rmse", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_budget_spend=("realized_label_spend", "mean"),
        )
        .reset_index()
    )
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "power_summary.csv", index=False)
    script = Path(__file__)
    monitor_script = script.with_name("risk_proxy_monitor_grid.py")
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "design": {
            "purpose": "diagnostic stress grid; not confirmatory and not a validity proof",
            "scenario": "residual_variance / target_variance",
            "severities": list(SEVERITIES),
            "query_rates": list(QUERY_RATES),
            "seeds_per_cell": seeds,
            "seed_range_inclusive": [seed_offset, seed_offset + seeds - 1],
            "n": n,
            "methods": list(PROCESS_NAMES),
            "device": config.device,
            "diagnostics": "offline_* fields use evaluator truth and are never monitor inputs",
        },
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": {
            script.name: hashlib.sha256(script.read_bytes()).hexdigest(),
            monitor_script.name: hashlib.sha256(monitor_script.read_bytes()).hexdigest(),
        },
        "environment": environment(),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return metrics, summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/residual_variance_power_grid")
    parser.add_argument("--seeds", type=int, default=100)
    parser.add_argument("--seed-offset", type=int, default=31_102_026)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, summary, manifest = run_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        device=args.device,
    )
    print(summary.to_string(index=False))
    print(f"metric_rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
