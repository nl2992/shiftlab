"""Independent null calibration and confirmation for contextual stratification."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from scipy.stats import beta

from .contextual_stratified_intervention import SCENARIOS, run_grid

ALPHA_FAMILY = 0.05
N_CALIBRATION_CELLS = 8
CALIBRATION_OFFSET = 90_102_024
CONFIRMATION_OFFSET = 91_102_024
DEVELOPMENT_OFFSET = 80_102_024
SCENARIO_SEED_STRIDE = 107_003
DEVELOPMENT_SEEDS = 500
QUERY_RATE = 0.80
BUDGET_RATE = 0.40
HORIZON = 400


def _cp_upper(events: int, trials: int, alpha: float) -> float:
    if trials <= 0 or not 0 <= events <= trials:
        raise ValueError("Clopper-Pearson inputs require 0 <= events <= trials and trials > 0")
    if events == trials:
        return 1.0
    return float(beta.ppf(1 - alpha, events + 1, trials - events))


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_calibration(
    output_dir: str | Path,
    *,
    seeds: int = 2_000,
    seed_offset: int = CALIBRATION_OFFSET,
    horizon: int = HORIZON,
    device: str = "cuda",
    bootstrap_replicates: int = 2_000,
) -> tuple[pd.DataFrame, dict]:
    """Evaluate eight simultaneous one-sided exact-binomial null cells."""
    last_development_seed = (
        DEVELOPMENT_OFFSET + (len(SCENARIOS) - 1) * SCENARIO_SEED_STRIDE + DEVELOPMENT_SEEDS - 1
    )
    if seed_offset <= last_development_seed:
        raise ValueError("calibration seed block must follow and be disjoint from development")
    output = Path(output_dir)
    grid, _, grid_manifest = run_grid(
        output / "grid",
        seeds=seeds,
        seed_offset=seed_offset,
        horizon=horizon,
        query_rates=(QUERY_RATE,),
        budget_rates=(BUDGET_RATE,),
        device=device,
        bootstrap_replicates=bootstrap_replicates,
    )
    cells: list[tuple[str, str, str, str]] = []
    for scenario in ("stationary_null", "benign_nuisance"):
        for method in ("promotion_rollback", "stratified_promotion_rollback"):
            cells.append((scenario, method, "false_promotion_under_null", "all"))
    cells.extend(
        [
            (
                "rollback_boundary_global",
                "promotion_rollback",
                "false_rollback_under_null",
                "promoted",
            ),
            (
                "rollback_boundary_stratified",
                "stratified_promotion_rollback",
                "false_rollback_under_null",
                "promoted",
            ),
            ("persistent_benefit", "promotion_rollback", "false_rollback_under_null", "promoted"),
            (
                "persistent_benefit",
                "stratified_promotion_rollback",
                "false_rollback_under_null",
                "promoted",
            ),
        ]
    )
    rows = []
    cell_alpha = ALPHA_FAMILY / N_CALIBRATION_CELLS
    for scenario, method, event_column, risk_set in cells:
        selected = grid.loc[grid.scenario.eq(scenario) & grid.method.eq(method)]
        if risk_set == "promoted":
            selected = selected.loc[selected.promoted]
        trials = len(selected)
        events = int(selected[event_column].sum())
        upper = _cp_upper(events, trials, cell_alpha) if trials else 1.0
        rows.append(
            {
                "scenario": scenario,
                "method": method,
                "event": event_column,
                "risk_set": risk_set,
                "events": events,
                "trials": trials,
                "simultaneous_one_sided_alpha": cell_alpha,
                "clopper_pearson_upper": upper,
                "cell_pass": trials >= 1_000 and upper <= ALPHA_FAMILY,
            }
        )
    table = pd.DataFrame(rows)
    passed = bool(table.cell_pass.all() and grid_manifest["all_label_caps_respected"])
    table.to_csv(output / "calibration.csv", index=False)
    source = Path(__file__)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed" if passed else "failed",
        "purpose": "independent simultaneous one-sided exact-binomial calibration for global and stratified promotion/rollback rules",
        "seed_offset": seed_offset,
        "seeds_per_scenario": seeds,
        "development_seed_offset": DEVELOPMENT_OFFSET,
        "query_rate": QUERY_RATE,
        "budget_rate": BUDGET_RATE,
        "horizon_per_phase": horizon,
        "familywise_alpha": ALPHA_FAMILY,
        "simultaneous_cells": N_CALIBRATION_CELLS,
        "all_cells_pass": bool(table.cell_pass.all()),
        "all_label_caps_respected": grid_manifest["all_label_caps_respected"],
        "grid_metrics_sha256": grid_manifest["metrics_sha256"],
        "calibration_sha256": _source_hash(output / "calibration.csv"),
        "code_sha256": _source_hash(source),
        "limitation": "Calibration applies only to the registered bounded synthetic nulls, fixed policies, query mechanism, horizon, costs, and alpha allocation.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Contextual stratification null calibration",
        "",
        f"Status: **{manifest['status']}**; {seeds} independent streams per scenario; seed root {seed_offset}; device {device}.",
        "",
        "The eight prespecified cells cover familywise false promotion under two nulls for both methods, false rollback at each method's own least-favourable boundary, and false rollback under persistent benefit. Rollback rates use promoted streams as the risk set. Each cell receives one-sided Clopper–Pearson alpha 0.05/8; passing requires at least 1,000 at-risk streams and upper bound at most 0.05.",
        "",
        table.to_markdown(index=False, floatfmt=".5f"),
        "",
        "This is a finite registered synthetic calibration, not a general theorem beyond the gate's stated bounded-mean assumptions and this data-generating process.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return table, manifest


def run_confirmation(
    output_dir: str | Path,
    calibration_manifest: str | Path,
    *,
    seeds: int = 2_000,
    seed_offset: int = CONFIRMATION_OFFSET,
    horizon: int = HORIZON,
    device: str = "cuda",
    bootstrap_replicates: int = 5_000,
) -> tuple[pd.DataFrame, dict]:
    """Run a frozen heterogeneous-reversal confirmation on fresh streams."""
    calibration = json.loads(Path(calibration_manifest).read_text(encoding="utf-8"))
    if calibration.get("status") != "passed":
        raise ValueError("confirmation requires a passed independent calibration manifest")
    if (
        seed_offset < CONFIRMATION_OFFSET
        or horizon != int(calibration["horizon_per_phase"])
        or QUERY_RATE != float(calibration["query_rate"])
        or BUDGET_RATE != float(calibration["budget_rate"])
    ):
        raise ValueError("confirmation must match the calibrated horizon, query rate, and budget")
    last_calibration_seed = (
        int(calibration["seed_offset"])
        + (len(SCENARIOS) - 1) * SCENARIO_SEED_STRIDE
        + int(calibration["seeds_per_scenario"])
        - 1
    )
    if seed_offset <= last_calibration_seed:
        raise ValueError("confirmation seed block must follow and be disjoint from calibration")
    output = Path(output_dir)
    metrics, contrasts, grid_manifest = run_grid(
        output / "grid",
        seeds=seeds,
        seed_offset=seed_offset,
        horizon=horizon,
        query_rates=(QUERY_RATE,),
        budget_rates=(BUDGET_RATE,),
        device=device,
        bootstrap_replicates=bootstrap_replicates,
    )
    hetero = metrics.loc[
        metrics.scenario.eq("heterogeneous_reversal")
        & metrics.query_rate.eq(QUERY_RATE)
        & metrics.budget_rate.eq(BUDGET_RATE)
    ]
    strat = hetero.loc[hetero.method.eq("stratified_promotion_rollback")]
    by_contrast = contrasts.loc[
        contrasts.scenario.eq("heterogeneous_reversal")
        & contrasts.query_rate.eq(QUERY_RATE)
        & contrasts.budget_rate.eq(BUDGET_RATE)
        & contrasts.method.eq("stratified_promotion_rollback")
    ].set_index("reference")
    conditions = {
        "stratified_beats_global_lower_ci_positive": bool(
            by_contrast.loc["promotion_rollback", "seed_bootstrap_ci95_low"] > 0
        ),
        "stratified_beats_continue_lower_ci_positive": bool(
            by_contrast.loc["continue", "seed_bootstrap_ci95_low"] > 0
        ),
        "mean_harmful_groups_rolled_back_at_least_half": bool(
            strat.harmful_groups_rolled_back.mean() >= 0.5
        ),
        "mean_safe_groups_retained_above_90_percent": bool(strat.safe_groups_retained.mean() > 0.9),
        "all_label_caps_respected": bool(grid_manifest["all_label_caps_respected"]),
    }
    passed = all(conditions.values())
    report_rows = []
    for reference in ("promotion_rollback", "continue"):
        row = by_contrast.loc[reference]
        report_rows.append(
            {
                "comparison": f"stratified - {reference}",
                "paired_mean": row.paired_mean_realized_utility_difference,
                "ci95_low": row.seed_bootstrap_ci95_low,
                "ci95_high": row.seed_bootstrap_ci95_high,
            }
        )
    table = pd.DataFrame(report_rows)
    table.to_csv(output / "confirmation_contrasts.csv", index=False)
    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "status": "passed" if passed else "criteria_not_met",
        "purpose": "independent frozen-seed confirmation of context-local rollback in heterogeneous reversal",
        "seed_offset": seed_offset,
        "seeds_per_scenario": seeds,
        "calibration_manifest": str(Path(calibration_manifest)),
        "calibration_status": calibration["status"],
        "query_rate": QUERY_RATE,
        "budget_rate": BUDGET_RATE,
        "horizon_per_phase": horizon,
        "criteria": conditions,
        "mean_harmful_groups_rolled_back": float(strat.harmful_groups_rolled_back.mean()),
        "mean_safe_groups_retained": float(strat.safe_groups_retained.mean()),
        "all_label_caps_respected": grid_manifest["all_label_caps_respected"],
        "grid_metrics_sha256": grid_manifest["metrics_sha256"],
        "contrast_sha256": _source_hash(output / "confirmation_contrasts.csv"),
        "bootstrap_replicates": bootstrap_replicates,
        "interpretation_limit": "One synthetic heterogeneous-reversal confirmation; it does not establish general superiority or algorithmic novelty.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    report = [
        "# Contextual stratification independent confirmation",
        "",
        f"Status: **{manifest['status']}**; {seeds} independent streams per scenario; seed root {seed_offset}; device {device}.",
        "",
        "The primary profile and criteria were fixed after the development screen: heterogeneous reversal, 80% query rate, 40% of the total two-phase stream as the hard label cap, paired 95% seed-bootstrap lower bounds above zero against both the global gate and continue, at least 0.5 harmful-group rollbacks per stream, more than 0.9 safe groups retained per stream, and no cap violations.",
        "",
        table.to_markdown(index=False, floatfmt=".4f"),
        "",
        f"Mean harmful groups rolled back per stream: {manifest['mean_harmful_groups_rolled_back']:.4f}. Mean safe groups retained: {manifest['mean_safe_groups_retained']:.4f}.",
        "",
        "These criteria assess this registered synthetic case only. The procedures use standard Bonferroni composition of the existing gate; no novelty claim follows.",
    ]
    (output / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return table, manifest


def main_calibration() -> None:
    parser = argparse.ArgumentParser(description="Calibrate contextual stratified gates")
    parser.add_argument("--seeds", type=int, default=2_000)
    parser.add_argument("--seed-offset", type=int, default=CALIBRATION_OFFSET)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/contextual_stratified_calibration")
    )
    args = parser.parse_args()
    _, manifest = run_calibration(
        args.output_dir,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        device=args.device,
    )
    print(json.dumps(manifest, indent=2))


def main_confirmation() -> None:
    parser = argparse.ArgumentParser(description="Confirm contextual stratified gates")
    parser.add_argument(
        "--calibration-manifest",
        type=Path,
        default=Path("outputs/contextual_stratified_calibration/manifest.json"),
    )
    parser.add_argument("--seeds", type=int, default=2_000)
    parser.add_argument("--seed-offset", type=int, default=CONFIRMATION_OFFSET)
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/contextual_stratified_confirmation")
    )
    args = parser.parse_args()
    _, manifest = run_confirmation(
        args.output_dir,
        args.calibration_manifest,
        seeds=args.seeds,
        seed_offset=args.seed_offset,
        horizon=args.horizon,
        device=args.device,
    )
    print(json.dumps(manifest, indent=2))
