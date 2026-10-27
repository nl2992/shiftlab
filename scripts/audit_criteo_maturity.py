"""Stream aggregate Criteo Attribution label-maturity diagnostics."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from shiftlab.data.provenance import commit, sha256, utc_now, write_json

EXPECTED_VERSION = "c9a39688a4d56f404fb3"
MATURITY_SECONDS = 30 * 86_400


def _curve_cutoffs(start: float, end: float) -> np.ndarray:
    days = int(np.floor((end - start) / 86_400))
    cutoffs = start + np.arange(days + 1, dtype=np.float64) * 86_400
    if cutoffs[-1] < end:
        cutoffs = np.append(cutoffs, end)
    return cutoffs


def audit(dataset_path: Path, output_dir: Path) -> Path:
    manifest_path = dataset_path / "dataset_manifest.json"
    observations_path = dataset_path / "observations.parquet"
    protocol_path = (
        Path(__file__).resolve().parents[1]
        / "papers/shiftguard_unified/criteo_maturity_audit_protocol.md"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("dataset") != "criteo_attribution"
        or manifest.get("version") != EXPECTED_VERSION
    ):
        raise ValueError("This frozen audit accepts only the pinned Criteo release")
    parquet = pq.ParquetFile(observations_path)
    missing_columns = {"event_time", "target", "label_available_time"} - set(parquet.schema.names)
    if missing_columns:
        raise ValueError(
            f"Criteo observations lack required audit columns: {sorted(missing_columns)}"
        )

    start_time = None
    end_time = None
    previous_time = -np.inf
    row_count = 0
    for batch in parquet.iter_batches(columns=["event_time"], batch_size=250_000):
        times = batch.column("event_time").to_numpy(zero_copy_only=False).astype(np.float64)
        if not np.isfinite(times).all() or (np.diff(times) < 0).any() or times[0] < previous_time:
            raise ValueError("Publisher-relative impression times must be finite and nondecreasing")
        if start_time is None:
            start_time = float(times[0])
        end_time = float(times[-1])
        previous_time = end_time
        row_count += len(times)
    if start_time is None or end_time is None:
        raise ValueError("Criteo observations parquet is empty")
    if row_count != int(manifest.get("n_observations", -1)):
        raise ValueError("Parquet row count disagrees with its dataset manifest")
    cutoffs = _curve_cutoffs(start_time, end_time)
    event_deltas = np.zeros(len(cutoffs) + 1, dtype=np.int64)
    matured_deltas = np.zeros(len(cutoffs) + 1, dtype=np.int64)
    positive_deltas = np.zeros(len(cutoffs) + 1, dtype=np.int64)
    negative_deltas = np.zeros(len(cutoffs) + 1, dtype=np.int64)
    positive_total = 0
    negative_total = 0
    max_available: float = float("-inf")
    for batch in parquet.iter_batches(
        columns=["event_time", "target", "label_available_time"], batch_size=250_000
    ):
        event = batch.column("event_time").to_numpy(zero_copy_only=False).astype(np.float64)
        target = batch.column("target").to_numpy(zero_copy_only=False).astype(np.float64)
        available = (
            batch.column("label_available_time").to_numpy(zero_copy_only=False).astype(np.float64)
        )
        if (
            not np.isfinite(event).all()
            or not np.isfinite(available).all()
            or not np.isin(target, [0, 1]).all()
        ):
            raise ValueError("Criteo event/availability times or binary outcomes are invalid")
        if np.any(available < event) or not np.allclose(
            available - event, MATURITY_SECONDS, atol=1e-5, rtol=0
        ):
            raise ValueError("Processed availability does not match the conservative 30-day rule")
        positive = target == 1
        positive_total += int(positive.sum())
        negative_total += int((~positive).sum())
        max_available = max(max_available, float(available.max()))
        event_index = np.searchsorted(cutoffs, event, side="left")
        mature_index = np.searchsorted(cutoffs, available, side="left")
        np.add.at(event_deltas, event_index[event_index < len(cutoffs)], 1)
        in_stream = mature_index < len(cutoffs)
        np.add.at(matured_deltas, mature_index[in_stream], 1)
        np.add.at(positive_deltas, mature_index[in_stream & positive], 1)
        np.add.at(negative_deltas, mature_index[in_stream & ~positive], 1)

    event_seen = np.cumsum(event_deltas[:-1])
    matured_count = np.cumsum(matured_deltas[:-1])
    matured_positive = np.cumsum(positive_deltas[:-1])
    matured_negative = np.cumsum(negative_deltas[:-1])
    duration = end_time - start_time
    curve = [
        {
            "days_since_first_event": float((cutoff - start_time) / 86_400),
            "event_time_cutoff": float(cutoff),
            "observations_seen": int(event_seen[index]),
            "labels_matured_by_cutoff": int(matured_count[index]),
            "fraction_of_full_dataset_matured": float(matured_count[index] / row_count),
            "positive_labels_matured": int(matured_positive[index]),
            "negative_labels_matured": int(matured_negative[index]),
        }
        for index, cutoff in enumerate(cutoffs)
    ]
    end_index = len(cutoffs) - 1
    summary = {
        "observations": row_count,
        "positive_labels": positive_total,
        "negative_labels": negative_total,
        "event_time_start": start_time,
        "event_time_end": end_time,
        "event_span_seconds": duration,
        "event_span_days": duration / 86_400,
        "label_available_time_end": max_available,
        "max_followup_after_last_event_seconds": float(max_available - end_time),
        "labels_matured_by_last_impression": int(matured_count[end_index]),
        "fraction_matured_by_last_impression": float(matured_count[end_index] / row_count),
        "positive_matured_by_last_impression": int(matured_positive[end_index]),
        "negative_matured_by_last_impression": int(matured_negative[end_index]),
        "maturity_curve": curve,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    curve = pd.DataFrame(summary.pop("maturity_curve"))
    curve.to_csv(output_dir / "maturity_curve.csv", index=False)
    remaining_followup_days = (max_available - end_time) / 86_400
    summary["maturity_rule_seconds"] = MATURITY_SECONDS
    summary["maturity_rule_verified_against_processed_contract"] = True
    summary["suitability"] = (
        "not suitable for informative within-impression-stream delayed-monitor comparison under this conservative maturity convention; only the observed maturity curve supports this judgment"
    )
    run_manifest = {
        "audit": "criteo_attribution_maturity_suitability_v2",
        "executed_at": utc_now(),
        "git_head": commit(),
        "dataset_version": manifest["version"],
        "source_url": manifest.get("source_url"),
        "license": manifest.get("license"),
        "input_manifest_sha256": sha256(manifest_path),
        "observations_sha256": sha256(observations_path),
        "protocol_sha256": sha256(protocol_path),
        "runner_sha256": sha256(Path(__file__)),
        "python_version": platform.python_version(),
        "processed_rows": summary["observations"],
        "learner_data_accessed": "none; aggregate source timing/label fields only",
        "row_level_outputs": False,
        "summary": summary,
        "output_sha256": {},
    }
    report_lines = [
        "# Criteo Attribution 30-day label-maturity suitability audit",
        "",
        "**Status:** aggregate-only source timing audit. The publisher-relative clock and 30-day maturity are not verified real-world release instants.",
        "",
        f"- Rows: {summary['observations']:,} ({summary['positive_labels']:,} conversions; {summary['negative_labels']:,} nonconversions).",
        f"- Impression stream span: {summary['event_span_days']:.3f} days.",
        f"- Conservative labels mature by the last impression: {summary['labels_matured_by_last_impression']:,} ({summary['fraction_matured_by_last_impression']:.2%}).",
        f"- Mature positives by the last impression: {summary['positive_matured_by_last_impression']:,}; mature negatives: {summary['negative_matured_by_last_impression']:,}.",
        f"- Remaining follow-up to the final label: {remaining_followup_days:.1f} days.",
        "",
        f"Under this conservative rule, only {summary['fraction_matured_by_last_impression']:.2%} of labels mature within the 30.9-day impression stream, leaving too little within-stream feedback for an informative delayed-monitor comparison. The data can support retrospective fixed-sample prediction or a delayed-feedback stress test that explicitly continues label arrivals for the 30-day follow-up. The data contain no verified campaign counterfactual outcomes, and `cost`/`cpo` are transformed publisher fields rather than real prices.",
        "",
        "See `maturity_curve.csv` and `manifest.json` for the daily maturity curve and source/protocol/output hashes. Only aggregate counts are saved.",
    ]
    (output_dir / "results.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    run_manifest["output_sha256"] = {
        name: sha256(output_dir / name) for name in ("maturity_curve.csv", "results.md")
    }
    write_json(output_dir / "manifest.json", run_manifest)
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-path",
        type=Path,
        default=Path("data/processed/criteo_attribution/c9a39688a4d56f404fb3"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/criteo_maturity_v2"),
    )
    args = parser.parse_args()
    print(audit(args.dataset_path, args.output_dir))


if __name__ == "__main__":
    main()
