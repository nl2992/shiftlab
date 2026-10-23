"""Create a seed-clustered comparison of bounded-mean betting mixtures."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

HARM_SCENARIOS = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
MONITOR_COLUMNS = {
    "multiscale_e_detected": "Broad multiscale",
    "protected_e_detected": "Protected multiscale",
}


def _cluster_summary(
    metrics: pd.DataFrame,
    candidate_column: str,
    *,
    seed: int = 7731,
    bootstrap_replicates: int = 20_000,
) -> tuple[dict[str, float | int], pd.DataFrame, pd.DataFrame]:
    required = {
        "scenario",
        "seed",
        "method",
        "material_harm",
        "harm_reached_before_budget_stop",
        "single_e_detected",
        candidate_column,
    }
    missing = required - set(metrics.columns)
    if missing:
        raise ValueError(f"metrics are missing required columns: {sorted(missing)}")
    frame = metrics.loc[metrics.scenario.isin(HARM_SCENARIOS) & metrics.material_harm].copy()
    if frame.empty:
        raise ValueError("no evaluator-labeled harmful streams found in the locked scenarios")
    if frame.duplicated(["scenario", "seed", "method"]).any():
        raise ValueError("expected one metric row per scenario, seed, and query policy")

    frame["fixed"] = frame.single_e_detected.astype(bool)
    frame["candidate"] = frame[candidate_column].astype(bool)
    frame["candidate_minus_fixed"] = frame.candidate.astype(int) - frame.fixed.astype(int)
    frame["candidate_only"] = frame.candidate & ~frame.fixed
    frame["fixed_only"] = frame.fixed & ~frame.candidate
    per_cell = (
        frame.groupby(["scenario", "method"], sort=True)
        .agg(
            harmful_streams=("seed", "size"),
            reached_streams=("harm_reached_before_budget_stop", "sum"),
            fixed_detections=("fixed", "sum"),
            candidate_detections=("candidate", "sum"),
            candidate_only=("candidate_only", "sum"),
            fixed_only=("fixed_only", "sum"),
        )
        .reset_index()
    )

    by_seed = frame.groupby("seed", sort=True).candidate_minus_fixed.agg(["mean", "size"])
    if by_seed["size"].nunique() != 1:
        raise ValueError("seed clusters have unequal numbers of scenario-policy rows")
    n_cells_per_seed = int(by_seed["size"].iloc[0])
    if n_cells_per_seed != len(HARM_SCENARIOS) * metrics.method.nunique():
        raise ValueError("harmful comparison is missing scenario-policy cells within seed clusters")
    seed_effect = by_seed["mean"].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(seed_effect), size=(bootstrap_replicates, len(seed_effect)))
    bootstrap = seed_effect[draws].mean(axis=1)
    summary = {
        "seeds": len(seed_effect),
        "scenario_policy_rows": len(frame),
        "scenario_policy_cells_per_seed": n_cells_per_seed,
        "fixed_detections": int(frame.fixed.sum()),
        "candidate_detections": int(frame.candidate.sum()),
        "candidate_only": int(frame.candidate_only.sum()),
        "fixed_only": int(frame.fixed_only.sum()),
        "detection_difference": float(seed_effect.mean()),
        "ci_low": float(np.quantile(bootstrap, 0.025)),
        "ci_high": float(np.quantile(bootstrap, 0.975)),
        "onsets_reached": int(frame.harm_reached_before_budget_stop.sum()),
        "harmful_rows": len(frame),
    }
    by_scenario = (
        frame.groupby("scenario", sort=True)
        .agg(
            harmful_rows=("seed", "size"),
            fixed_detections=("fixed", "sum"),
            candidate_detections=("candidate", "sum"),
            candidate_only=("candidate_only", "sum"),
            fixed_only=("fixed_only", "sum"),
            onsets_reached=("harm_reached_before_budget_stop", "sum"),
        )
        .reset_index()
    )
    return summary, per_cell, by_scenario


def _render_report(metrics: pd.DataFrame, candidate_column: str) -> str:
    candidate_name = MONITOR_COLUMNS[candidate_column]
    summary, per_cell, by_scenario = _cluster_summary(metrics, candidate_column)
    fixed_rate = summary["fixed_detections"] / summary["harmful_rows"]
    candidate_rate = summary["candidate_detections"] / summary["harmful_rows"]
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    lines = [
        "# Betting-mixture paired analysis",
        "",
        f"Candidate: **{candidate_name}**; comparator: the fixed five-stake mixture.",
        "",
        f"Across {summary['seeds']} independent seed clusters and {summary['scenario_policy_rows']} evaluator-harm scenario-policy rows, the fixed mixture detected {summary['fixed_detections']} ({fixed_rate:.3%}) and the candidate detected {summary['candidate_detections']} ({candidate_rate:.3%}). The paired candidate-minus-fixed difference was {summary['detection_difference']:.3%} (95% percentile bootstrap interval [{summary['ci_low']:.3%}, {summary['ci_high']:.3%}]), resampling whole seeds across all {summary['scenario_policy_cells_per_seed']} scenario-policy cells.",
        "",
        f"Discordant outcomes: candidate-only {summary['candidate_only']}; fixed-only {summary['fixed_only']}. Harm onsets were reached in {summary['onsets_reached']}/{summary['harmful_rows']} evaluator-harm rows.",
        "",
        "The interval is descriptive for this predeclared synthetic block. It is not adjusted for any follow-on selection, and does not establish power or a general ordering.",
        "",
        "## By scenario",
        "",
        "|Scenario|Rows|Fixed detections|Candidate detections|Candidate-only|Fixed-only|Onsets reached|",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in by_scenario.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['harmful_rows']}|{row['fixed_detections']}|{row['candidate_detections']}|{row['candidate_only']}|{row['fixed_only']}|{row['onsets_reached']}|"
        )
    lines.extend(
        [
            "",
            "## By scenario and query policy",
            "",
            "|Scenario|Policy|Rows|Fixed detections|Candidate detections|Candidate-only|Fixed-only|Onsets reached|",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in per_cell.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['method']}|{row['harmful_streams']}|{row['fixed_detections']}|{row['candidate_detections']}|{row['candidate_only']}|{row['fixed_only']}|{row['reached_streams']}|"
        )

    controls = metrics.loc[metrics.scenario.isin(["stationary", "benign_nuisance"])].copy()
    lines.extend(
        [
            "",
            "## Controls and budget audit",
            "",
            "|Scenario|Policy|Rows|Fixed any alarms|Candidate any alarms|Pathwise oracle materiality flags|Population-null harm onsets|Budget violations|",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    if not controls.empty:
        candidate_alarm_column = candidate_column.replace("_detected", "_alarm_time")
        for (scenario, method), group in controls.groupby(["scenario", "method"], sort=True):
            lines.append(
                f"|{scenario}|{method}|{len(group)}|{group.single_e_alarm_time.notna().sum()}|{group[candidate_alarm_column].notna().sum()}|{group.get('sample_path_material_harm', group.material_harm).sum()}|{group.loc[~group.scenario.isin(['stationary', 'benign_nuisance']), 'harm_reached_before_budget_stop'].sum()}|{(~group.budget_respected).sum()}|"
            )
    else:
        lines.append("|No control scenarios|n/a|0|n/a|n/a|n/a|n/a|n/a|")
    if "budget_respected" in metrics:
        lines.extend(
            [
                "",
                f"Across all {len(metrics)} rows, budget violations: {(~metrics.budget_respected).sum()}.",
            ]
        )
    lines.extend(
        [
            "",
            "## Reproduction",
            "",
            (
                "Run `uv run python scripts/analyze_betting_mixture.py --input "
                "<run>/metrics/hard_budget_comparison.parquet --candidate-column "
                f"{candidate_column}`. Bootstrap seed: `7731`; replicates: `20000`."
            ),
            "",
            f"Analysis script SHA-256: `{script_hash}`.",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--candidate-column", choices=tuple(MONITOR_COLUMNS), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    metrics = pd.read_parquet(args.input)
    output = args.output or args.input.parent.parent / "reports" / "stake_mixture_analysis.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_render_report(metrics, args.candidate_column), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
