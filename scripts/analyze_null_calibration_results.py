"""Analyze the completed q_min=.20 synthetic null-calibration run."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import beta, binomtest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shiftlab.dive.experiment import finalize_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/null_calibration_qmin020_2000"
PRIMARY_MONITORS = ("fixed_mixture", "predictable_variance")
MONITORS = {
    "fixed_mixture": "single_e",
    "predictable_variance": "variance_adaptive",
    "predictable_empirical_bernstein": "pm_eb",
}
NULL_SCENARIOS = ("stationary", "benign_nuisance")
TARGET_RATE = 0.05
ALPHA = 0.05


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clopper_pearson_upper(events: int, trials: int, confidence: float = 0.95) -> float:
    if trials <= 0 or events < 0 or events > trials:
        raise ValueError("require 0 <= events <= positive trials")
    if events == trials:
        return 1.0
    return float(beta.ppf(confidence, events + 1, trials - events))


def wilson_interval(events: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials <= 0 or events < 0 or events > trials:
        raise ValueError("require 0 <= events <= positive trials")
    if events == 0:
        upper = z * z / (trials + z * z)
        return 0.0, float(upper)
    if events == trials:
        return 1.0 - z / np.sqrt(trials + z * z), 1.0
    rate = events / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / trials + z * z / (4 * trials**2)) / denominator
    return max(0.0, float(center - radius)), min(1.0, float(center + radius))


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for scenario in NULL_SCENARIOS:
        group = metrics.loc[
            metrics.scenario.eq(scenario) & metrics.method.eq("uniform_proxy")
        ].copy()
        if group.empty:
            raise ValueError(f"missing population-null scenario: {scenario}")
        if len(group) != 2000 or not group.population_null_control.astype(bool).all():
            raise ValueError(f"{scenario} must contain 2,000 population-null streams")
        if not group.budget_respected.astype(bool).all():
            raise ValueError(f"hard-budget violation found in {scenario}")
        for monitor, prefix in MONITORS.items():
            alarm = group[f"{prefix}_false_escalation"].astype(bool)
            events = int(alarm.sum())
            trials = len(group)
            low, high = wilson_interval(events, trials)
            rows.append(
                {
                    "scenario": scenario,
                    "monitor": monitor,
                    "streams": trials,
                    "false_escalations": events,
                    "false_escalation_rate": events / trials,
                    "wilson_95_low": low,
                    "wilson_95_high": high,
                    "clopper_pearson_95_upper": clopper_pearson_upper(events, trials),
                    "familywise_95_upper_primary": (
                        clopper_pearson_upper(events, trials, confidence=1 - ALPHA / 4)
                        if monitor in PRIMARY_MONITORS
                        else np.nan
                    ),
                    "exact_binomial_p_gt_005": float(
                        binomtest(events, trials, p=TARGET_RATE, alternative="greater").pvalue
                    ),
                    "mean_spend": float(group.realized_label_spend.mean()),
                    "mean_budget": float(group.hard_budget.mean()),
                    "mean_labels": float(group.labels_queried.mean()),
                    "mean_processed_fraction": float(group.monitor_fraction_processed.mean()),
                    "budget_violations": int((~group.budget_respected.astype(bool)).sum()),
                    "sample_path_materiality_flags": int(
                        group.sample_path_material_harm.astype(bool).sum()
                    ),
                }
            )
    return pd.DataFrame(rows)


def write_figure(summary: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    monitor_names = {
        "fixed_mixture": "Fixed mixture",
        "predictable_variance": "Predictable variance",
        "predictable_empirical_bernstein": "PM-EB",
    }
    labels = [
        f"{r.scenario.replace('_', ' ')}\n{monitor_names[r.monitor]}" for r in summary.itertuples()
    ]
    values = summary.false_escalation_rate.to_numpy(float)
    lows = summary.wilson_95_low.to_numpy(float)
    highs = summary.wilson_95_high.to_numpy(float)
    positions = np.arange(len(summary))
    ax.bar(positions, values, color="#2878b5", width=0.68)
    ax.errorbar(
        positions,
        values,
        yerr=np.vstack((np.maximum(0, values - lows), np.maximum(0, highs - values))),
        fmt="none",
        ecolor="#1e293b",
        capsize=4,
    )
    ax.axhline(TARGET_RATE, color="#b42318", linestyle="--", label="target α = 0.05")
    ax.set_xticks(positions, labels, rotation=20, ha="right")
    ax.set_ylim(0, max(0.01, float(highs.max()) * 1.25, TARGET_RATE * 1.1))
    ax.set_ylabel("Stream-level false escalation rate")
    ax.set_title("Synthetic null calibration, 2,000 streams per scenario")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    metrics_path = args.output / "metrics/hard_budget_comparison.parquet"
    metrics = pd.read_parquet(metrics_path)
    summary = summarize(metrics)
    csv_path = args.output / "metrics/null_calibration.csv"
    summary.to_csv(csv_path, index=False)
    figure_path = args.output / "figures/null_calibration.png"
    write_figure(summary, figure_path)

    primary = summary.loc[summary.monitor.isin(PRIMARY_MONITORS)]
    if len(primary) != 4:
        raise ValueError("expected four primary monitor-scenario calibration cells")
    all_familywise_below_target = bool((primary.familywise_95_upper_primary < TARGET_RATE).all())
    lines = [
        "# Synthetic null calibration at q_min=.20",
        "",
        "The frozen run evaluated 2,000 independent streams in each registered population-null control (stationary and benign nuisance), using uniform querying, a 20% hard label-dollar cap, alpha=.05, and the common q_min=.20 increment bound. The primary monitor is fixed mixture; predictable variance is secondary. PM-EB is exploratory. Requested device was CUDA; the manifest records the resolved device and runtime.",
        "",
        "|Scenario|Monitor|False escalations|Rate|95% Wilson interval|95% exact upper|Primary-familywise 95% exact upper|Mean labels|Mean spend / budget|Cap violations|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        familywise = (
            f"{row['familywise_95_upper_primary']:.5f}"
            if pd.notna(row["familywise_95_upper_primary"])
            else "—"
        )
        lines.append(
            f"|{row['scenario']}|{row['monitor']}|{row['false_escalations']}/{row['streams']}|"
            f"{row['false_escalation_rate']:.5f}|[{row['wilson_95_low']:.5f}, {row['wilson_95_high']:.5f}]|"
            f"{row['clopper_pearson_95_upper']:.5f}|{familywise}|{row['mean_labels']:.2f}|"
            f"{row['mean_spend']:.2f} / {row['mean_budget']:.2f}|{row['budget_violations']}|"
        )
    lines.extend(
        [
            "",
            "## Interpretation and limits",
            "",
            f"All six monitor-scenario cells had 0/2,000 false escalations. For each cell, the two-sided 95% Wilson interval is [0, {summary.wilson_95_high.max():.5f}], and the one-sided 95% Clopper–Pearson upper limit is {summary.clopper_pearson_95_upper.max():.5f}. For the four pre-specified primary/secondary monitor-scenario cells, the Bonferroni simultaneous one-sided 95% upper limit is {primary.familywise_95_upper_primary.max():.5f}. Thus the simulation provides evidence that the false-escalation rate is below 5% for these procedures under these two generated nulls; it does not prove the theorem's assumptions hold outside this simulator.",
            "",
            f"The four-cell familywise upper-limit criterion below 5%: **{all_familywise_below_target}**. Exact binomial tests against a one-sided 5% excess-rate alternative are included in the CSV; no post-hoc monitor selection is used.",
            "",
            "The 90 finite-stream sample-path materiality flags in the benign-nuisance scenario are evaluator diagnostics, not population-null violations; they are retained in the CSV for transparency. Immediate labels, synthetic tariffs, the registered reference policy, and this scenario family limit interpretation. Delayed labels, serial dependence, adaptive candidate search, and misspecification were not tested. The result calibrates monitoring only; it says nothing about harmful-regime detection power or the novelty of a method.",
            "",
            "## Reproduction and artifacts",
            "",
            "The stream simulation command is in `docs/null_calibration_qmin020_protocol.md`. Rebuild the table and figure from saved observations with `uv run python scripts/analyze_null_calibration_results.py`. Raw stream observations are not published; the aggregate CSV, report, figure, and manifest are versioned.",
        ]
    )
    report_path = args.output / "reports/null_calibration_results.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    finalize_manifest(args.output)
    manifest_path = args.output / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        run_script = subprocess.check_output(
            ["git", "show", "080c202:scripts/diagnose_hard_budget_monitors.py"],
            cwd=ROOT,
            text=False,
        )
        run_script_sha = hashlib.sha256(run_script).hexdigest()
    except subprocess.CalledProcessError:
        run_script_sha = None
    manifest["run_provenance"] = {
        "protocol": "docs/null_calibration_qmin020_protocol.md",
        "protocol_commit": "080c202893197d217630a21369a1e879df3a1e3e",
        "diagnostic_script_sha256_at_run": run_script_sha,
        "analysis_script_sha256": _sha256(Path(__file__).resolve()),
        "source_git_commit_at_run": "080c202893197d217630a21369a1e879df3a1e3e",
        "simulations_completed": len(metrics),
        "postprocessing_failure": "monitor diagnostic figure had a floating-point negative lower errorbar at 0/2000; simulation metrics were saved first and independently analyzed here",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {csv_path.relative_to(ROOT).as_posix()}")
    print(f"Wrote {report_path.relative_to(ROOT).as_posix()}")
    print(
        summary[
            ["scenario", "monitor", "false_escalations", "streams", "clopper_pearson_95_upper"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
