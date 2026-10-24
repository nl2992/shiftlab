"""Paired seed-level comparison of hard-budget minimum-propensity floors."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.dive.experiment import finalize_manifest

KEYS = ["scenario", "method", "seed"]


def compare(baseline_run: Path, higher_floor_run: Path) -> Path:
    def read_run(run: Path, floor_label: str) -> pd.DataFrame:
        metrics = pd.read_parquet(run / "metrics" / "hard_budget_comparison.parquet")
        diagnostics = pd.read_csv(run / "analysis" / "seed_diagnostics.csv")
        merged = metrics.merge(diagnostics, on=KEYS, validate="one_to_one")
        merged["floor_setting"] = floor_label
        return merged

    low = read_run(baseline_run, "q_min=0.10")
    high = read_run(higher_floor_run, "q_min=0.20")
    paired = low.merge(high, on=KEYS, suffixes=("_q010", "_q020"), validate="one_to_one")
    if len(paired) != len(high) or set(map(tuple, paired[KEYS].to_numpy())) != set(
        map(tuple, high[KEYS].to_numpy())
    ):
        raise ValueError("higher-floor streams are not all present in the baseline seed block")
    if paired.eprocess_minimum_propensity_q010.nunique() != 1 or not np.isclose(
        paired.eprocess_minimum_propensity_q010.iloc[0], 0.10
    ):
        raise ValueError("baseline run does not use a 0.10 e-process minimum propensity")
    if paired.eprocess_minimum_propensity_q020.nunique() != 1 or not np.isclose(
        paired.eprocess_minimum_propensity_q020.iloc[0], 0.20
    ):
        raise ValueError("higher-floor run does not use a 0.20 e-process minimum propensity")
    trace_columns = [
        "event_offset",
        "stream_index",
        "propensity",
        "queried",
        "learner_observed_excess_cost",
        "proxy_prediction",
        "ppi_increment",
        "evaluator_full_feedback_increment",
    ]
    low_trace = pd.read_parquet(baseline_run / "metrics" / "event_traces.parquet")
    high_trace = pd.read_parquet(higher_floor_run / "metrics" / "event_traces.parquet")
    uniform_trace_equal: dict[tuple[object, ...], bool] = {}
    for key in high.loc[high.method.eq("uniform_proxy"), KEYS].itertuples(index=False, name=None):
        low_events = low_trace.loc[
            low_trace.scenario.eq(key[0]) & low_trace.method.eq(key[1]) & low_trace.seed.eq(key[2]),
            trace_columns,
        ].reset_index(drop=True)
        high_events = high_trace.loc[
            high_trace.scenario.eq(key[0])
            & high_trace.method.eq(key[1])
            & high_trace.seed.eq(key[2]),
            trace_columns,
        ].reset_index(drop=True)
        uniform_trace_equal[key] = low_events.equals(high_events)

    rows = []
    for (scenario, method), group in paired.groupby(KEYS[:2], sort=True):
        harmful = scenario == "boundary_local_harm"
        discordant_020 = int((group.single_e_detected_q020 & ~group.single_e_detected_q010).sum())
        discordant_010 = int((group.single_e_detected_q010 & ~group.single_e_detected_q020).sum())
        rows.append(
            {
                "scenario": scenario,
                "method": method,
                "paired_streams": len(group),
                "q_min_010_bound": float(group.eprocess_minimum_propensity_q010.iloc[0]),
                "q_min_020_bound": float(group.eprocess_minimum_propensity_q020.iloc[0]),
                "q_min_010_actual_query_min": float(group.query_propensity_min_q010.mean()),
                "q_min_020_actual_query_min": float(group.query_propensity_min_q020.mean()),
                "q_min_010_detected": int(group.single_e_detected_q010.sum()),
                "q_min_020_detected": int(group.single_e_detected_q020.sum()),
                "policy_bound_q010_detected": int(group.policy_bound_any_crossing_q010.sum()),
                "policy_bound_q020_detected": int(group.policy_bound_any_crossing_q020.sum()),
                "policy_variance_q010_detected": int(group.policy_variance_any_crossing_q010.sum()),
                "policy_variance_q020_detected": int(group.policy_variance_any_crossing_q020.sum()),
                "policy_pm_eb_q010_detected": int(group.policy_pm_eb_any_crossing_q010.sum()),
                "policy_pm_eb_q020_detected": int(group.policy_pm_eb_any_crossing_q020.sum()),
                "q_min_010_reached_harm": int(group.harm_reached_before_budget_stop_q010.sum())
                if harmful
                else np.nan,
                "q_min_020_reached_harm": int(group.harm_reached_before_budget_stop_q020.sum())
                if harmful
                else np.nan,
                "q_min_010_false_escalations": int(group.single_e_false_escalation_q010.sum())
                if not harmful
                else np.nan,
                "q_min_020_false_escalations": int(group.single_e_false_escalation_q020.sum())
                if not harmful
                else np.nan,
                "q_min_010_mean_budget": float(group.hard_budget_q010.mean()),
                "q_min_020_mean_budget": float(group.hard_budget_q020.mean()),
                "q_min_010_mean_spend": float(group.realized_label_spend_q010.mean()),
                "q_min_020_mean_spend": float(group.realized_label_spend_q020.mean()),
                "q_min_010_mean_labels": float(group.labels_queried_q010.mean()),
                "q_min_020_mean_labels": float(group.labels_queried_q020.mean()),
                "q_min_010_mean_events": float(group.processed_events_q010.mean()),
                "q_min_020_mean_events": float(group.processed_events_q020.mean()),
                "q_min_010_mean_stream_rmse": float(group.stream_mean_estimation_rmse_q010.mean()),
                "q_min_020_mean_stream_rmse": float(group.stream_mean_estimation_rmse_q020.mean()),
                "q_min_010_mean_ppi_variance": float(group.ppi_increment_variance_q010.mean()),
                "q_min_020_mean_ppi_variance": float(group.ppi_increment_variance_q020.mean()),
                "q_min_010_mean_bound": float(group.ppi_support_bound_q010.mean()),
                "q_min_020_mean_bound": float(group.ppi_support_bound_q020.mean()),
                "detection_discordant_q020_only": discordant_020,
                "detection_discordant_q010_only": discordant_010,
                "uniform_potential_outcome_path_identical": (
                    all(uniform_trace_equal[(scenario, method, int(seed))] for seed in group.seed)
                    if method == "uniform_proxy"
                    else np.nan
                ),
            }
        )
    summary = pd.DataFrame(rows)
    analysis_dir = higher_floor_run / "analysis"
    reports_dir = higher_floor_run / "reports"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path = analysis_dir / "propensity_floor_paired_comparison.csv"
    summary.to_csv(summary_path, index=False)

    lines = [
        "# Minimum-propensity floor diagnostic",
        "",
        "This same-seed comparison reuses the first 30 streams from the 60-seed `q_min=0.10` run and compares them with a `q_min=0.20` run under the same 20% dollar budget. It is descriptive, not an independent confirmation or a calibration study. The floor changes the e-process support bound and can change both propensities and the budget stopping horizon.",
        "",
        "For uniform paths, the script verifies event-by-event equality of propensities, query indicators, observed labels, proxy predictions, PPI increments, and evaluator outcomes. The realized query floor is 0.20 in both runs. Thus the uniform crossing difference under the original common bounds isolates the support-bound setting: the `q_min=0.10` run used 96.9 despite uniform querying never falling below 0.20, while the second used 45.9. The CSV also reports fixed-mixture, predictable-variance, and plug-in empirical-Bernstein replays using each policy's registered support bound. For uniform, that policy-specific bound is 45.9 in both runs, so the correctly matched replay should be identical event by event.",
        "",
        "|Scenario|Method|Streams|Common-bound detections q=.10 / .20|Policy-bound fixed-mixture detections q=.10 / .20|Policy-bound PVA detections q=.10 / .20|Policy-bound PM-EB detections q=.10 / .20|Reached harm q=.10 / .20|Mean events q=.10 / .20|Mean labels q=.10 / .20|Mean spend q=.10 / .20|PPI variance q=.10 / .20|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        reached = (
            f"{int(row['q_min_010_reached_harm'])}/{int(row['q_min_020_reached_harm'])}"
            if np.isfinite(row["q_min_010_reached_harm"])
            else "n/a"
        )
        lines.append(
            f"|{row['scenario']}|{row['method']}|{int(row['paired_streams'])}|{int(row['q_min_010_detected'])}/{int(row['paired_streams'])} / {int(row['q_min_020_detected'])}/{int(row['paired_streams'])}|{int(row['policy_bound_q010_detected'])}/{int(row['paired_streams'])} / {int(row['policy_bound_q020_detected'])}/{int(row['paired_streams'])}|{int(row['policy_variance_q010_detected'])}/{int(row['paired_streams'])} / {int(row['policy_variance_q020_detected'])}/{int(row['paired_streams'])}|{int(row['policy_pm_eb_q010_detected'])}/{int(row['paired_streams'])} / {int(row['policy_pm_eb_q020_detected'])}/{int(row['paired_streams'])}|{reached}|{row['q_min_010_mean_events']:.0f} / {row['q_min_020_mean_events']:.0f}|{row['q_min_010_mean_labels']:.1f} / {row['q_min_020_mean_labels']:.1f}|{row['q_min_010_mean_spend']:.1f} / {row['q_min_020_mean_spend']:.1f}|{row['q_min_010_mean_ppi_variance']:.3f} / {row['q_min_020_mean_ppi_variance']:.3f}|"
        )
    lines.extend(
        [
            "",
            "Detection discordances are recorded in the CSV for paired inspection. Because seeds are reused from the development comparison, do not treat paired p-values or rates here as confirmatory and do not promote a floor setting from this diagnostic. Null false-escalation counts are similarly diagnostic only.",
            "",
            "No figure was generated. PaperBanana remains the project preference for future research visuals.",
            "",
        ]
    )
    report_path = reports_dir / "propensity_floor_comparison.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    finalize_manifest(higher_floor_run)
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline_run", type=Path)
    parser.add_argument("higher_floor_run", type=Path)
    args = parser.parse_args()
    print(compare(args.baseline_run, args.higher_floor_run))


if __name__ == "__main__":
    main()
