"""Validate and summarize a stored NOAA panel without inventing availability times."""

import argparse
import json
from pathlib import Path

import pandas as pd

from shiftlab.data.group_diagnostics import group_summaries
from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.validation import validate_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--report-dir", default="data/reports/noaa_panel")
    args = parser.parse_args()
    path, report = Path(args.dataset_path), Path(args.report_dir)
    quality = validate_dataset(path)
    manifest = json.loads((path / "dataset_manifest.json").read_text())
    if manifest["dataset"] != "noaa":
        parser.error("Expected a NOAA version directory")
    frame = pd.read_parquet(path / "observations.parquet")
    features, _ = group_summaries(frame, manifest["feature_names"])
    rows = []
    for station, group in frame.groupby("domain_id", sort=False):
        horizon = group.label_event_time - group.event_time
        source = json.loads(group.metadata.iloc[0])["source"]
        rows.append(
            {
                "station": station,
                "source_name": source.get("NAME"),
                "rows": len(group),
                "event_start_utc": pd.to_datetime(
                    group.event_time.min(), unit="s", utc=True
                ).isoformat(),
                "event_end_utc": pd.to_datetime(
                    group.event_time.max(), unit="s", utc=True
                ).isoformat(),
                "horizon_seconds_min": float(horizon.min()),
                "horizon_seconds_median": float(horizon.median()),
                "horizon_seconds_max": float(horizon.max()),
                "unknown_label_availability": int(group.label_available_time.isna().sum()),
                "missing_target_count": int(group.target.isna().sum()),
            }
        )
    report.mkdir(parents=True, exist_ok=True)
    features.to_csv(report / "feature_summaries.csv", index=False)
    pd.DataFrame(rows).to_csv(report / "station_summary.csv", index=False)
    frame.groupby(["domain_id", "split"], sort=False).size().rename("rows").to_csv(
        report / "partition_counts.csv"
    )
    write_json(
        report / "validation.json",
        {
            "quality": quality,
            "input_manifest_sha256": sha256(path / "dataset_manifest.json"),
            "source_hash": source_hash(),
            "script_sha256": sha256(Path(__file__)),
            "processing_commit": commit(),
            "executed_at": utc_now(),
            "manifest": manifest,
        },
    )
    print(report)


if __name__ == "__main__":
    main()
