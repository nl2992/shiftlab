"""Run a paired severity/onset/horizon screen for the decision-harm monitor baselines."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import binomtest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.decision_harm_experiment import SCENARIOS as REGISTERED_SCENARIOS
from shiftlab.dive.experiment import finalize_manifest
from shiftlab.dive.hard_budget import (
    HARD_BUDGET_MONITOR_COMPARATORS,
    HardBudgetConfig,
    _generate_stream_rows,
    _wilson_bounds,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/harm_power_grid_30"
SEVERITIES = (0.75, 1.5, 2.25)
ONSET_FRACTIONS = (0.35, 0.50, 0.65)
HORIZONS = (2400, 3200, 4000)
SCENARIOS = ("boundary_local_harm", "recurring_regimes")
MONITORS = {
    "fixed_mixture": "single_e",
    "predictable_variance": "variance_adaptive",
    "predictable_empirical_bernstein": "pm_eb",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _cell_configs():
    for scenario in SCENARIOS:
        for horizon in HORIZONS:
            for severity in SEVERITIES:
                fractions = ONSET_FRACTIONS if scenario == "boundary_local_harm" else (0.50,)
                for onset_fraction in fractions:
                    yield scenario, horizon, severity, onset_fraction


def _summarize(metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["scenario", "n", "scenario_severity", "change_fraction"]
    rows: list[dict[str, object]] = []
    paired: list[dict[str, object]] = []
    for key, group in metrics.groupby(keys, sort=True):
        scenario, n, severity, fraction = key
        harmful = group.material_harm.astype(bool)
        for monitor, prefix in MONITORS.items():
            detected = group[f"{prefix}_detected"].astype(bool) & harmful
            count = int(detected.sum())
            total_harm = int(harmful.sum())
            reached = group.harm_reached_before_budget_stop.astype(bool) & harmful
            reached_count = int(reached.sum())
            reached_detected = int((detected & reached).sum())
            if total_harm:
                lower, upper = _wilson_bounds(np.array([count]), np.array([total_harm]))
                low, high = float(lower[0]), float(upper[0])
                rate = count / total_harm
            else:
                low = high = rate = float("nan")
            delays = pd.to_numeric(group.loc[detected, f"{prefix}_delay"], errors="coerce").dropna()
            rows.append(
                {
                    "scenario": scenario,
                    "n": int(n),
                    "scenario_severity": float(severity),
                    "change_fraction": float(fraction),
                    "monitor": monitor,
                    "streams": len(group),
                    "material_harm_streams": total_harm,
                    "harm_onsets_reached": reached_count,
                    "harm_detections": count,
                    "detection_rate_all_material_harm": rate,
                    "detection_wilson_95_low": low,
                    "detection_wilson_95_high": high,
                    "detection_rate_reached_harm": (
                        reached_detected / reached_count if reached_count else np.nan
                    ),
                    "median_delay_given_detection": float(delays.median())
                    if not delays.empty
                    else np.nan,
                    "mean_spend": float(group.realized_label_spend.mean()),
                    "mean_budget": float(group.hard_budget.mean()),
                    "mean_labels": float(group.labels_queried.mean()),
                    "mean_processed_events": float(group.processed_events.mean()),
                    "mean_processed_fraction": float(group.monitor_fraction_processed.mean()),
                    "budget_violations": int((~group.budget_respected.astype(bool)).sum()),
                    "no_material_harm_streams": int((~harmful).sum()),
                }
            )
        fixed = group.single_e_detected.astype(bool) & harmful
        for monitor, prefix in list(MONITORS.items())[1:]:
            comparator = group[f"{prefix}_detected"].astype(bool) & harmful
            fixed_only = int((fixed & ~comparator).sum())
            comparator_only = int((~fixed & comparator).sum())
            discordant = fixed_only + comparator_only
            paired.append(
                {
                    "scenario": scenario,
                    "n": int(n),
                    "scenario_severity": float(severity),
                    "change_fraction": float(fraction),
                    "primary_monitor": "fixed_mixture",
                    "comparator": monitor,
                    "fixed_only_detections": fixed_only,
                    "comparator_only_detections": comparator_only,
                    "discordant_pairs": discordant,
                    "mcnemar_exact_two_sided_p_exploratory": (
                        float(binomtest(fixed_only, discordant, p=0.5).pvalue)
                        if discordant
                        else 1.0
                    ),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(paired)


def _plot(summary: pd.DataFrame, path: Path) -> None:
    monitors = list(MONITORS)
    fig, axes = plt.subplots(
        len(HORIZONS), len(monitors), figsize=(14, 10), constrained_layout=True
    )
    onset_colors = {0.35: "#174a7e", 0.5: "#3478b7", 0.65: "#8ab6d6"}
    recurring_color = "#e87500"
    for row, horizon in enumerate(HORIZONS):
        for column, monitor in enumerate(monitors):
            ax = axes[row, column]
            data = summary.loc[summary.n.eq(horizon) & summary.monitor.eq(monitor)]
            for scenario in SCENARIOS:
                sub = data.loc[data.scenario.eq(scenario)]
                for fraction, frac_group in sub.groupby("change_fraction", sort=True):
                    frac_group = frac_group.sort_values("scenario_severity")
                    label = (
                        f"boundary onset={fraction:.2f}"
                        if scenario == "boundary_local_harm"
                        else "recurring"
                    )
                    color = (
                        onset_colors[float(fraction)]
                        if scenario == "boundary_local_harm"
                        else recurring_color
                    )
                    ax.plot(
                        frac_group.scenario_severity,
                        frac_group.detection_rate_all_material_harm,
                        marker="o",
                        color=color,
                        linestyle="-" if scenario == "boundary_local_harm" else "--",
                        alpha=0.9 if scenario == "boundary_local_harm" else 0.55,
                        label=label,
                    )
            ax.set_ylim(0, 1)
            ax.set_xticks(SEVERITIES)
            ax.grid(alpha=0.25)
            ax.set_title(f"n={horizon}, {monitor.replace('_', ' ')}")
            if column == 0:
                ax.set_ylabel("Detection / all material-harm streams")
            if row == len(HORIZONS) - 1:
                ax.set_xlabel("DGP severity")
            if row == 0 and column == 0:
                ax.legend(fontsize=7, ncol=2)
    fig.suptitle("Paired development grid: harm severity, onset and horizon (30 streams per cell)")
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


def run_grid(
    output: Path,
    *,
    seeds: int = 30,
    seed_offset: int = 54000000,
    device: str = "cuda",
) -> Path:
    output = output.resolve()
    metrics_path = output / "metrics/harm_power_grid.parquet"
    if metrics_path.exists():
        raise FileExistsError(f"refusing to overwrite completed power grid: {output}")
    if seeds < 1 or seed_offset < 0:
        raise ValueError("seeds must be positive and seed_offset nonnegative")
    resolved = resolve_device(device, n=max(HORIZONS), d=16, chunk_size=2048)
    output.mkdir(parents=True, exist_ok=True)
    for folder in ("metrics", "reports", "figures"):
        (output / folder).mkdir(exist_ok=True)

    scenario_lookup = {item.name: item for item in REGISTERED_SCENARIOS}
    cells = list(_cell_configs())
    rows: list[dict[str, object]] = []
    for cell_index, (scenario_name, n, severity, onset_fraction) in enumerate(cells, 1):
        config = HardBudgetConfig(
            n=n,
            d=16,
            seeds=seeds,
            seed_offset=seed_offset,
            alpha=0.05,
            harm_margin=0.10,
            budget_rate=0.20,
            q_min=0.20,
            q_max=0.80,
            common_eprocess_bound=True,
            monitor_comparators=HARD_BUDGET_MONITOR_COMPARATORS,
            scenario_severity=severity,
            change_fraction=onset_fraction,
            device=resolved,
            scenario_subset=(scenario_name,),
            method_subset=("uniform_proxy",),
        ).validate()
        scenario = scenario_lookup[scenario_name]
        print(
            f"grid cell={cell_index}/{len(cells)} scenario={scenario_name} n={n} "
            f"severity={severity:g} onset_fraction={onset_fraction:g}",
            flush=True,
        )
        for replicate in range(seeds):
            seed = seed_offset + replicate
            common_uniforms = np.random.default_rng(seed + 9_173).random(n)
            for result in _generate_stream_rows(scenario, seed, config, common_uniforms):
                result.update(
                    {
                        "n": n,
                        "scenario_severity": severity,
                        "change_fraction": onset_fraction,
                    }
                )
                rows.append(result)
    metrics = pd.DataFrame(rows)
    forbidden = {"probability_positive", "oracle_probability", "expected_difference"}
    leaked = sorted(forbidden & set(metrics.columns))
    if leaked:
        raise RuntimeError(f"evaluator-only information leaked into metrics: {leaked}")
    if not metrics.budget_respected.astype(bool).all():
        raise RuntimeError("a power-grid cell violated its hard label-dollar cap")
    expected_rows = seeds * len(cells)
    if len(metrics) != expected_rows:
        raise RuntimeError(f"expected {expected_rows} stream rows, got {len(metrics)}")
    metrics.to_parquet(metrics_path, index=False)
    summary, paired = _summarize(metrics)
    summary_path = output / "metrics/harm_power_grid_summary.csv"
    paired_path = output / "metrics/harm_power_grid_paired_tests.csv"
    summary.to_csv(summary_path, index=False)
    paired.to_csv(paired_path, index=False)
    figure_path = output / "figures/harm_power_grid.png"
    _plot(summary, figure_path)

    report_lines = [
        "# Harm severity, onset, and horizon development grid",
        "",
        f"This paired CUDA development screen evaluates {len(cells)} parameter cells with {seeds} shared seed streams per cell ({len(metrics)} stream-cell observations). The common seed block is `{seed_offset}–{seed_offset + seeds - 1}`. Each monitor receives the same uniform-query labels, prediction-powered increments, q_min=.20 global bound, alpha=.05, epsilon=.10, and 20% realized dollar cap within a cell.",
        "",
        "Boundary-local harm varies DGP severity over 0.75, 1.50, 2.25; abrupt change fraction over .35, .50, .65; and stream horizon n over 2,400, 3,200, 4,000. Recurring regimes vary severity and horizon, while their built-in four-regime schedule is preserved; `change_fraction` is not presented as an onset control for recurrence.",
        "",
        "Each cell reports the fraction of all evaluator-classified material-harm streams detected, Wilson intervals, onset reachability, delay among detections, labels, spend, horizon, and cap compliance. A stream whose material-harm onset is not reached remains a nondetection in the all-harm denominator. Paired exact tests are exploratory and unadjusted across this screen; they do not select a confirmatory winner.",
        "",
        "No evaluator oracle probabilities enter model inputs or the exported stream metrics. The grid is intended to identify regions where the fixed-mixture result is robust and regions where the comparison changes. It is not a final test of error control or a novelty claim.",
        "",
        "## Reproduction",
        "",
        "Run `uv run python scripts/run_harm_power_grid.py --output outputs/harm_power_grid_30 --seeds 30 --seed-offset 54000000 --device cuda`. Use `metrics/harm_power_grid_summary.csv` for cell rates and `metrics/harm_power_grid_paired_tests.csv` only as exploratory contrasts.",
        "",
        "## Cell summaries",
        "",
        "|Scenario|n|Severity|Onset fraction|Monitor|Detect / material harm|Reach / material harm|Median delay|Mean labels|Mean spend / budget|",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        report_lines.append(
            f"|{row['scenario']}|{row['n']}|{row['scenario_severity']:.2f}|"
            f"{row['change_fraction']:.2f}|{row['monitor']}|"
            f"{row['harm_detections']}/{row['material_harm_streams']} "
            f"[{row['detection_wilson_95_low']:.2f}, {row['detection_wilson_95_high']:.2f}]|"
            f"{row['harm_onsets_reached']}/{row['material_harm_streams']}|"
            f"{row['median_delay_given_detection']:.1f}|{row['mean_labels']:.1f}|"
            f"{row['mean_spend']:.1f}/{row['mean_budget']:.1f}|"
        )
    report_path = output / "reports/harm_power_grid.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest_path = output / "reports/manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "experiment": "paired_harm_severity_onset_horizon_grid",
                "configuration": {
                    "seeds_per_cell": seeds,
                    "seed_offset": seed_offset,
                    "cells": len(cells),
                    "scenario_subset": list(SCENARIOS),
                    "severities": list(SEVERITIES),
                    "boundary_onset_fractions": list(ONSET_FRACTIONS),
                    "horizons": list(HORIZONS),
                    "alpha": 0.05,
                    "harm_margin": 0.10,
                    "budget_rate": 0.20,
                    "q_min": 0.20,
                    "q_max": 0.80,
                    "device": device,
                    "resolved_device": resolved,
                    "monitor_comparators": list(HARD_BUDGET_MONITOR_COMPARATORS),
                },
                "environment": environment(),
                "source_git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "source_worktree_clean": not subprocess.check_output(
                    ["git", "status", "--porcelain"], cwd=ROOT, text=True
                ).strip(),
                "analysis_script_sha256": _sha256(Path(__file__).resolve()),
                "artifacts": {},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    finalize_manifest(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sha256"]["grid_script"] = _sha256(Path(__file__).resolve())
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {report_path.relative_to(ROOT).as_posix()}", flush=True)
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-offset", type=int, default=54000000)
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cuda")
    args = parser.parse_args()
    run_grid(args.output, seeds=args.seeds, seed_offset=args.seed_offset, device=args.device)


if __name__ == "__main__":
    main()
