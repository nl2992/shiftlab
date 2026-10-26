"""Replay established bounded-mean e-process candidates on the saved CRSP daily cost path."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.stats import rankdata

from shiftlab.data.provenance import sha256, write_json
from shiftlab.dive.eprocess import (
    BoundedMeanEProcess,
    PredictablePlugInEmpiricalBernsteinEProcess,
    PredictableStartedMixtureEProcess,
    PredictableVarianceAdaptiveEProcess,
)

ALPHA = 0.05
TURNOVER_FEE = 5 / 10_000.0
RETURN_CAP = 0.10
E_PROCESS_BOUND = 0.20 + 4 * TURNOVER_FEE
OUTPUT_INPUT = Path("outputs/crsp_monitor_comparison_full")
PROTOCOL = Path("docs/crsp_eprocess_candidate_replay_protocol.md")
HARM_LABEL_COLUMN = "next_20_date_harm_label"


def _verify_checksums(directory: Path) -> None:
    checksum_file = directory / "checksums.sha256"
    for line in checksum_file.read_text(encoding="utf-8").splitlines():
        expected, filename = line.split("  ", 1)
        actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"input artifact checksum mismatch: {filename}")


def _auroc_ap(scores: np.ndarray, labels: np.ndarray) -> tuple[float | None, float | None, int]:
    valid = np.isfinite(scores) & np.isfinite(labels)
    values, target = scores[valid], labels[valid].astype(bool)
    positives = int(target.sum())
    if positives in (0, len(target)):
        return None, None, positives
    ranks = rankdata(values, method="average")
    auroc = (ranks[target].sum() - positives * (positives + 1) / 2) / (
        positives * (len(target) - positives)
    )
    order = np.argsort(-values, kind="stable")
    cumulative = np.cumsum(target[order])
    precision = cumulative / np.arange(1, len(target) + 1)
    average_precision = float(np.sum(precision * target[order]) / positives)
    return float(auroc), average_precision, positives


def replay(*, input_dir: Path, output_dir: Path) -> Path:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")
    _verify_checksums(input_dir)
    input_path = input_dir / "monitor_trajectory.parquet"
    frame = pd.read_parquet(input_path)
    required = {"date", "mean_paired_excess_cost_5bps", HARM_LABEL_COLUMN}
    if not required <= set(frame.columns):
        raise ValueError(
            f"daily trajectory lacks required columns: {sorted(required - set(frame.columns))}"
        )
    frame["date"] = pd.to_datetime(frame.date, errors="raise")
    frame.sort_values("date", kind="stable", inplace=True)
    frame.reset_index(drop=True, inplace=True)
    if frame.date.duplicated().any() or not frame.date.is_monotonic_increasing:
        raise ValueError("daily trajectory dates must be unique and increasing")
    values = pd.to_numeric(frame.mean_paired_excess_cost_5bps, errors="raise").to_numpy(float)
    if (
        len(values) < 64
        or not np.isfinite(values).all()
        or np.max(np.abs(values)) > E_PROCESS_BOUND
    ):
        raise ValueError(
            "paired-cost path is too short, nonfinite, or outside the registered bound"
        )
    labels_series = frame[HARM_LABEL_COLUMN]
    labels = labels_series.map(
        lambda value: np.nan if pd.isna(value) else float(bool(value))
    ).to_numpy(float)

    horizon = len(values)
    starts = tuple(round(i * horizon / 8) for i in range(8))
    processes = {
        "fixed_stake_mixture": BoundedMeanEProcess(bound=E_PROCESS_BOUND, alpha=ALPHA),
        "predictable_kelly": PredictableVarianceAdaptiveEProcess(
            bound=E_PROCESS_BOUND, alpha=ALPHA
        ),
        "plug_in_empirical_bernstein": PredictablePlugInEmpiricalBernsteinEProcess(
            bound=E_PROCESS_BOUND, alpha=ALPHA
        ),
        "uniform_eight_start_mixture": PredictableStartedMixtureEProcess(
            alpha=ALPHA, starts=starts
        ),
    }
    score_paths = {name: np.empty(horizon, dtype=float) for name in processes}
    trace_rows: list[dict[str, object]] = []
    for t, value in enumerate(values):
        for name, process in processes.items():
            if name == "uniform_eight_start_mixture":
                score = process.update(float(value), bound=E_PROCESS_BOUND)
            else:
                score = process.update(float(value))
            score_paths[name][t] = score
        trace_rows.append(
            {
                "date": frame.date.iloc[t].date().isoformat(),
                "daily_paired_excess_cost_5bps": float(value),
                **{name: float(scores[t]) for name, scores in score_paths.items()},
                HARM_LABEL_COLUMN: None if not np.isfinite(labels[t]) else bool(labels[t]),
            }
        )

    rows = []
    threshold = math.log(1 / ALPHA)
    for name, scores in score_paths.items():
        auroc, average_precision, positive_windows = _auroc_ap(scores, labels)
        crossings = np.flatnonzero(scores >= threshold)
        rows.append(
            {
                "monitor": name,
                "alpha_threshold_log_e": threshold,
                "first_crossing_date": (
                    frame.date.iloc[int(crossings[0])].date().isoformat()
                    if len(crossings)
                    else None
                ),
                "crossing_fraction_of_test_dates": float(np.mean(scores >= threshold)),
                "maximum_log_e_value": float(scores.max()),
                "auroc_for_next_20_date_harm": auroc,
                "average_precision_for_next_20_date_harm": average_precision,
                "positive_harm_windows": positive_windows,
                "updates": horizon,
                "interpretation": "retrospective diagnostic; e-process assumptions unverified on CRSP",
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "experiment": "CRSP retrospective replay of established bounded-mean e-process candidates",
        "input_directory": input_dir.as_posix(),
        "input_trajectory_sha256": sha256(input_path),
        "input_checksum_file_sha256": sha256(input_dir / "checksums.sha256"),
        "protocol_sha256": hashlib.sha256(PROTOCOL.read_bytes()).hexdigest(),
        "dates": [frame.date.iloc[0].date().isoformat(), frame.date.iloc[-1].date().isoformat()],
        "test_dates": horizon,
        "turnover_cost_bps": 5,
        "daily_increment": "cross-sectional mean paired candidate-minus-reference capped cost for each CRSP date",
        "bound": E_PROCESS_BOUND,
        "alpha": ALPHA,
        "start_mixture": {
            "component_count": len(starts),
            "start_indices": list(starts),
            "weights": "equal and fixed before replay",
        },
        "future_harm_label": "evaluator-only positive mean paired cost over the next 20 test dates; overlapping hindsight labels",
        "monitors": rows,
        "limitations": [
            "All methods replay one dependent historical sequence and share the same fixed policy and daily paired-cost increments.",
            "The conditional-on-past mean null, per-date independence/dependence structure, and CRSP release times are not established; crossing frequencies are not false-alarm rates.",
            "Start locations use the registered fixed full test horizon and are not adapted to observed costs.",
            "Future-harm labels are used only for retrospective ranking and do not establish prospective detection quality.",
            "The bound is intentionally kept equal to the preceding CRSP fixed-mixture diagnostic to preserve comparability, though a tighter paired-action-specific bound may be possible after a separate audit.",
            "These are established e-process constructions; no novelty, real-data validity, or deployment claim is made.",
        ],
        "source_sha256": sha256(Path(__file__)),
        "created_utc": datetime.now(UTC).isoformat(),
    }
    pd.DataFrame(rows).to_csv(output_dir / "monitor_comparison.csv", index=False)
    pq.write_table(pa.Table.from_pylist(rows), output_dir / "monitor_comparison.parquet")
    pd.DataFrame(trace_rows).to_csv(output_dir / "monitor_trajectory.csv", index=False)
    pq.write_table(pa.Table.from_pylist(trace_rows), output_dir / "monitor_trajectory.parquet")
    write_json(output_dir / "report.json", report)
    checksums = [
        f"{hashlib.sha256(item.read_bytes()).hexdigest()}  {item.name}"
        for item in sorted(output_dir.iterdir())
        if item.name != "checksums.sha256"
    ]
    (output_dir / "checksums.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=OUTPUT_INPUT)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs/crsp_eprocess_candidate_replay")
    )
    args = parser.parse_args()
    replay(input_dir=args.input_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
