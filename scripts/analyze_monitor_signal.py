"""Summarize descriptive learner/evaluator traces from a hard-budget run."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.dive.experiment import finalize_manifest

KEYS = ["scenario", "method", "seed"]


def analyze(trace_path: Path, output_dir: Path) -> tuple[Path, Path, Path]:
    trace = pd.read_parquet(trace_path)
    required = {
        *KEYS,
        "event_offset",
        "queried",
        "learner_observed_excess_cost",
        "ppi_increment",
        "learner_log_e",
        "evaluator_expected_excess_cost",
        "evaluator_expected_paired_cost_difference",
        "evaluator_harm_margin",
        "evaluator_full_feedback_increment",
        "evaluator_full_feedback_log_e",
        "evaluator_harm_onset_event",
        "evaluator_threshold_log",
    }
    missing = required - set(trace.columns)
    if missing:
        raise ValueError(f"event trace is missing required columns: {sorted(missing)}")
    if trace.loc[~trace.queried, "learner_observed_excess_cost"].notna().any():
        raise ValueError("trace contains an observed outcome for an unqueried event")
    expected_centered = (
        trace.evaluator_expected_paired_cost_difference - trace.evaluator_harm_margin
    )
    if not np.allclose(
        expected_centered,
        trace.evaluator_expected_excess_cost,
        rtol=0,
        atol=1e-12,
    ):
        raise ValueError("evaluator expected excess costs are not correctly centered by epsilon")

    seed_rows: list[dict[str, object]] = []
    snapshots: list[dict[str, object]] = []
    for key, group in trace.groupby(KEYS, sort=True):
        group = group.sort_values("event_offset")
        onset_values = group.evaluator_harm_onset_event.dropna().unique()
        onset = int(onset_values[0]) if len(onset_values) else None
        threshold = float(group.evaluator_threshold_log.iloc[0])
        expected = group.evaluator_expected_excess_cost.to_numpy(dtype=float)
        ppi = group.ppi_increment.to_numpy(dtype=float)
        full_feedback = group.evaluator_full_feedback_increment.to_numpy(dtype=float)
        actual_log = group.learner_log_e.to_numpy(dtype=float)
        oracle_log = group.evaluator_full_feedback_log_e.to_numpy(dtype=float)
        offsets = group.event_offset.to_numpy(dtype=int)
        actual_crossings = np.flatnonzero(actual_log >= threshold)
        oracle_crossings = np.flatnonzero(oracle_log >= threshold)
        actual_first = int(offsets[actual_crossings[0]]) if len(actual_crossings) else None
        oracle_first = int(offsets[oracle_crossings[0]]) if len(oracle_crossings) else None
        actual_post = actual_first is not None and (onset is None or actual_first >= onset)
        oracle_post = oracle_first is not None and (onset is None or oracle_first >= onset)
        after_onset = offsets >= onset if onset is not None else np.zeros(len(offsets), dtype=bool)
        seed_rows.append(
            {
                "scenario": key[0],
                "method": key[1],
                "seed": key[2],
                "events_processed": len(group),
                "query_rate_realized": float(group.queried.mean()),
                "expected_excess_cost_mean": float(expected.mean()),
                "expected_excess_cost_sd": float(expected.std(ddof=1))
                if len(expected) > 1
                else 0.0,
                "fraction_expected_harm_positive": float(np.mean(expected > 0)),
                "post_onset_expected_excess_cost_mean": float(expected[after_onset].mean())
                if after_onset.any()
                else np.nan,
                "ppi_increment_mean": float(ppi.mean()),
                "ppi_increment_variance": float(ppi.var(ddof=1)) if len(ppi) > 1 else 0.0,
                "full_feedback_increment_mean": float(full_feedback.mean()),
                "full_feedback_increment_variance": float(full_feedback.var(ddof=1))
                if len(full_feedback) > 1
                else 0.0,
                "learner_final_log_e": float(actual_log[-1]),
                "learner_max_log_e": float(actual_log.max()),
                "evaluator_final_log_e": float(oracle_log[-1]),
                "evaluator_max_log_e": float(oracle_log.max()),
                "learner_any_crossing": bool(actual_first is not None),
                "evaluator_any_crossing": bool(oracle_first is not None),
                "learner_post_onset_crossing": bool(actual_post),
                "evaluator_post_onset_crossing": bool(oracle_post),
                "learner_crossing_event": actual_first,
                "evaluator_crossing_event": oracle_first,
                "harm_onset_event_evaluator_only": onset,
                "learner_detection_delay": actual_first - onset
                if actual_post and onset is not None
                else np.nan,
                "evaluator_detection_delay": oracle_first - onset
                if oracle_post and onset is not None
                else np.nan,
                "threshold_log_e": threshold,
            }
        )
        for fraction in (0.25, 0.50, 0.75, 1.0):
            index = min(len(group) - 1, max(0, int(np.ceil(fraction * len(group))) - 1))
            snapshots.append(
                {
                    "scenario": key[0],
                    "method": key[1],
                    "seed": key[2],
                    "horizon_fraction": fraction,
                    "event_offset": int(offsets[index]),
                    "learner_log_e": float(actual_log[index]),
                    "evaluator_full_feedback_log_e": float(oracle_log[index]),
                }
            )

    seed_metrics = pd.DataFrame(seed_rows)
    grouped = (
        seed_metrics.groupby(["scenario", "method"], sort=True)
        .agg(
            streams=("seed", "size"),
            mean_expected_excess_cost=("expected_excess_cost_mean", "mean"),
            mean_fraction_expected_harm_positive=("fraction_expected_harm_positive", "mean"),
            mean_post_onset_excess_cost=("post_onset_expected_excess_cost_mean", "mean"),
            mean_ppi_increment=("ppi_increment_mean", "mean"),
            mean_ppi_increment_variance=("ppi_increment_variance", "mean"),
            mean_full_feedback_increment=("full_feedback_increment_mean", "mean"),
            mean_full_feedback_increment_variance=("full_feedback_increment_variance", "mean"),
            learner_crossing_rate=("learner_any_crossing", "mean"),
            evaluator_crossing_rate=("evaluator_any_crossing", "mean"),
            learner_post_onset_crossing_rate=("learner_post_onset_crossing", "mean"),
            evaluator_post_onset_crossing_rate=("evaluator_post_onset_crossing", "mean"),
            learner_final_log_e_mean=("learner_final_log_e", "mean"),
            evaluator_final_log_e_mean=("evaluator_final_log_e", "mean"),
            learner_detection_delay_mean=("learner_detection_delay", "mean"),
            evaluator_detection_delay_mean=("evaluator_detection_delay", "mean"),
        )
        .reset_index()
    )
    snapshot_summary = (
        pd.DataFrame(snapshots)
        .groupby(["scenario", "method", "horizon_fraction"], sort=True)
        .agg(
            streams=("seed", "size"),
            learner_log_e_mean=("learner_log_e", "mean"),
            learner_log_e_median=("learner_log_e", "median"),
            evaluator_log_e_mean=("evaluator_full_feedback_log_e", "mean"),
            evaluator_log_e_median=("evaluator_full_feedback_log_e", "median"),
        )
        .reset_index()
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    seed_path = output_dir / "seed_diagnostics.csv"
    summary_path = output_dir / "group_summary.csv"
    snapshots_path = output_dir / "log_e_snapshots.csv"
    seed_metrics.to_csv(seed_path, index=False)
    grouped.to_csv(summary_path, index=False)
    snapshot_summary.to_csv(snapshots_path, index=False)
    report_path = output_dir / "monitor_signal_diagnostic.md"
    lines = [
        "# Monitor signal diagnostic",
        "",
        f"Input trace: `{trace_path}`. The unit of aggregation is the stream seed. This is a descriptive re-analysis of the supplied run, not an independent replication, calibration study, or method-selection experiment.",
        "",
        "`learner_*` values use only predictions and outcomes available under the run's query process. `evaluator_*` values use synthetic ground truth and full feedback for diagnosis only; they are not learner inputs. Expected excess cost is already centered at the configured harm margin, so positive values indicate expected harm above that margin.",
        "",
        "The full-feedback comparator updates the same bounded betting mixture on every synthetic outcome. Its crossing rate is descriptive and does not establish a valid monitoring guarantee under the alternative. Null calibration must be assessed in separate null experiments.",
        "",
        "## Seed-aggregated results",
        "",
        "|Scenario|Method|Streams|Mean expected excess cost|Fraction positive|PPI increment variance|Full-feedback increment variance|Learner crossings|Full-feedback crossings|Learner post-onset crossings|Full-feedback post-onset crossings|Learner delay|Full-feedback delay|",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in grouped.to_dict("records"):
        lines.append(
            f"|{row['scenario']}|{row['method']}|{int(row['streams'])}|{row['mean_expected_excess_cost']:.4f}|{row['mean_fraction_expected_harm_positive']:.3f}|{row['mean_ppi_increment_variance']:.4f}|{row['mean_full_feedback_increment_variance']:.4f}|{row['learner_crossing_rate']:.3f}|{row['evaluator_crossing_rate']:.3f}|{row['learner_post_onset_crossing_rate']:.3f}|{row['evaluator_post_onset_crossing_rate']:.3f}|{row['learner_detection_delay_mean']:.1f}|{row['evaluator_detection_delay_mean']:.1f}|"
        )
    lines.extend(
        [
            "",
            "## Cumulative evidence snapshots",
            "",
            "See `log_e_snapshots.csv` for mean and median cumulative log-e values at 25%, 50%, 75%, and 100% of each observed monitor path. These are descriptive trajectories; they are not additional independent test statistics.",
            "",
            "No visual was generated. PaperBanana is not available in the active environment.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    run_output = output_dir.parent
    if (run_output / "reports" / "manifest.json").is_file():
        finalize_manifest(run_output)
    return seed_path, summary_path, report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="metrics/event_traces.parquet from a traced run")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = analyze(args.trace, args.output)
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
