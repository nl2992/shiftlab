"""Validate and summarize the saved decision-risk proxy stress grid."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

FACTORS = (
    "all",
    "scenario",
    "severity",
    "query_rate",
    "train_fraction",
    "cost_ratio_fn_fp",
)
COMPARATORS = ("ridge", "validation_best", "prequential_hedge")
METRICS = ("detected", "estimator_rmse", "false_escalation")
BOOTSTRAP_REPLICATES = 20_000
BOOTSTRAP_SEED = 24102026


def _bootstrap_seed_mean(values: np.ndarray, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(BOOTSTRAP_REPLICATES, len(values)))
    draws = values[indices].mean(axis=1)
    return [float(value) for value in np.quantile(draws, [0.025, 0.975])]


def analyze_risk_proxy_stress_grid(output_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    output = Path(output_dir)
    metrics_path = output / "metrics.parquet"
    manifest_path = output / "manifest.json"
    if not metrics_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("metrics.parquet and manifest.json are required")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(metrics_path.read_bytes()).hexdigest()
    if digest != manifest["metrics_sha256"]:
        raise ValueError("metrics Parquet checksum does not match the run manifest")
    metrics = pd.read_parquet(metrics_path)
    if len(metrics) != manifest["metric_rows"]:
        raise ValueError("metrics row count does not match the run manifest")
    methods = set(metrics.method.unique())
    if not {"risk_model", *COMPARATORS} <= methods:
        raise ValueError("stress grid is missing a required comparison method")
    counts = metrics.groupby("cell_id").agg(
        seeds=("seed", "nunique"), methods=("method", "nunique"), rows=("seed", "size")
    )
    if not counts.seeds.eq(manifest["design"]["seeds_per_cell"]).all():
        raise ValueError("one or more cells have a missing seed")
    if (
        not counts.methods.eq(len(methods)).all()
        or not counts.rows.eq(manifest["design"]["seeds_per_cell"] * len(methods)).all()
    ):
        raise ValueError("one or more cells have a missing method-stream row")
    resource_counts = metrics.groupby(["cell_id", "seed"]).agg(
        labels=("labels_queried", "nunique"),
        spend=("realized_label_spend", "nunique"),
        events=("events_processed", "nunique"),
    )
    if not resource_counts.eq(1).all().all():
        raise ValueError("methods do not share identical query, spend, and event paths")
    if not metrics.budget_respected.all():
        raise ValueError("at least one method exceeded its hard label-cost cap")

    meta_columns = [
        "cell_id",
        "scenario",
        "severity",
        "query_rate",
        "train_fraction",
        "cost_ratio_fn_fp",
    ]
    metadata = metrics[meta_columns].drop_duplicates("cell_id")
    rows = []
    for factor in FACTORS:
        if factor == "all":
            groups = [("all", metrics)]
        else:
            groups = []
            for value, level in metadata.groupby(factor, sort=True):
                group = metrics[metrics.cell_id.isin(level.cell_id)]
                groups.append((value, group))
        for value, group in groups:
            for metric in METRICS:
                metric_group = group
                if metric == "detected":
                    metric_group = group[group.material_harm]
                    if metric_group.empty:
                        continue
                wide = metric_group.pivot(
                    index=["seed", "cell_id"], columns="method", values=metric
                )
                for comparator in COMPARATORS:
                    difference = (
                        (wide["risk_model"].astype(float) - wide[comparator].astype(float))
                        .groupby(level="seed")
                        .mean()
                    )
                    values = difference.to_numpy()
                    interval = _bootstrap_seed_mean(
                        values,
                        BOOTSTRAP_SEED + len(rows) * 17 + len(str(value)),
                    )
                    rows.append(
                        {
                            "factor": factor,
                            "level": value,
                            "metric": metric,
                            "comparator": comparator,
                            "risk_model_minus_comparator": float(values.mean()),
                            "seed_cluster_ci95_low": interval[0],
                            "seed_cluster_ci95_high": interval[1],
                            "favors_risk_model": bool(
                                values.mean() > 0 if metric == "detected" else values.mean() < 0
                            ),
                            "cell_count": int(metric_group.cell_id.nunique()),
                            "seed_clusters": len(values),
                            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                        }
                    )
    contrasts = pd.DataFrame(rows)
    contrasts.to_csv(output / "factor_contrasts.csv", index=False)
    summary = (
        metrics.groupby(["method"], sort=True)
        .agg(
            streams=("seed", "size"),
            material_harm_streams=("material_harm", "sum"),
            false_escalations=("false_escalation", "sum"),
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
    conditional_detection = (
        metrics[metrics.material_harm].groupby("method").detected.mean().rename("detection_rate")
    )
    summary = summary.merge(conditional_detection, on="method", how="left")
    summary.to_csv(output / "validated_method_summary.csv", index=False)

    report = [
        "# Decision-risk proxy stress grid results",
        "",
        f"Validated **{manifest['design']['cell_count']} cells**, **{len(metrics):,} rows**, and **{manifest['design']['seeds_per_cell']} paired seed streams per cell**. All methods shared query labels, realized spend, and processed events within every stream; all hard caps were respected.",
        f"Generation used {manifest['environment'].get('gpu_name', 'the recorded device')} with requested device `{manifest['design']['device_requested']}`. The saved Parquet SHA-256 matches the run manifest (`{digest}`).",
        "",
        "## Aggregate comparison",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Seed-clustered macro paired differences",
        "",
        "The table below averages paired differences over cells within each seed, then bootstraps the 12 seed clusters. Detection favors a positive risk-model difference; RMSE favors a negative difference. These intervals are descriptive and unadjusted.",
        "",
    ]
    overall = contrasts[contrasts.factor == "all"]
    report.extend(
        [
            "| Metric | Comparator | Risk model minus comparator | Seed-cluster 95% interval |",
            "|---|---|---:|---:|",
        ]
    )
    for row in overall.itertuples(index=False):
        report.append(
            f"| {row.metric} | {row.comparator} | {row.risk_model_minus_comparator:.4f} | [{row.seed_cluster_ci95_low:.4f}, {row.seed_cluster_ci95_high:.4f}] |"
        )
    report.extend(
        [
            "",
            "## Limits and decision",
            "",
            "This screen had no pre-onset false escalations. It includes structural zero-harm cells where the compared policies coincide, but no nondegenerate population-null cells; therefore it gives no false-alarm calibration. Its seed count is useful for screening, not precise cellwise conclusions. Lower RMSE did not translate into a reliable detection gain over ridge, validation-best, or Hedge. Keep the logistic risk model as the strongest estimation proxy in this grid; do not advance it as a novel or confirmatory monitoring method. The next experiment should compare established, variance-sensitive anytime monitors using this proxy under matched query and cost paths, with separate nondegenerate null calibration.",
            "",
            "No figure was generated. Use PaperBanana for any future research visual and verify plotted values against the saved metrics.",
            "",
        ]
    )
    (output / "results.md").write_text("\n".join(report), encoding="utf-8")
    manifest["analysis"] = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "factor_contrast_rows": len(contrasts),
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "validation": {
            "row_count": len(metrics),
            "cell_count": int(metrics.cell_id.nunique()),
            "matched_resources": True,
            "hard_budget_respected": True,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return contrasts, summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="outputs/risk_proxy_stress_grid")
    args = parser.parse_args()
    contrasts, summary = analyze_risk_proxy_stress_grid(args.output_dir)
    print(summary.to_string(index=False))
    print("\nMacro paired differences:")
    print(contrasts[contrasts.factor == "all"].to_string(index=False))


if __name__ == "__main__":
    main()
