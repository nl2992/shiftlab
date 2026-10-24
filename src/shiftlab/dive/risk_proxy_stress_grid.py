"""Stress-test static decision-risk proxies under misspecification and resource changes."""

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
from .proxy_hedge_benchmark import METHODS, ProxyHedgeBenchmarkConfig, _run_stream

GRID_SCENARIOS = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
TRAIN_FRACTIONS = (0.05, 0.125, 0.25)
QUERY_RATES = (0.10, 0.20, 0.40)
COST_REGIMES = ((5.0, 1.0), (1.0, 1.0))
SEVERITIES = (0.75, 1.5, 2.25)
BOOTSTRAP_REPLICATES = 10_000


def _paired_bootstrap(values: np.ndarray, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(BOOTSTRAP_REPLICATES, len(values)))
    draws = values[indices].mean(axis=1)
    return [float(value) for value in np.quantile(draws, [0.025, 0.975])]


def run_risk_proxy_stress_grid(
    output_dir: str | Path,
    *,
    seeds: int = 12,
    seed_offset: int = 20402024,
    n: int = 2400,
    device: str = "cuda",
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if seeds < 2 or n < 1000:
        raise ValueError("stress grid requires at least two seeds and n >= 1000")
    if device not in {"auto", "cpu", "cuda"}:
        raise ValueError("device must be auto, cpu, or cuda")
    scenarios = {item.name: item for item in SCENARIOS}
    rows: list[dict[str, object]] = []
    cell_id = 0
    for scenario_name in GRID_SCENARIOS:
        severities = SEVERITIES if scenario_name != "harmful_adaptation" else (1.5,)
        for severity in severities:
            for fn_cost, fp_cost in COST_REGIMES:
                scenario = replace(
                    scenarios[scenario_name], severity=severity, fn_cost=fn_cost, fp_cost=fp_cost
                )
                for train_fraction in TRAIN_FRACTIONS:
                    for query_rate in QUERY_RATES:
                        cell_id += 1
                        config = ProxyHedgeBenchmarkConfig(
                            n=n,
                            seeds=seeds,
                            seed_offset=seed_offset,
                            query_rate=query_rate,
                            device=device,
                            scenario_subset=(scenario_name,),
                            train_fraction=train_fraction,
                            validation_fraction=0.125,
                        ).validate()
                        for seed in range(seed_offset, seed_offset + seeds):
                            for row in _run_stream(scenario, seed, config):
                                row.update(
                                    {
                                        "cell_id": cell_id,
                                        "severity": severity,
                                        "fn_cost": fn_cost,
                                        "fp_cost": fp_cost,
                                        "cost_ratio_fn_fp": fn_cost / fp_cost,
                                        "train_fraction": train_fraction,
                                        "query_rate": query_rate,
                                    }
                                )
                                rows.append(row)

    metrics = pd.DataFrame(rows)
    group_keys = [
        "cell_id",
        "scenario",
        "severity",
        "fn_cost",
        "fp_cost",
        "cost_ratio_fn_fp",
        "train_fraction",
        "query_rate",
        "method",
    ]
    summary = (
        metrics.groupby(group_keys, sort=True)
        .agg(
            streams=("seed", "size"),
            detection_rate=("detected", "mean"),
            false_escalation_rate=("false_escalation", "mean"),
            mean_rmse=("estimator_rmse", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_spend=("realized_label_spend", "mean"),
            mean_events_processed=("events_processed", "mean"),
            validation_selected_risk_model=(
                "selected_validation_expert",
                lambda values: float(np.mean(values == "risk_model")),
            ),
        )
        .reset_index()
    )

    contrasts = []
    paired_metrics = ("detected", "estimator_rmse", "false_escalation")
    cell_keys = [
        "cell_id",
        "scenario",
        "severity",
        "fn_cost",
        "fp_cost",
        "cost_ratio_fn_fp",
        "train_fraction",
        "query_rate",
    ]
    for cell, group in metrics.groupby(cell_keys, sort=True):
        wide = group.pivot(index="seed", columns="method", values=list(paired_metrics))
        for comparator in ("ridge", "validation_best", "prequential_hedge"):
            for metric in paired_metrics:
                # Lower false escalation and lower RMSE favor the risk model; higher detection
                # favors it. Preserve raw risk-minus-comparator signs in the saved table.
                difference = (
                    wide[(metric, "risk_model")].astype(float)
                    - wide[(metric, comparator)].astype(float)
                ).to_numpy()
                record = dict(zip(cell_keys, cell, strict=True))
                record.update(
                    {
                        "comparator": comparator,
                        "metric": metric,
                        "risk_model_minus_comparator": float(difference.mean()),
                        "seed_cluster_bootstrap_95": _paired_bootstrap(
                            difference, seed_offset + int(record["cell_id"]) * 31 + len(contrasts)
                        ),
                        "seeds": len(difference),
                    }
                )
                contrasts.append(record)
    contrast_frame = pd.DataFrame(contrasts)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    parquet_path = output / "metrics.parquet"
    metrics.to_parquet(parquet_path, index=False)
    metrics.to_csv(output / "metrics.csv", index=False)
    summary.to_csv(output / "scenario_summary.csv", index=False)
    contrast_frame.to_csv(output / "paired_contrasts.csv", index=False)
    module_path = Path(__file__)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "design": {
            "seeds_per_cell": seeds,
            "seed_offset": seed_offset,
            "n": n,
            "device_requested": device,
            "scenarios": list(GRID_SCENARIOS),
            "severity_values": list(SEVERITIES),
            "training_fractions": list(TRAIN_FRACTIONS),
            "query_rates": list(QUERY_RATES),
            "cost_regimes_fn_fp": [list(pair) for pair in COST_REGIMES],
            "validation_fraction": 0.125,
            "methods": list(METHODS),
            "paired_comparators": ["ridge", "validation_best", "prequential_hedge"],
            "cell_count": cell_id,
        },
        "metric_rows": len(metrics),
        "metrics_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(module_path.read_bytes()).hexdigest(),
        "proxy_benchmark_sha256": hashlib.sha256(
            module_path.with_name("proxy_hedge_benchmark.py").read_bytes()
        ).hexdigest(),
        "environment": environment(),
        "interpretation": "Development stress screen. Per-cell seed counts rank conditions only; no cellwise or familywise error-control certification is claimed.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Decision-risk proxy stress grid",
        "",
        f"The grid contains {cell_id} matched cells, {seeds} shared seeds per cell, and {len(metrics):,} method-stream rows.",
        "It varies severity, cost asymmetry, historical training share, and query rate. The logistic proxy is a standard fitted conditional-cost predictor, not a novelty claim.",
        "",
        "## Design summary",
        "",
        f"Scenarios: {', '.join(GRID_SCENARIOS)}. Training fractions: {TRAIN_FRACTIONS}. Query rates: {QUERY_RATES}. Cost regimes (FN, FP): {COST_REGIMES}.",
        "",
        "## Interpretation limits",
        "",
        "This is a development screen with small within-cell seed counts. Bootstrap intervals are descriptive and unadjusted across the grid. Null controls are absent, so the results do not calibrate false escalation. Retain a proxy for independent study only if it remains competitive across the registered misspecification and resource conditions.",
        "",
    ]
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    return metrics, summary, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/risk_proxy_stress_grid")
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--seed-offset", type=int, default=20402024)
    parser.add_argument("--n", type=int, default=2400)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    _metrics, summary, manifest = run_risk_proxy_stress_grid(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        n=args.n,
        device=args.device,
    )
    print(summary.groupby(["method"])[["detection_rate", "mean_rmse"]].mean().to_string())
    print(f"cells={manifest['design']['cell_count']} rows={manifest['metric_rows']}")
    print(f"metrics_sha256={manifest['metrics_sha256']}")
    print(f"output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
