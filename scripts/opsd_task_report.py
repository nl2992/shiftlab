"""Export provenance, observed coverage and task timing for actual OPSD versions."""

import argparse
import json
from pathlib import Path

import pandas as pd

from shiftlab.data.group_diagnostics import group_summaries
from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.validation import validate_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-path", nargs="+", required=True)
    parser.add_argument("--report-dir", default="data/reports/opsd_tasks")
    args = parser.parse_args()
    report = Path(args.report_dir)
    report.mkdir(parents=True, exist_ok=True)
    versions, summaries = [], []
    for value in args.dataset_path:
        path = Path(value)
        quality = validate_dataset(path)
        manifest = json.loads((path / "dataset_manifest.json").read_text())
        if manifest["dataset"] != "opsd":
            parser.error("Expected OPSD version directories")
        frame = pd.read_parquet(path / "observations.parquet")
        features, _ = group_summaries(frame, manifest["feature_names"])
        features.insert(0, "version", manifest["version"])
        summaries.append(features)
        metadata = json.loads(frame.metadata.iloc[0])
        versions.append(
            {
                "manifest": manifest,
                "quality": quality,
                "input_manifest_sha256": sha256(path / "dataset_manifest.json"),
                "task": metadata["task"],
                "aggregation": metadata["aggregation"],
                "source_fields": metadata["source_fields"],
                "outcome_event_lag_seconds": sorted(
                    (frame.label_event_time - frame.event_time).unique().tolist()
                ),
                "partition_counts": frame.split.value_counts().to_dict(),
            }
        )
    pd.concat(summaries, ignore_index=True).to_csv(report / "feature_coverage.csv", index=False)
    write_json(
        report / "validation.json",
        {
            "versions": versions,
            "processing_commit": commit(),
            "source_hash": source_hash(),
            "script_sha256": sha256(Path(__file__)),
            "executed_at": utc_now(),
            "excluded_candidate": "AT_price_day_ahead has zero observed values in the 2019 source window; default panel uses DE/DE_LU and DK_1 instead.",
            "availability": "unknown; retrospective task and outcome timing only",
        },
    )
    print(report)


if __name__ == "__main__":
    main()
