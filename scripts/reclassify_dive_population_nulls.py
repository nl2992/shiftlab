"""Correct saved DIVE labels for known population-null control scenarios."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from shiftlab.dive.evaluation import apply_population_null_classification
from shiftlab.dive.experiment import _plots, finalize_manifest, refresh_report_with_uncertainty
from shiftlab.dive.hard_budget import (
    _append_paired_comparisons,
    _plot_hard_budget,
)
from shiftlab.dive.hard_budget import (
    _summarize as summarize_hard_budget,
)


def reclassify_saved_comparison(root: Path) -> pd.DataFrame:
    metrics_path = root / "metrics" / "method_comparison.parquet"
    metrics = pd.read_parquet(metrics_path)
    corrected = apply_population_null_classification(metrics)
    corrected.to_parquet(metrics_path, index=False)

    report_path = root / "reports" / "method_comparison.md"
    report = report_path.read_text(encoding="utf-8")
    replacement = (
        "Stationary and benign-nuisance streams are population-null controls, independently "
        "verified below epsilon. Their finite-stream oracle averages can cross epsilon by "
        "chance; those pathwise flags are retained as `sample_path_material_harm` and are not "
        "counted as true alternatives. Every monitor alarm on these population-null controls "
        "counts as a false escalation. For shifted alternatives, evaluator-known finite-regime "
        "oracle averages continue to define the sample-specific harm onset."
    )
    legacy = (
        "Evaluator materiality and onset are computed from oracle conditional expected costs "
        "averaged over each finite simulated regime, not a population-risk estimate with zero "
        "Monte Carlo error. In this run, 7/30 benign-nuisance streams crossed the 0.1 threshold "
        "although the across-seed mean harm remained below it; treat that borderline control "
        "label as seed-sensitive."
    )
    report = report_path.read_text(encoding="utf-8").replace(legacy, replacement)
    report_path.write_text(report, encoding="utf-8")

    _plots(corrected, root / "figures")
    refresh_report_with_uncertainty(root)
    manifest_path = root / "reports" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["population_null_reclassification"] = {
        "scenario_names": ["stationary", "benign_nuisance"],
        "classification": "finite-stream oracle flags retained separately; alarms count as null false escalations",
        "observed_streams_and_alarm_times_preserved": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(root)
    return corrected


def reclassify_saved_hard_budget(root: Path) -> pd.DataFrame:
    metrics_path = root / "metrics" / "hard_budget_comparison.parquet"
    metrics = apply_population_null_classification(pd.read_parquet(metrics_path))
    metrics.to_parquet(metrics_path, index=False)
    summary = summarize_hard_budget(metrics)
    summary.to_csv(root / "metrics" / "hard_budget_summary.csv", index=False)
    report_path = root / "reports" / "hard_budget_comparison.md"
    figure_path = root / "figures" / "hard_budget_tradeoff.png"
    if figure_path.parent.exists():
        _plot_hard_budget(metrics, figure_path)
    if not report_path.exists():
        manifest_path = root / "reports" / "manifest.json"
        if manifest_path.exists():
            finalize_manifest(root)
        return metrics

    report = report_path.read_text(encoding="utf-8")
    report = report.replace(
        "The e-process is evaluated only through its budget stopping time. Harm detection is "
        "reported both over all evaluator-labeled harmful streams and over harmful streams whose "
        "onset occurred before budget stopping; the latter avoids calling an unobserved late "
        "onset a monitor miss. Stream seeds are the inferential units. The outcomes and tariffs "
        "are synthetic; current and reference policy costs are paired on the same label.",
        "The e-process is evaluated only through its budget stopping time. Harm detection is "
        "reported over evaluator-labeled alternatives and over onsets reached before budget "
        "stopping. Stationary and benign-nuisance controls are population nulls; finite-stream "
        "oracle flags are listed separately and every alarm on these controls counts as a false "
        "escalation. Stream seeds are the inferential units. The outcomes and tariffs are "
        "synthetic; current and reference policy costs are paired on the same label.",
    )
    table_start = report.index("|Scenario|Method|Mean cap")
    try:
        table_end = report.index("\n\n## Full-horizon consistency check", table_start)
    except ValueError:
        table_end = report.index("\n\n## ", table_start)
    header = [
        "Scenario",
        "Method",
        "Mean cap",
        "Mean spend",
        "Mean cap use",
        "Mean labels",
        "Monitor fraction",
        "Stream-mean RMSE",
        "Harm reached / harmful streams",
        "Pathwise oracle flags",
        "Fixed detection all / reached",
        "Multiscale detection all / reached",
        "Protected detection all / reached",
        "Fixed / multiscale / protected false escalation",
    ]
    table = ["|" + "|".join(header) + "|", "|" + "|".join(["---:"] * len(header)) + "|"]
    for row in summary.to_dict("records"):

        def rate_text(value: float) -> str:
            return "n/a" if pd.isna(value) else f"{value:.3f}"

        cells = [
            str(row["scenario"]),
            str(row["method"]),
            f"{row['mean_budget']:.2f}",
            f"{row['mean_spend']:.2f}",
            f"{row['budget_utilization']:.3f}",
            f"{row['mean_labels']:.1f}",
            f"{row['mean_monitor_fraction']:.3f}",
            f"{row['stream_mean_rmse']:.4f}",
            f"{row['harm_reachable_streams']}/{row['harmful_streams']}",
            str(row["sample_path_materiality_flags"]),
            f"{rate_text(row['detection_rate_all_harm'])} / {rate_text(row['detection_rate_reached_harm'])}",
            f"{rate_text(row['multiscale_detection_rate_all_harm'])} / {rate_text(row['multiscale_detection_rate_reached_harm'])}",
            f"{rate_text(row['protected_detection_rate_all_harm'])} / {rate_text(row['protected_detection_rate_reached_harm'])}",
            f"{row['false_escalation_rate']:.3f} / {rate_text(row['multiscale_false_escalation_rate'])} / {rate_text(row['protected_false_escalation_rate'])}",
        ]
        table.append("|" + "|".join(cells) + "|")
    report = report[:table_start] + "\n".join(table) + report[table_end:]
    report_path.write_text(report, encoding="utf-8")

    manifest_path = root / "reports" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seed = int(manifest.get("configuration", {}).get("seed_offset", 0)) + 443
    if {"multiscale_e_detected", "protected_e_detected"} <= set(metrics.columns):
        _append_paired_comparisons(root, metrics, seed)
    manifest["population_null_reclassification"] = {
        "scenario_names": ["stationary", "benign_nuisance"],
        "classification": "finite-stream oracle flags retained separately; alarms count as null false escalations",
        "observed_streams_and_alarm_times_preserved": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(root)

    analysis_path = root / "reports" / "stake_mixture_analysis.md"
    if analysis_path.exists():
        candidate = (
            "protected_e_detected" if "protected_e_detected" in metrics else "multiscale_e_detected"
        )
        subprocess.run(
            [
                sys.executable,
                "scripts/analyze_betting_mixture.py",
                "--input",
                str(metrics_path),
                "--candidate-column",
                candidate,
            ],
            check=True,
        )
        finalize_manifest(root)
    return metrics


def main() -> None:
    root = Path("outputs")
    metrics = reclassify_saved_comparison(root)
    controls = metrics.loc[metrics.population_null_control]
    print(f"Reclassified {len(controls)} population-null control rows.")
    for monitor in ("single_e", "mixture_e"):
        alarm_column = f"{monitor}_alarm"
        for scenario, group in controls.groupby("scenario", sort=True):
            print(
                f"{scenario} {monitor}: {int(group[alarm_column].sum())}/{len(group)} false escalations"
            )
    for scenario, group in controls.groupby("scenario", sort=True):
        print(
            f"{scenario}: {int(group.sample_path_material_harm.sum())}/{len(group)} "
            "finite-stream oracle flags retained"
        )
    for metrics_path in sorted(root.glob("hard_budget_*/metrics/hard_budget_comparison.parquet")):
        output = metrics_path.parents[1]
        corrected = reclassify_saved_hard_budget(output)
        null_metrics = corrected.loc[corrected.population_null_control]
        print(
            f"{output.name}: {len(null_metrics)} population-null rows, "
            f"{int(null_metrics.single_e_false_escalation.sum())} fixed-monitor false escalations"
        )


if __name__ == "__main__":
    main()
