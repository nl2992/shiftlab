"""Validate and summarize the fresh common-bound hard-budget replication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import beta

from shiftlab.dive.experiment import finalize_manifest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/hard_budget_matched_qmin_010_replication_60"
METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)
SCENARIOS = ("stationary", "benign_nuisance", "boundary_local_harm")


def _exact_interval(successes: int, total: int, alpha: float = 0.05) -> tuple[float, float]:
    if total <= 0:
        return float("nan"), float("nan")
    low = 0.0 if successes == 0 else float(beta.ppf(alpha / 2, successes, total - successes + 1))
    high = (
        1.0
        if successes == total
        else float(beta.ppf(1 - alpha / 2, successes + 1, total - successes))
    )
    return low, high


def _bootstrap_difference(
    candidate: np.ndarray,
    baseline: np.ndarray,
    *,
    rng: np.random.Generator,
    draws: int = 50_000,
) -> tuple[float, float, float]:
    difference = np.asarray(candidate, dtype=float) - np.asarray(baseline, dtype=float)
    if difference.ndim != 1 or len(difference) < 2:
        raise ValueError("paired bootstrap requires at least two one-dimensional seed outcomes")
    indices = rng.integers(0, len(difference), size=(draws, len(difference)))
    boot = difference[indices].mean(axis=1)
    return (
        float(difference.mean()),
        float(np.quantile(boot, 0.025)),
        float(np.quantile(boot, 0.975)),
    )


def _bootstrap_rmse_difference(
    candidate_error: np.ndarray,
    baseline_error: np.ndarray,
    *,
    rng: np.random.Generator,
    draws: int = 50_000,
) -> tuple[float, float, float]:
    candidate = np.asarray(candidate_error, dtype=float)
    baseline = np.asarray(baseline_error, dtype=float)
    if candidate.ndim != 1 or baseline.shape != candidate.shape or len(candidate) < 2:
        raise ValueError("paired RMSE bootstrap requires equal one-dimensional seed outcomes")
    indices = rng.integers(0, len(candidate), size=(draws, len(candidate)))
    boot = np.sqrt(np.mean(candidate[indices] ** 2, axis=1)) - np.sqrt(
        np.mean(baseline[indices] ** 2, axis=1)
    )
    return (
        float(np.sqrt(np.mean(candidate**2)) - np.sqrt(np.mean(baseline**2))),
        float(np.quantile(boot, 0.025)),
        float(np.quantile(boot, 0.975)),
    )


def main() -> None:
    metrics_path = OUTPUT / "metrics/hard_budget_comparison.parquet"
    metrics = pd.read_parquet(metrics_path)
    expected_rows = 60 * len(SCENARIOS) * len(METHODS)
    if len(metrics) != expected_rows:
        raise ValueError(f"expected {expected_rows} rows, found {len(metrics)}")
    if set(metrics.scenario) != set(SCENARIOS) or set(metrics.method) != set(METHODS):
        raise ValueError("scenario or method set differs from the locked protocol")
    if metrics.seed.nunique() != 60:
        raise ValueError("expected 60 unique fresh stream seeds")
    if set(metrics.seed.unique()) != set(range(20_362_022, 20_362_082)):
        raise ValueError("stream seed block differs from the locked protocol")
    if not np.allclose(metrics.eprocess_minimum_propensity, 0.10):
        raise ValueError("e-process bounds are not common at q_min=0.10")
    if (
        not metrics.budget_respected.all()
        or (metrics.realized_label_spend > metrics.hard_budget + 1e-9).any()
    ):
        raise ValueError("a run violated the pathwise dollar cap")
    if metrics.duplicated(["scenario", "seed", "method"]).any():
        raise ValueError("duplicate scenario-seed-method rows")
    if not metrics.groupby(["scenario", "seed"]).hard_budget.nunique().eq(1).all():
        raise ValueError("methods did not share a per-stream budget")

    rng = np.random.default_rng(20362023)
    rows: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        scenario_rows = metrics.loc[metrics.scenario.eq(scenario)]
        baseline = scenario_rows.loc[scenario_rows.method.eq("uniform_proxy")].sort_values("seed")
        for method in METHODS:
            group = scenario_rows.loc[scenario_rows.method.eq(method)].sort_values("seed")
            alarms = int(group.single_e_detected.sum())
            low, high = _exact_interval(alarms, len(group))
            false_alarms = int(group.single_e_false_escalation.sum())
            false_low, false_high = _exact_interval(false_alarms, len(group))
            row: dict[str, Any] = {
                "scenario": scenario,
                "method": method,
                "streams": len(group),
                "material_harm_streams": int(group.material_harm.sum()),
                "harm_reached": int(group.harm_reached_before_budget_stop.sum()),
                "detections": alarms,
                "detection_rate": alarms / len(group),
                "detection_ci_low": low,
                "detection_ci_high": high,
                "false_escalations": false_alarms,
                "false_escalation_ci_low": false_low,
                "false_escalation_ci_high": false_high,
                "mean_labels": float(group.labels_queried.mean()),
                "mean_realized_spend": float(group.realized_label_spend.mean()),
                "mean_budget": float(group.hard_budget.mean()),
                "mean_monitor_fraction": float(group.monitor_fraction_processed.mean()),
                "stream_mean_rmse": float(
                    np.sqrt(np.mean(group.stream_mean_estimation_error.to_numpy(dtype=float) ** 2))
                ),
                "mean_delay_when_detected": float(group.single_e_delay.dropna().mean()),
            }
            if method != "uniform_proxy":
                base = baseline.set_index("seed")
                candidate = group.set_index("seed").loc[base.index]
                detection_diff = _bootstrap_difference(
                    candidate.single_e_detected.to_numpy(dtype=float),
                    base.single_e_detected.to_numpy(dtype=float),
                    rng=rng,
                )
                rmse_diff = _bootstrap_rmse_difference(
                    candidate.stream_mean_estimation_error.to_numpy(dtype=float),
                    base.stream_mean_estimation_error.to_numpy(dtype=float),
                    rng=rng,
                )
                row.update(
                    detection_difference_vs_uniform=detection_diff[0],
                    detection_difference_ci_low=detection_diff[1],
                    detection_difference_ci_high=detection_diff[2],
                    rmse_difference_vs_uniform=rmse_diff[0],
                    rmse_difference_ci_low=rmse_diff[1],
                    rmse_difference_ci_high=rmse_diff[2],
                )
            rows.append(row)

    summary = pd.DataFrame(rows)
    summary_path = OUTPUT / "metrics/matched_bound_replication_summary.csv"
    summary.to_csv(summary_path, index=False)
    report_path = OUTPUT / "reports/matched_bound_replication_analysis.md"
    lines = [
        "# Matched-bound hard-budget replication",
        "",
        "This is a fresh 60-seed replication under the locked protocol in `docs/hard_budget_matched_bound_protocol.md`. All five policies use the same fixed e-process bound with `q_min=0.10`, a 20% target spend rate, and `q_max=0.80`. Each policy shares the same stream seed and hard dollar cap within a stream. Synthetic truth is used for evaluator metrics only.",
        "",
        f"Validation checks passed: {len(metrics)} unique method-stream rows; 60 seeds in each of three scenarios; common e-process minimum propensity 0.10; no hard-budget violations.",
        "",
        "Exact two-sided Clopper-Pearson intervals describe detection rates. Paired percentile bootstrap intervals use 50,000 resamples of stream seeds and estimate adaptive-minus-uniform differences. These are descriptive intervals for this replication; they are not adjusted for multiple method comparisons.",
        "",
        "|Scenario|Method|Detection / streams (95% exact CI)|Harm reached / material|False escalations / streams (95% exact CI)|Mean labels|Mean spend / cap|RMSE|RMSE difference vs uniform (95% paired bootstrap CI)|Mean delay if detected|Detection-rate difference vs uniform (95% paired bootstrap CI)|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        ci = f"[{row['detection_ci_low']:.3f}, {row['detection_ci_high']:.3f}]"
        false_ci = f"[{row['false_escalation_ci_low']:.3f}, {row['false_escalation_ci_high']:.3f}]"
        diff = "—"
        rmse_diff_text = "—"
        if row["method"] != "uniform_proxy":
            diff = (
                f"{row['detection_difference_vs_uniform']:+.3f} "
                f"[{row['detection_difference_ci_low']:+.3f}, {row['detection_difference_ci_high']:+.3f}]"
            )
            rmse_diff_text = (
                f"{row['rmse_difference_vs_uniform']:+.4f} "
                f"[{row['rmse_difference_ci_low']:+.4f}, {row['rmse_difference_ci_high']:+.4f}]"
            )
        delay_value = float(row["mean_delay_when_detected"])
        delay = "—" if np.isnan(delay_value) else f"{delay_value:.1f}"
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['detections']}/{row['streams']} {ci}|"
            f"{row['harm_reached']}/{row['material_harm_streams']}|"
            f"{row['false_escalations']}/{row['streams']} {false_ci}|"
            f"{row['mean_labels']:.1f}|{row['mean_realized_spend']:.2f} / {row['mean_budget']:.2f}|"
            f"{row['stream_mean_rmse']:.4f}|{rmse_diff_text}|{delay}|{diff}|"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Detection is the primary endpoint only for boundary-local harm. Stationary and benign-nuisance alarm counts are safety diagnostics; benign-shift power is interpretable only for evaluator-labeled materially harmful streams. On boundary-local harm, cost-stabilized allocation detected 12/60 streams versus 8/60 for uniform (paired difference +0.067; 95% seed-bootstrap CI [0.000, 0.150]); the interval touches zero, is not multiplicity-adjusted, and does not establish an advantage. Its RMSE difference was computed on the same paired seeds. Do not infer a general allocation winner from this single block.",
            "",
            "No method is declared optimal from this single seed block. Any threshold, allocation, or budget change requires a new seed block for evaluation.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    manifest_path = OUTPUT / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["analysis"] = {
        "script": "scripts/analyze_matched_bound_replication.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "rng_seed": 20362023,
        "bootstrap_draws": 50_000,
        "confidence_interval": "exact two-sided Clopper-Pearson for binary rates; paired seed bootstrap for differences",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(OUTPUT)
    print(summary_path.relative_to(ROOT))
    print(report_path.relative_to(ROOT))
    print(
        summary.loc[
            summary.scenario.eq("boundary_local_harm"),
            [
                "method",
                "detections",
                "harm_reached",
                "material_harm_streams",
                "detection_difference_vs_uniform",
                "detection_difference_ci_low",
                "detection_difference_ci_high",
            ],
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
