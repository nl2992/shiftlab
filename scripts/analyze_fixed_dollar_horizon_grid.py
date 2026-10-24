"""Summarize a fixed-dollar decision-harm horizon development grid."""

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

HORIZONS = (1000, 1800, 2600)
SCENARIO_CELLS = (
    "stationary",
    "benign_nuisance",
    "boundary_early",
    "boundary_late",
    "recurring_regimes",
    "harmful_adaptation",
)
MONITORS = ("fixed_mixture", "predictable_variance", "pm_eb", "pprm_mix_w0p1")
DETECTION_COLUMNS = {
    "fixed_mixture": ("single_e_detected", "single_e_false_escalation", "single_e_alarm_time"),
    "predictable_variance": (
        "variance_adaptive_detected",
        "variance_adaptive_false_escalation",
        "variance_adaptive_alarm_time",
    ),
    "pm_eb": ("pm_eb_detected", "pm_eb_false_escalation", "pm_eb_alarm_time"),
    "pprm_mix_w0p1": (
        "pprm_mix_w0p1_detected",
        "pprm_mix_w0p1_false_escalation",
        "pprm_mix_w0p1_alarm_time",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials < 1:
        return float("nan"), float("nan")
    p = successes / trials
    denominator = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denominator
    radius = z * np.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def _monitor_rows(frame: pd.DataFrame) -> pd.DataFrame:
    eventwise = frame.loc[frame.method.eq("uniform_proxy")].copy()
    block = frame.loc[frame.method.eq("pprm_block_adaptive")].copy()
    rows: list[dict[str, object]] = []
    for source, monitor in (
        (eventwise, "fixed_mixture"),
        (eventwise, "predictable_variance"),
        (eventwise, "pm_eb"),
        (block, "pprm_mix_w0p1"),
    ):
        detected_col, false_col, alarm_col = DETECTION_COLUMNS[monitor]
        for record in source.to_dict("records"):
            detected = bool(record[detected_col])
            onset = record["harm_onset_relative"]
            alarm = record[alarm_col]
            rows.append(
                {
                    "scenario": record["scenario"],
                    "cell": record["cell"],
                    "horizon": int(record["horizon"]),
                    "monitor": monitor,
                    "seed": int(record["seed"]),
                    "population_null_control": bool(record["population_null_control"]),
                    "material_harm": bool(record["material_harm"]),
                    "harm_onset_relative": onset,
                    "harm_reached": bool(record["harm_reached_before_budget_stop"]),
                    "detected": detected,
                    "false_escalation": bool(record[false_col]),
                    "delay": int(alarm - onset)
                    if detected and alarm is not None and onset is not None
                    else np.nan,
                    "processed_events": int(record["processed_events"]),
                    "labels_queried": int(record["labels_queried"]),
                    "realized_label_spend": float(record["realized_label_spend"]),
                    "hard_budget": float(record["hard_budget"]),
                    "mean_expected_decision_harm": float(record["mean_expected_decision_harm"]),
                    "stream_mean_estimation_rmse": float(record["stream_mean_estimation_rmse"]),
                }
            )
    return pd.DataFrame(rows)


def _summarize(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (cell, horizon, monitor), group in frame.groupby(["cell", "horizon", "monitor"], sort=True):
        harmful = group.loc[group.material_harm]
        reached = harmful.loc[harmful.harm_reached]
        controls = group.loc[group.population_null_control]
        detections = int(harmful.detected.sum())
        reached_detections = int(reached.detected.sum())
        false_alarms = int(controls.false_escalation.sum())
        lower, upper = _wilson(detections, len(harmful))
        f_lower, f_upper = _wilson(false_alarms, len(controls))
        rows.append(
            {
                "cell": cell,
                "horizon": horizon,
                "monitor": monitor,
                "streams": len(group),
                "harmful_streams": len(harmful),
                "harm_onsets_reached": int(harmful.harm_reached.sum()),
                "detections_all_harm": detections,
                "detection_rate_all_harm": detections / len(harmful) if len(harmful) else np.nan,
                "detection_wilson_95_low": lower,
                "detection_wilson_95_high": upper,
                "detection_rate_reached_harm": reached_detections / len(reached)
                if len(reached)
                else np.nan,
                "mean_delay_detected": float(harmful.loc[harmful.detected, "delay"].mean()),
                "control_streams": len(controls),
                "false_escalations": false_alarms,
                "false_escalation_rate": false_alarms / len(controls) if len(controls) else np.nan,
                "false_wilson_95_low": f_lower,
                "false_wilson_95_high": f_upper,
                "mean_events_processed": float(group.processed_events.mean()),
                "mean_labels": float(group.labels_queried.mean()),
                "mean_dollar_spend": float(group.realized_label_spend.mean()),
                "mean_budget_utilization": float(
                    (group.realized_label_spend / group.hard_budget).mean()
                ),
                "mean_expected_decision_harm": float(group.mean_expected_decision_harm.mean()),
                "mean_stream_estimation_rmse": float(group.stream_mean_estimation_rmse.mean()),
            }
        )
    return pd.DataFrame(rows)


def _paired_detection_contrasts(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    harm = frame.loc[frame.material_harm]
    for (cell, horizon), group in harm.groupby(["cell", "horizon"], sort=True):
        wide = group.pivot(index="seed", columns="monitor", values="detected").sort_index()
        for comparator in MONITORS:
            if comparator == "fixed_mixture":
                continue
            left = wide["fixed_mixture"].to_numpy(dtype=bool)
            right = wide[comparator].to_numpy(dtype=bool)
            fixed_only = int(np.sum(left & ~right))
            comparator_only = int(np.sum(~left & right))
            discordant = fixed_only + comparator_only
            p_value = float(binomtest(fixed_only, discordant).pvalue) if discordant else 1.0
            digest = hashlib.sha256(f"{cell}:{horizon}:{comparator}".encode()).digest()
            rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
            draws = rng.integers(0, len(left), size=(20_000, len(left)))
            differences = left[draws].astype(np.int8) - right[draws].astype(np.int8)
            rows.append(
                {
                    "cell": cell,
                    "horizon": horizon,
                    "candidate": "fixed_mixture",
                    "comparator": comparator,
                    "streams": len(left),
                    "fixed_only": fixed_only,
                    "comparator_only": comparator_only,
                    "rate_difference": float(left.mean() - right.mean()),
                    "paired_bootstrap_95_low": float(np.quantile(differences.mean(axis=1), 0.025)),
                    "paired_bootstrap_95_high": float(np.quantile(differences.mean(axis=1), 0.975)),
                    "mcnemar_exact_p": p_value,
                }
            )
    result = pd.DataFrame(rows)
    order = np.argsort(result.mcnemar_exact_p.to_numpy())
    adjusted = np.empty(len(result), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(result) - rank) * result.mcnemar_exact_p.iloc[index])
        adjusted[index] = min(1.0, running)
    result["holm_adjusted_p"] = adjusted
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("outputs/fixed_dollar_horizon_grid_development")
    )
    args = parser.parse_args()
    grid_config = json.loads((args.input / "grid_config.json").read_text(encoding="utf-8"))
    frames = []
    run_hashes = {}
    run_manifest_hashes = {}
    for horizon in HORIZONS:
        for cell in SCENARIO_CELLS:
            run_dir = args.input / f"horizon_{horizon:04d}" / cell
            path = run_dir / "metrics" / "hard_budget_comparison.parquet"
            if not path.is_file():
                raise FileNotFoundError(f"missing frozen grid cell: {path}")
            metrics = pd.read_parquet(path)
            metrics["cell"] = cell
            metrics["horizon"] = horizon
            run_manifest = run_dir / "reports" / "manifest.json"
            if not run_manifest.is_file():
                raise FileNotFoundError(f"missing run manifest: {run_manifest}")
            run_metadata = json.loads(run_manifest.read_text(encoding="utf-8"))
            run_config = run_metadata["configuration"]
            if (
                run_config["n"] != grid_config["n"]
                or run_config["monitor_horizon_events"] != horizon
                or run_config["budget_dollars"] != grid_config["fixed_label_dollar_cap"]
                or run_config["seed_offset"] != grid_config["seed_offset"]
                or run_config["seeds"] != grid_config["seeds_per_cell"]
            ):
                raise ValueError(f"run configuration differs from frozen grid in {run_dir}")
            expected_scenario = next(
                item["scenario"] for item in grid_config["scenarios"] if item["cell"] == cell
            )
            if run_config["scenario_subset"] != [expected_scenario]:
                raise ValueError(f"scenario differs from frozen grid in {run_dir}")
            for relative_path, expected_hash in run_metadata["sha256"]["artifacts"].items():
                artifact = run_dir / Path(relative_path)
                if not artifact.is_file() or _sha256(artifact) != expected_hash:
                    raise ValueError(f"run artifact hash mismatch: {artifact}")
            if metrics.seed.nunique() != grid_config["seeds_per_cell"]:
                raise ValueError(f"unexpected seed count in {run_dir}")
            expected_seeds = set(
                range(
                    grid_config["seed_offset"],
                    grid_config["seed_offset"] + grid_config["seeds_per_cell"],
                )
            )
            if set(metrics.seed.astype(int)) != expected_seeds:
                raise ValueError(f"seed block differs from frozen grid in {run_dir}")
            if metrics.groupby("method").seed.nunique().min() != grid_config["seeds_per_cell"]:
                raise ValueError(f"incomplete method pairing in {run_dir}")
            if not metrics.budget_respected.all():
                raise ValueError(f"hard budget violation in {run_dir}")
            if not metrics.hard_budget.eq(grid_config["fixed_label_dollar_cap"]).all():
                raise ValueError(f"budget differs from frozen common cap in {run_dir}")
            run_hashes[str(path.relative_to(args.input))] = _sha256(path)
            run_manifest_hashes[str(run_manifest.relative_to(args.input))] = _sha256(run_manifest)
            frames.append(metrics)
    monitor_frame = _monitor_rows(pd.concat(frames, ignore_index=True))
    summary = _summarize(monitor_frame)
    contrasts = _paired_detection_contrasts(monitor_frame)
    analysis_dir = args.input / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    stream_metrics_path = analysis_dir / "monitor_stream_metrics.csv"
    summary_path = analysis_dir / "horizon_summary.csv"
    contrasts_path = analysis_dir / "paired_detection_contrasts.csv"
    report_path = analysis_dir / "fixed_dollar_horizon_results.md"
    monitor_frame.to_csv(stream_metrics_path, index=False)
    summary.to_csv(summary_path, index=False)
    contrasts.to_csv(contrasts_path, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    scenarios = ("boundary_early", "boundary_late", "recurring_regimes", "harmful_adaptation")
    colors = dict(zip(MONITORS, ("#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e"), strict=True))
    labels = {
        "fixed_mixture": "Eventwise fixed mixture",
        "predictable_variance": "Predictable variance",
        "pm_eb": "PM-EB",
        "pprm_mix_w0p1": "Block PPI mixture",
    }
    for ax, cell in zip(axes.ravel(), scenarios, strict=True):
        part = summary.loc[summary.cell.eq(cell)]
        for monitor in MONITORS:
            series = part.loc[part.monitor.eq(monitor)].sort_values("horizon")
            ax.plot(
                series.horizon,
                series.detection_rate_all_harm,
                marker="o",
                label=labels[monitor],
                color=colors[monitor],
            )
            ax.fill_between(
                series.horizon.to_numpy(dtype=float),
                series.detection_wilson_95_low.to_numpy(dtype=float),
                series.detection_wilson_95_high.to_numpy(dtype=float),
                color=colors[monitor],
                alpha=0.12,
            )
        ax.set_title(cell.replace("_", " "))
        ax.set_ylim(0, 1)
        ax.grid(alpha=0.25)
        ax.set_xlabel("Available monitoring events")
        ax.set_ylabel("Detection / all harmful streams")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(
        f"Monitor comparison under a fixed ${grid_config['fixed_label_dollar_cap']:.0f} label budget"
    )
    fig.tight_layout()
    figure_path = args.input / "analysis" / "fixed_dollar_horizon_detection.png"
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)

    control = summary.loc[summary.cell.isin(("stationary", "benign_nuisance"))]
    harm = summary.loc[summary.cell.isin(scenarios)]
    lines = [
        "# Fixed-dollar horizon monitor development grid",
        "",
        f"This development screen compares four monitoring procedures over {grid_config['seeds_per_cell']} paired seeds in each of six scenario cells and three horizons. Every run used the same ${grid_config['fixed_label_dollar_cap']:.2f} realized label-dollar cap, the same full generated n=4,000 stream, and a prefix of that stream as the available monitor horizon. The source model and pre-monitor validation split were therefore held fixed across horizons. CUDA was requested; inspect each run manifest for the resolved device.",
        "",
        "Eventwise fixed-mixture, predictable-variance, and PM-EB monitors share the uniform-query labels within each stream. The block PPI mixture uses its registered 20-event / four-label block design under the same dollar cap; its block labels are not identical to the eventwise labels. All procedures use alpha=.05, harm margin=.10, q_min=.20 (eventwise), and the predeclared fixed 10% block-PPI mixture. This is a development grid: intervals are descriptive, no winner is selected, and no claim of general superiority follows.",
        "",
        "## Harm results",
        "",
        "Rates use all evaluator-classified harmful streams in the denominator; the reached-harm rate is reported separately so budget-censored onsets are visible. Wilson intervals are marginal and not multiplicity-adjusted.",
        "",
        "| Cell | Horizon | Monitor | Detect / harm | Reached | Rate (95% Wilson) | Reached rate | Mean delay | Mean events | Mean labels | Mean spend |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in harm.itertuples(index=False):
        lines.append(
            f"| {row.cell} | {row.horizon} | {row.monitor} | {row.detections_all_harm}/{row.harmful_streams} | {row.harm_onsets_reached}/{row.harmful_streams} | {row.detection_rate_all_harm:.3f} [{row.detection_wilson_95_low:.3f}, {row.detection_wilson_95_high:.3f}] | {row.detection_rate_reached_harm:.3f} | {row.mean_delay_detected:.1f} | {row.mean_events_processed:.1f} | {row.mean_labels:.1f} | ${row.mean_dollar_spend:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Population-null controls",
            "",
            "| Cell | Horizon | Monitor | False escalations / streams | Rate (95% Wilson) | Mean events | Mean labels | Mean spend |",
            "|---|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in control.itertuples(index=False):
        lines.append(
            f"| {row.cell} | {row.horizon} | {row.monitor} | {row.false_escalations}/{row.control_streams} | {row.false_escalation_rate:.3f} [{row.false_wilson_95_low:.3f}, {row.false_wilson_95_high:.3f}] | {row.mean_events_processed:.1f} | {row.mean_labels:.1f} | ${row.mean_dollar_spend:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Paired detection contrasts",
            "",
            "Positive rate difference favors the fixed mixture. Paired bootstrap intervals and exact McNemar p-values use common seeds; Holm adjustment covers all fixed-mixture-versus-comparator contrasts across the 12 harmful cell/horizon combinations. These remain exploratory because this block is a development grid.",
            "",
            "| Cell | Horizon | Comparator | Fixed-only / comparator-only | Difference (paired 95% bootstrap CI) | Exact p | Holm p |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in contrasts.itertuples(index=False):
        lines.append(
            f"| {row.cell} | {row.horizon} | {row.comparator} | {row.fixed_only}/{row.comparator_only} | {row.rate_difference:.3f} [{row.paired_bootstrap_95_low:.3f}, {row.paired_bootstrap_95_high:.3f}] | {row.mcnemar_exact_p:.4g} | {row.holm_adjusted_p:.4g} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "The synthetic evaluator supplies true material-harm onset and labels only to scoring; the monitoring procedures receive the declared query feedback. This study holds the generated stream, source fit, validation slice, and total dollar cap fixed across available horizons. It does not establish validity for delayed feedback, arbitrary serial dependence, adaptively selected policy candidates, or deployment distributions beyond these registered generators. The comparison identifies empirical power and cost trade-offs for a development design; a confirmatory claim requires a frozen method and separate seed block.",
            "",
            "![Detection across available horizons](fixed_dollar_horizon_detection.png)",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "experiment": grid_config["experiment"],
        "grid_config": grid_config,
        "grid_config_sha256": _sha256(args.input / "grid_config.json"),
        "runner_sha256": _sha256(Path(__file__).with_name("run_fixed_dollar_horizon_grid.py")),
        "analyzer_sha256": _sha256(Path(__file__)),
        "input_run_metrics_sha256": run_hashes,
        "input_run_manifest_sha256": run_manifest_hashes,
        "outputs_sha256": {
            path.name: _sha256(path)
            for path in (
                stream_metrics_path,
                summary_path,
                contrasts_path,
                report_path,
                figure_path,
            )
        },
    }
    (analysis_dir / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(report_path)


if __name__ == "__main__":
    main()
