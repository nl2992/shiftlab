"""Export gas-sensor batch summaries and a fixed train-only baseline."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.data.group_diagnostics import (
    classification_group_evidence,
    fit_offline_classifier,
    group_summaries,
)
from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.validation import validate_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--report-dir", default="data/reports/gas_sensor_groups")
    args = parser.parse_args()
    path, report = Path(args.dataset_path), Path(args.report_dir)
    validate_dataset(path)
    manifest = json.loads((path / "dataset_manifest.json").read_text())
    if manifest["dataset"] != "gas_sensor":
        parser.error("This source-specific evidence command expects gas_sensor")
    frame = pd.read_parquet(path / "observations.parquet")
    features, labels = group_summaries(frame, manifest["feature_names"])
    p, classes = fit_offline_classifier(frame)
    costs = np.ones((len(classes), len(classes))) - np.eye(len(classes))
    # Class 6 is designated high-cost solely for a controlled decision study.
    costs[:, classes == 6] *= 5
    evidence = classification_group_evidence(frame, p, classes, costs)
    report.mkdir(parents=True, exist_ok=True)
    features.to_csv(report / "feature_summaries.csv", index=False)
    labels.to_csv(report / "class_balance.csv", index=False)
    evidence.to_csv(report / "classification_evidence.csv", index=False)
    write_json(
        report / "protocol.json",
        {
            "dataset": manifest["dataset"],
            "version": manifest["version"],
            "executed_at": utc_now(),
            "processing_commit": commit(),
            "processing_source_hash": source_hash(),
            "script_sha256": sha256(Path(__file__)),
            "input_manifest_sha256": sha256(path / "dataset_manifest.json"),
            "train_domains": frame.loc[frame.split == "train", "domain_id"]
            .drop_duplicates()
            .tolist(),
            "feature_inputs": "128 source features only; imputation/scaling fit on train",
            "classes": classes.tolist(),
            "cost_matrix_action_by_class": costs.tolist(),
            "utility_origin": "imposed; class 6 error cost 5, others 1; correct cost zero",
            "timing": "coarse ordered batches; unknown within-batch time, no online claim",
            "probability_calibration": "Brier and log loss reported; no prediction-set coverage claim",
            "attribution": "inconclusive; observational domain evidence is not concept-drift ground truth",
        },
    )
    print(report)


if __name__ == "__main__":
    main()
