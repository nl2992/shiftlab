"""Validate and summarize the prespecified start-time mixture horizon grid."""

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
CELLS = (
    "stationary",
    "benign_nuisance",
    "boundary_early",
    "boundary_late",
    "recurring_regimes",
    "harmful_adaptation",
)
MONITORS = {
    "fixed_mixture": ("single_e_detected", "single_e_false_escalation", "single_e_alarm_time"),
    "started_mixture": (
        "started_mixture_e_detected",
        "started_mixture_e_false_escalation",
        "started_mixture_e_alarm_time",
    ),
    "predictable_variance": (
        "variance_adaptive_detected",
        "variance_adaptive_false_escalation",
        "variance_adaptive_alarm_time",
    ),
    "pm_eb": ("pm_eb_detected", "pm_eb_false_escalation", "pm_eb_alarm_time"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(successes: int, trials: int) -> tuple[float, float]:
    if not trials:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = successes / trials
    denom = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denom
    radius = z * np.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denom
    return max(0.0, center - radius), min(1.0, center + radius)


def collect_rows(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for record in frame.to_dict("records"):
        for monitor, (detected_col, false_col, alarm_col) in MONITORS.items():
            alarm = record[alarm_col]
            onset = record["harm_onset_relative"]
            detected = bool(record[detected_col])
            rows.append(
                {
                    "cell": record["cell"],
                    "scenario": record["scenario"],
                    "horizon": int(record["horizon"]),
                    "seed": int(record["seed"]),
                    "monitor": monitor,
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


def summarize(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (cell, horizon, monitor), group in frame.groupby(["cell", "horizon", "monitor"], sort=True):
        harm = group.loc[group.material_harm]
        reached = harm.loc[harm.harm_reached]
        controls = group.loc[group.population_null_control]
        detections = int(harm.detected.sum())
        false = int(controls.false_escalation.sum())
        low, high = wilson(detections, len(harm))
        f_low, f_high = wilson(false, len(controls))
        rows.append(
            {
                "cell": cell,
                "horizon": horizon,
                "monitor": monitor,
                "streams": len(group),
                "harm_streams": len(harm),
                "onsets_reached": int(harm.harm_reached.sum()),
                "detections": detections,
                "detection_rate_all_harm": detections / len(harm) if len(harm) else np.nan,
                "detection_wilson_95_low": low,
                "detection_wilson_95_high": high,
                "detection_rate_reached_harm": int(reached.detected.sum()) / len(reached)
                if len(reached)
                else np.nan,
                "mean_delay_when_detected": float(harm.loc[harm.detected, "delay"].mean()),
                "control_streams": len(controls),
                "false_escalations": false,
                "false_escalation_rate": false / len(controls) if len(controls) else np.nan,
                "false_wilson_95_low": f_low,
                "false_wilson_95_high": f_high,
                "mean_events_processed": float(group.processed_events.mean()),
                "mean_labels": float(group.labels_queried.mean()),
                "mean_dollar_spend": float(group.realized_label_spend.mean()),
                "mean_estimation_rmse": float(group.stream_mean_estimation_rmse.mean()),
            }
        )
    return pd.DataFrame(rows)


def paired_contrasts(frame: pd.DataFrame) -> pd.DataFrame:
    harms = frame.loc[frame.material_harm]
    rows = []
    for (cell, horizon), group in harms.groupby(["cell", "horizon"], sort=True):
        wide = group.pivot(index="seed", columns="monitor", values="detected").sort_index()
        candidate = wide["started_mixture"].to_numpy(dtype=bool)
        baseline = wide["fixed_mixture"].to_numpy(dtype=bool)
        candidate_only = int(np.sum(candidate & ~baseline))
        baseline_only = int(np.sum(~candidate & baseline))
        discordant = candidate_only + baseline_only
        p_value = float(binomtest(candidate_only, discordant).pvalue) if discordant else 1.0
        digest = hashlib.sha256(f"{cell}:{horizon}:started_vs_fixed".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "little"))
        draws = rng.integers(0, len(candidate), size=(20000, len(candidate)))
        diffs = candidate[draws].astype(np.int8) - baseline[draws].astype(np.int8)
        rows.append(
            {
                "cell": cell,
                "horizon": horizon,
                "streams": len(candidate),
                "started_only": candidate_only,
                "fixed_only": baseline_only,
                "rate_difference_started_minus_fixed": float(candidate.mean() - baseline.mean()),
                "paired_bootstrap_95_low": float(np.quantile(diffs.mean(axis=1), 0.025)),
                "paired_bootstrap_95_high": float(np.quantile(diffs.mean(axis=1), 0.975)),
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
        "--input", type=Path, default=Path("outputs/started_mixture_horizon_development")
    )
    args = parser.parse_args()
    root = args.input
    config_path = root / "grid_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    grid_manifest_path = root / "grid_manifest.json"
    grid_manifest = json.loads(grid_manifest_path.read_text(encoding="utf-8"))
    if (
        grid_manifest["configuration"] != config
        or grid_manifest["configuration_sha256"] != sha256(config_path)
        or grid_manifest["runner_sha256"]
        != sha256(Path("scripts/run_started_mixture_horizon_grid.py"))
        or grid_manifest["protocol_sha256"]
        != sha256(Path("docs/started_mixture_horizon_protocol.md"))
    ):
        raise ValueError(
            "grid manifest does not match the frozen configuration, runner, or protocol"
        )
    source_frames = []
    run_hashes = {}
    manifest_hashes = {}
    expected_seeds = set(
        range(config["seed_offset"], config["seed_offset"] + config["seeds_per_cell"])
    )
    for horizon in HORIZONS:
        for cell in CELLS:
            run_dir = root / f"horizon_{horizon:04d}" / cell
            metrics_path = run_dir / "metrics" / "hard_budget_comparison.parquet"
            manifest_path = run_dir / "reports" / "manifest.json"
            if not metrics_path.is_file() or not manifest_path.is_file():
                raise FileNotFoundError(f"incomplete cell: {run_dir}")
            metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
            run_config = metadata["configuration"]
            if (
                run_config["n"] != config["n"]
                or run_config["monitor_horizon_events"] != horizon
                or run_config["budget_dollars"] != config["budget_dollars"]
                or run_config["seed_offset"] != config["seed_offset"]
                or run_config["seeds"] != config["seeds_per_cell"]
                or run_config["method_subset"] != ["uniform_proxy"]
                or run_config["monitor_comparators"] != ["variance_adaptive", "pm_eb"]
                or run_config["budget_rate"] != config["budget_rate"]
                or run_config["q_min"] != config["q_min"]
                or run_config["q_max"] != config["q_max"]
                or run_config["alpha"] != config["alpha"]
                or run_config["harm_margin"] != config["harm_margin"]
                or not run_config["common_eprocess_bound"]
                or run_config["scenario_subset"]
                != [item["scenario"] for item in config["scenario_cells"] if item["cell"] == cell]
            ):
                raise ValueError(f"run differs from frozen configuration: {run_dir}")
            for relative, digest in metadata["sha256"]["artifacts"].items():
                artifact = run_dir / relative
                if not artifact.is_file() or sha256(artifact) != digest:
                    raise ValueError(f"run artifact hash mismatch: {artifact}")
            metrics = pd.read_parquet(metrics_path)
            if set(metrics.method) != {"uniform_proxy"}:
                raise ValueError(f"unexpected acquisition methods in {metrics_path}")
            if set(metrics.seed.astype(int)) != expected_seeds or len(metrics) != len(
                expected_seeds
            ):
                raise ValueError(f"seed set/count mismatch: {metrics_path}")
            if (
                not metrics.budget_respected.all()
                or not metrics.hard_budget.eq(config["budget_dollars"]).all()
            ):
                raise ValueError(f"budget invariant failed: {metrics_path}")
            required = {name for triplet in MONITORS.values() for name in triplet}
            if required - set(metrics.columns):
                raise ValueError(
                    f"monitor outcomes missing in {metrics_path}: {required - set(metrics.columns)}"
                )
            metrics["cell"] = cell
            metrics["horizon"] = horizon
            source_frames.append(metrics)
            run_hashes[str(metrics_path.relative_to(root))] = sha256(metrics_path)
            manifest_hashes[str(manifest_path.relative_to(root))] = sha256(manifest_path)

    streams = collect_rows(pd.concat(source_frames, ignore_index=True))
    summary = summarize(streams)
    contrasts = paired_contrasts(streams)
    analysis_dir = root / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    stream_path = analysis_dir / "monitor_stream_metrics.csv"
    summary_path = analysis_dir / "horizon_summary.csv"
    contrasts_path = analysis_dir / "paired_start_mixture_contrasts.csv"
    report_path = analysis_dir / "started_mixture_results.md"
    figure_path = analysis_dir / "started_mixture_detection.png"
    streams.to_csv(stream_path, index=False)
    summary.to_csv(summary_path, index=False)
    contrasts.to_csv(contrasts_path, index=False)

    colors = {
        "fixed_mixture": "#1f77b4",
        "started_mixture": "#d62728",
        "predictable_variance": "#2ca02c",
        "pm_eb": "#9467bd",
    }
    labels = {
        "fixed_mixture": "Full-stream mixture",
        "started_mixture": "Four-start mixture",
        "predictable_variance": "Predictable variance",
        "pm_eb": "PM-EB",
    }
    cells = ("boundary_early", "boundary_late", "recurring_regimes", "harmful_adaptation")
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
    for ax, cell in zip(axes.ravel(), cells, strict=True):
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
        ax.set_xlabel("Available monitor events")
        ax.set_ylabel("Detection / all harmful streams")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(
        f"Start-time mixture under a fixed ${config['budget_dollars']:.0f} label-dollar cap"
    )
    fig.tight_layout()
    fig.savefig(figure_path, dpi=170)
    plt.close(fig)

    report = [
        "# Prespecified start-time mixture: development results",
        "",
        f"This CUDA-requested development grid uses {config['seeds_per_cell']} paired seeds per cell, a fixed ${config['budget_dollars']:.0f} label-dollar cap, identical query labels for all eventwise monitors, and horizons {', '.join(map(str, HORIZONS))}. It compares a four-start equal e-process mixture with the full-stream fixed mixture, predictable-variance e-process, and PM-EB.",
        "",
        "The starts are fixed as `{0, H/4, H/2, 3H/4}` (integer floors, duplicate positions removed). A convex mixture of valid e-processes is an established construction; this benchmark does not claim novelty. The 30-stream null controls are too small to establish the target false-escalation rate.",
        "",
        "## Harm detection",
        "",
        "| Cell | Horizon | Monitor | Detections / harm streams | Onsets reached | Mean delay | False escalations / controls | Mean labels | Mean spend |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.itertuples(index=False):
        report.append(
            f"| {row.cell} | {row.horizon} | {row.monitor} | {row.detections}/{row.harm_streams} | {row.onsets_reached} | {row.mean_delay_when_detected:.1f} | {row.false_escalations}/{row.control_streams} | {row.mean_labels:.1f} | ${row.mean_dollar_spend:.2f} |"
        )
    report.extend(
        [
            "",
            "## Paired start-mixture versus full-stream contrasts",
            "",
            "McNemar tests are paired by seed; Holm adjustment covers every harmful cell and horizon in this grid.",
            "",
            "| Cell | Horizon | Start-only | Full-only | Rate difference | Paired 95% bootstrap interval | Holm p |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in contrasts.itertuples(index=False):
        report.append(
            f"| {row.cell} | {row.horizon} | {row.started_only} | {row.fixed_only} | {row.rate_difference_started_minus_fixed:.3f} | [{row.paired_bootstrap_95_low:.3f}, {row.paired_bootstrap_95_high:.3f}] | {row.holm_adjusted_p:.4g} |"
        )
    report.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "These development estimates map the trade-off; they do not select a universally best process. Every monitor shares the same eventwise corrected estimates and dollar expenditure within a seed. Nondetections remain in the all-harm denominator, and onset reachability is shown separately. A confirmatory result requires independent high-precision null calibration and a fresh alternative seed block with a frozen primary contrast.",
            "",
            "Reproduction: `uv run python scripts/run_started_mixture_horizon_grid.py --seeds 30 --seed-offset 57100000 --budget-dollars 720 --device cuda`, then `uv run python scripts/analyze_started_mixture_horizon_grid.py`.",
        ]
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    output_paths = [stream_path, summary_path, contrasts_path, report_path, figure_path]
    manifest = {
        "experiment": config["experiment"],
        "grid_config_sha256": sha256(config_path),
        "runner_sha256": sha256(Path("scripts/run_started_mixture_horizon_grid.py")),
        "analyzer_sha256": sha256(Path(__file__)),
        "input_run_metrics_sha256": run_hashes,
        "input_run_manifest_sha256": manifest_hashes,
        "outputs_sha256": {path.name: sha256(path) for path in output_paths},
        "n_runs": len(run_hashes),
        "n_stream_monitor_rows": len(streams),
        "analysis_status": "development; not confirmatory",
    }
    (analysis_dir / "analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(report_path)


if __name__ == "__main__":
    main()
