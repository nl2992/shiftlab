"""Analyze the independent robust mixture-growth acquisition evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import binomtest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shiftlab.dive.experiment import finalize_manifest

ROBUST = "robust_mixture_growth_proxy"
BASELINES = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
    "exact_mixture_growth_proxy",
)


def analyze(output: Path) -> Path:
    metrics = pd.read_parquet(output / "metrics" / "hard_budget_comparison.parquet")
    if not metrics.budget_respected.all():
        raise ValueError("fresh evaluation contains a hard-budget violation")
    if ROBUST not in set(metrics.method) or set(BASELINES) - set(metrics.method):
        raise ValueError("fresh evaluation does not contain the registered method set")
    seed_offset = int(metrics.seed.min())
    rows: list[dict[str, object]] = []
    lines = [
        "# Fresh evaluation of robust mixture-growth acquisition",
        "",
        "This independent evaluation uses the development-selected probability radius `0.20`, 60 paired seeds per scenario, and the same hard dollar cap, propensity bounds, common e-process bound, stream seeds, and query uniforms for the robust method and six established baselines. The uncertainty interval is centered on the pre-monitor classifier probability. Evaluator-only coverage compares it with the synthetic true conditional probability after query decisions have been made.",
        "",
        "RMSE intervals resample independent stream seeds and are descriptive, unadjusted comparisons across the six baselines. Detection differences are shown descriptively with discordant paired-seed counts; the exact McNemar test is reported for the prespecified robust-versus-uniform contrast because detection events are sparse. Detection is only defined for boundary-local harm; every method's harm reachability is shown separately. A finite run with no false escalation is an implementation diagnostic, not a 5% calibration proof.",
        "",
        "`figures/hard_budget_tradeoff.png` plots paired-seed bootstrap intervals for boundary stream-mean RMSE, Wilson intervals for boundary-harm detection, and the processed stream fraction for all seven acquisition policies.",
        "",
        "|Scenario|Baseline|Robust detections / baseline|Harm reached robust / baseline|Paired detection difference (wins / losses)|Robust / baseline RMSE|RMSE difference (95% bootstrap CI)|Spend difference|Label difference|Processed-fraction difference|Robust interval coverage|False escalations robust / baseline|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario in sorted(metrics.scenario.unique()):
        group = metrics.loc[metrics.scenario.eq(scenario)]
        wide = group.pivot(index="seed", columns="method")
        robust = wide.xs(ROBUST, axis=1, level=1).sort_index()
        for baseline_name in BASELINES:
            baseline = wide.xs(baseline_name, axis=1, level=1).sort_index()
            if not robust.index.equals(baseline.index):
                raise ValueError(f"{ROBUST} is not seed-matched to {baseline_name} in {scenario}")
            seed_rng = np.random.default_rng(
                seed_offset + len(scenario) + BASELINES.index(baseline_name) * 31
            )
            n = len(robust)
            indices = seed_rng.integers(0, n, size=(50_000, n))
            harmful = scenario == "boundary_local_harm"
            det_r = robust.single_e_detected.astype(float).to_numpy()
            det_b = baseline.single_e_detected.astype(float).to_numpy()
            detection_delta = det_r - det_b
            error_r = robust.stream_mean_estimation_error.to_numpy(dtype=float)
            error_b = baseline.stream_mean_estimation_error.to_numpy(dtype=float)
            rmse_delta_draws = np.sqrt(np.mean(error_r[indices] ** 2, axis=1)) - np.sqrt(
                np.mean(error_b[indices] ** 2, axis=1)
            )
            rmse_r = float(np.sqrt(np.mean(error_r**2)))
            rmse_b = float(np.sqrt(np.mean(error_b**2)))
            robust_harm = robust.loc[robust.material_harm]
            base_harm = baseline.loc[baseline.material_harm]
            row: dict[str, object] = {
                "scenario": scenario,
                "baseline": baseline_name,
                "streams": n,
                "robust_detections": int(robust_harm.single_e_detected.sum()) if harmful else None,
                "baseline_detections": int(base_harm.single_e_detected.sum()) if harmful else None,
                "robust_harm_reached": int(robust.harm_reached_before_budget_stop.sum()),
                "baseline_harm_reached": int(baseline.harm_reached_before_budget_stop.sum()),
                "paired_detection_difference": float(detection_delta.mean()) if harmful else None,
                "robust_detection_wins": int((detection_delta > 0).sum()) if harmful else None,
                "robust_detection_losses": int((detection_delta < 0).sum()) if harmful else None,
                "robust_rmse": rmse_r,
                "baseline_rmse": rmse_b,
                "rmse_difference": rmse_r - rmse_b,
                "rmse_ci_low": float(np.quantile(rmse_delta_draws, 0.025)),
                "rmse_ci_high": float(np.quantile(rmse_delta_draws, 0.975)),
                "spend_difference": float(
                    (robust.realized_label_spend - baseline.realized_label_spend).mean()
                ),
                "label_difference": float((robust.labels_queried - baseline.labels_queried).mean()),
                "processed_fraction_difference": float(
                    (robust.monitor_fraction_processed - baseline.monitor_fraction_processed).mean()
                ),
                "robust_probability_interval_coverage": float(
                    robust.robust_probability_interval_coverage.mean()
                ),
                "robust_false_escalations": int(robust.single_e_false_escalation.sum()),
                "baseline_false_escalations": int(baseline.single_e_false_escalation.sum()),
                "robust_budget_violations": int((~robust.budget_respected).sum()),
            }
            rows.append(row)
            if harmful:
                detection_text = (
                    f"{row['robust_detections']}/{n} / {row['baseline_detections']}/{n}"
                )
                detection_delta_text = (
                    f"{row['paired_detection_difference']:+.3f} "
                    f"({row['robust_detection_wins']} / {row['robust_detection_losses']})"
                )
            else:
                detection_text = detection_delta_text = "n/a"
            lines.append(
                f"|{scenario}|{baseline_name}|{detection_text}|"
                f"{row['robust_harm_reached']}/{n} / {row['baseline_harm_reached']}/{n}|"
                f"{detection_delta_text}|"
                f"{rmse_r:.4f} / {rmse_b:.4f}|{rmse_r - rmse_b:+.4f} "
                f"[{np.quantile(rmse_delta_draws, 0.025):+.4f}, {np.quantile(rmse_delta_draws, 0.975):+.4f}]|"
                f"{row['spend_difference']:+.2f}|{row['label_difference']:+.1f}|"
                f"{row['processed_fraction_difference']:+.3f}|"
                f"{row['robust_probability_interval_coverage']:.3f}|"
                f"{row['robust_false_escalations']} / {row['baseline_false_escalations']}|"
            )

    boundary = metrics.loc[metrics.scenario.eq("boundary_local_harm")].pivot(
        index="seed", columns="method", values="single_e_detected"
    )
    robust_win = int((boundary[ROBUST] & ~boundary["uniform_proxy"]).sum())
    robust_loss = int((~boundary[ROBUST] & boundary["uniform_proxy"]).sum())
    mcnemar = float(binomtest(robust_win, robust_win + robust_loss, p=0.5).pvalue)
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The development rule selected radius `0.20` because the candidate radii all had zero boundary-harm detections and this setting had the lowest boundary stream-mean RMSE under the tie-break. In the fresh boundary-harm block, the robust method detected {int(boundary[ROBUST].sum())}/60 and uniform detected {int(boundary['uniform_proxy'].sum())}/60. {robust_win} paired seeds favored robust sampling and {robust_loss} favored uniform; exact two-sided McNemar p={mcnemar:.3f}. This is evidence about one synthetic scenario only.",
            "",
            "Interpret the RMSE contrasts as estimation efficiency, separately from harm detection. A lower stream-mean RMSE does not establish higher e-process power, and the interval-robust optimization is valid only as an allocation objective under the specified probability set. The anytime-validity conditions do not require that set to contain the true post-shift probability, but model misspecification may eliminate the intended allocation benefit.",
            "",
            f"Reproduce the run with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset {seed_offset} --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --robust-growth-probability-radius 0.20 --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy robust_mixture_growth_proxy --device cuda --output outputs/robust_growth_grid_fresh_60`, then run `uv run python scripts/analyze_robust_growth_fresh.py --output outputs/robust_growth_grid_fresh_60`.",
            "",
        ]
    )
    paired = pd.DataFrame(rows)
    paired.to_csv(output / "metrics" / "robust_growth_fresh_paired.csv", index=False)
    methods = [*BASELINES, ROBUST]
    labels = [
        "Uniform",
        "Variance",
        "Decision\nvalue",
        "Cost\nvariance",
        "Cost\nstabilized",
        "Exact\ngrowth",
        "Robust\ngrowth",
    ]
    boundary_rows = metrics.loc[metrics.scenario.eq("boundary_local_harm")]
    boundary_wide = boundary_rows.pivot(index="seed", columns="method")
    rmse_values = np.array(
        [
            np.sqrt(np.mean(boundary_wide.stream_mean_estimation_error[method] ** 2))
            for method in methods
        ]
    )
    rmse_rng = np.random.default_rng(seed_offset + 910_021)
    rmse_draws = np.empty((10_000, len(methods)))
    error_matrix = np.column_stack(
        [boundary_wide.stream_mean_estimation_error[method].to_numpy() for method in methods]
    )
    for start in range(0, len(rmse_draws), 250):
        idx = rmse_rng.integers(0, len(error_matrix), size=(250, len(error_matrix)))
        rmse_draws[start : start + len(idx)] = np.sqrt(np.mean(error_matrix[idx] ** 2, axis=1))
    rmse_low, rmse_high = np.quantile(rmse_draws, [0.025, 0.975], axis=0)
    detection_counts = np.array(
        [int(boundary_wide.single_e_detected[method].sum()) for method in methods]
    )
    detection_rate = detection_counts / len(boundary_wide)
    z = 1.959963984540054
    denom = 1 + z**2 / len(boundary_wide)
    center = (detection_rate + z**2 / (2 * len(boundary_wide))) / denom
    half = (
        z
        * np.sqrt(
            detection_rate * (1 - detection_rate) / len(boundary_wide)
            + z**2 / (4 * len(boundary_wide) ** 2)
        )
        / denom
    )
    monitor_fraction = np.array(
        [
            boundary_rows.loc[boundary_rows.method.eq(method), "monitor_fraction_processed"].mean()
            for method in methods
        ]
    )
    x = np.arange(len(methods))
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2), constrained_layout=True)
    axes[0].bar(x, rmse_values, color="#337ab7")
    axes[0].errorbar(
        x,
        rmse_values,
        yerr=np.vstack((rmse_values - rmse_low, rmse_high - rmse_values)),
        fmt="none",
        ecolor="black",
        capsize=3,
    )
    axes[0].set_title("Boundary stream-mean RMSE")
    axes[0].set_ylabel("RMSE (lower is better)")
    axes[1].bar(x, detection_rate, color="#e1812c")
    axes[1].errorbar(
        x,
        detection_rate,
        yerr=np.vstack((detection_rate - center + half, center + half - detection_rate)),
        fmt="none",
        ecolor="black",
        capsize=3,
    )
    axes[1].set_title("Boundary-harm detection")
    axes[1].set_ylabel("Detected streams / 60")
    axes[1].set_ylim(0, max(0.12, float((center + half).max() * 1.2)))
    axes[2].bar(x, monitor_fraction, color="#59a14f")
    axes[2].set_title("Processed stream fraction")
    axes[2].set_ylabel("Fraction processed")
    for axis in axes:
        axis.set_xticks(x, labels, rotation=0)
        axis.grid(axis="y", alpha=0.25)
    fig.suptitle("Robust mixture-growth acquisition: independent 60-seed evaluation")
    fig.savefig(output / "figures" / "hard_budget_tradeoff.png", dpi=180)
    plt.close(fig)
    report_path = output / "reports" / "robust_growth_fresh_analysis.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    finalize_manifest(output)
    manifest_path = output / "reports" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["paired_analysis"] = {
        "script": "scripts/analyze_robust_growth_fresh.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "bootstrap_resamples": 50_000,
        "seed_offset": seed_offset,
        "mcnemar_two_sided_p_vs_uniform": mcnemar,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/robust_growth_grid_fresh_60"))
    args = parser.parse_args()
    print(analyze(args.output))


if __name__ == "__main__":
    main()
