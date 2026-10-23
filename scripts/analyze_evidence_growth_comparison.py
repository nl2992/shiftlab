"""Paired-seed analysis for the expected-evidence allocation experiment."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from shiftlab.dive.experiment import finalize_manifest


def _wilson(successes: int, trials: int) -> tuple[float, float]:
    if trials == 0:
        return float("nan"), float("nan")
    z = float(norm.ppf(0.975))
    rate = successes / trials
    denominator = 1 + z**2 / trials
    center = (rate + z**2 / (2 * trials)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / trials + z**2 / (4 * trials**2)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _paired_bootstrap(
    difference: np.ndarray,
    *,
    rng: np.random.Generator,
    draws: int = 50_000,
) -> tuple[float, float, float]:
    values = np.asarray(difference, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("paired seed differences must be finite with at least two seeds")
    samples = rng.integers(0, len(values), size=(draws, len(values)))
    means = values[samples].mean(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(values.mean()), float(low), float(high)


def analyze(output: Path) -> Path:
    metrics_path = output / "metrics/method_comparison.parquet"
    metrics = pd.read_parquet(metrics_path)
    if metrics.duplicated(["scenario", "seed", "method"]).any():
        raise ValueError("metrics contain duplicate scenario/seed/method rows")
    available = set(metrics.method)
    if "uniform_proxy" not in available or not available.intersection(
        {"evidence_growth_proxy", "evidence_growth_stabilized_proxy"}
    ):
        raise ValueError("the run must include uniform and at least one evidence-growth policy")

    summary_rows: list[dict[str, object]] = []
    effect_rows: list[dict[str, object]] = []
    seed_rng = np.random.default_rng(20261023)
    effects = {
        "detection_rate": "single_e_detected",
        "false_escalation_rate": "single_e_false_escalation",
        "labels_per_stream": "labels_queried",
        "mean_query_propensity": "propensity_mean",
        "cumulative_net_cost": "cumulative_net_cost_vs_reference",
    }
    for scenario, group in metrics.groupby("scenario", sort=True):
        for method, method_rows in group.groupby("method", sort=True):
            n = len(method_rows)
            false_count = int(method_rows.single_e_false_escalation.sum())
            false_ci = _wilson(false_count, n)
            harmful = method_rows[method_rows.material_harm]
            detections = int(harmful.single_e_detected.sum())
            detection_ci = _wilson(detections, len(harmful))
            errors = method_rows.stream_mean_estimation_error.to_numpy(dtype=float)
            summary_rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "streams": n,
                    "false_escalations": false_count,
                    "false_escalation_wilson_low": false_ci[0],
                    "false_escalation_wilson_high": false_ci[1],
                    "harmful_stream_detections": detections,
                    "harmful_streams": len(harmful),
                    "detection_wilson_low": detection_ci[0],
                    "detection_wilson_high": detection_ci[1],
                    "mean_labels": float(method_rows.labels_queried.mean()),
                    "mean_query_propensity": float(method_rows.propensity_mean.mean()),
                    "stream_mean_rmse": float(np.sqrt(np.mean(errors**2))),
                    "mean_net_cost": float(method_rows.cumulative_net_cost_vs_reference.mean()),
                }
            )

        reference = group[group.method.eq("uniform_proxy")].set_index("seed")
        for method in sorted(set(group.method) - {"uniform_proxy"}):
            candidate = group[group.method.eq(method)].set_index("seed")
            if set(candidate.index) != set(reference.index):
                raise ValueError(f"{scenario}/{method} does not share the uniform seed set")
            candidate = candidate.loc[reference.index]
            for metric_name, column in effects.items():
                eligible = (
                    candidate.material_harm.astype(bool)
                    if metric_name == "detection_rate"
                    else pd.Series(True, index=candidate.index)
                )
                if metric_name == "detection_rate":
                    if not eligible.any():
                        continue
                    a = candidate.loc[eligible, column].to_numpy(dtype=float)
                    b = reference.loc[eligible, column].to_numpy(dtype=float)
                else:
                    a = candidate[column].to_numpy(dtype=float)
                    b = reference[column].to_numpy(dtype=float)
                mean, low, high = _paired_bootstrap(a - b, rng=seed_rng)
                effect_rows.append(
                    {
                        "scenario": scenario,
                        "method": method,
                        "metric": metric_name,
                        "candidate_minus_uniform": mean,
                        "bootstrap_95_low": low,
                        "bootstrap_95_high": high,
                        "paired_seeds": len(a),
                    }
                )
            cand_error = candidate.stream_mean_estimation_error.to_numpy(dtype=float)
            ref_error = reference.stream_mean_estimation_error.to_numpy(dtype=float)
            candidate_rmse = float(np.sqrt(np.mean(cand_error**2)))
            ref_rmse = float(np.sqrt(np.mean(ref_error**2)))
            draw_idx = seed_rng.integers(0, len(cand_error), size=(50_000, len(cand_error)))
            rmse_delta = np.sqrt(np.mean(cand_error[draw_idx] ** 2, axis=1)) - np.sqrt(
                np.mean(ref_error[draw_idx] ** 2, axis=1)
            )
            low, high = np.quantile(rmse_delta, [0.025, 0.975])
            effect_rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "metric": "stream_mean_rmse",
                    "candidate_minus_uniform": candidate_rmse - ref_rmse,
                    "bootstrap_95_low": float(low),
                    "bootstrap_95_high": float(high),
                    "paired_seeds": len(cand_error),
                }
            )

    summary = pd.DataFrame(summary_rows)
    effects_frame = pd.DataFrame(effect_rows)
    summary_path = output / "metrics/evidence_growth_summary.csv"
    effects_path = output / "metrics/evidence_growth_paired_effects.csv"
    summary.to_csv(summary_path, index=False)
    effects_frame.to_csv(effects_path, index=False)

    report = [
        "# Expected-evidence allocation: paired evaluation",
        "",
        f"This report analyzes `{metrics_path.as_posix()}`. Independent stream seeds are the inferential units; all method contrasts are paired by seed. The monitor-period stream was not used to fit the outcome or decision-loss models.",
        "",
        "## Detection, false escalation, budget use, and estimation",
        "",
        "Rates have Wilson 95% intervals. `mean_query_propensity` is the average of predictable monitor propensities; labels are realized Bernoulli queries. The stream-mean RMSE is calculated across seed-level estimation errors.",
        "",
        "| Scenario | Method | False escalations / streams (95% Wilson) | Detections / harmful streams (95% Wilson) | Labels/stream | Mean propensity | Stream-mean RMSE | Mean net cost |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        fci = (
            f"[{row['false_escalation_wilson_low']:.3f}, {row['false_escalation_wilson_high']:.3f}]"
        )
        dci = (
            "—"
            if row["harmful_streams"] == 0
            else f"[{row['detection_wilson_low']:.3f}, {row['detection_wilson_high']:.3f}]"
        )
        report.append(
            f"| {row['scenario']} | {row['method']} | {row['false_escalations']}/{row['streams']} {fci} | {row['harmful_stream_detections']}/{row['harmful_streams']} {dci} | {row['mean_labels']:.1f} | {row['mean_query_propensity']:.4f} | {row['stream_mean_rmse']:.4f} | {row['mean_net_cost']:.2f} |"
        )
    report.extend(
        [
            "",
            "## Paired differences versus uniform PPI",
            "",
            "Intervals are percentile bootstrap intervals over paired seeds. They are descriptive, unadjusted across methods and metrics, and should not be read as confirmatory hypothesis tests.",
            "",
            "| Scenario | Method | Metric | Difference vs uniform (95% paired bootstrap) | Seeds |",
            "|---|---|---|---:|---:|",
        ]
    )
    for row in effects_frame.to_dict("records"):
        report.append(
            f"| {row['scenario']} | {row['method']} | {row['metric']} | {row['candidate_minus_uniform']:+.4f} [{row['bootstrap_95_low']:+.4f}, {row['bootstrap_95_high']:+.4f}] | {row['paired_seeds']} |"
        )
    report.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The raw evidence-growth allocation may shift its average query rate under covariate shift because it is calibrated on the validation distribution. The stabilized version mixes it toward uniform; its stated rate-drift guarantee assumes every deployment propensity remains in `[q_min,q_max]`. Neither allocation changes the monitor's e-process validity conditions. The expected-log-growth optimization is exact only for its estimated outcome model and fixed stake-weighted surrogate; it is not an optimality claim for detection power or the exact log-mixture e-value.",
            "",
            "Reproduce the underlying run with `uv run shiftlab-dive --seeds 30 --n 3200 --d 16 --query-rate 0.10 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy decision_value_proxy evidence_growth_stabilized_proxy --device cuda --seed-offset 20272024 --evidence-rate-stability-tolerance 0.01 --output outputs/evidence_growth_stabilized_replication_30`, then run `uv run python scripts/analyze_evidence_growth_comparison.py`.",
        ]
    )
    report_path = output / "reports/evidence_growth_paired_comparison.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    finalize_manifest(output)
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("outputs/evidence_growth_stabilized_replication_30")
    )
    args = parser.parse_args()
    print(analyze(args.output), flush=True)


if __name__ == "__main__":
    main()
