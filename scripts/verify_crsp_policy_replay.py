"""Verify provenance and aggregate consistency of a CRSP replay artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/crsp_decision_policy_replay_protocol.md"
RUN_SCRIPT = ROOT / "scripts/evaluate_crsp_policy_replay.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(output: Path, data_root: Path) -> dict[str, object]:
    report_path = output / "report.json"
    cost_path = output / "cost_summary.csv"
    yearly_path = output / "yearly_cost_summary.csv"
    checksum_path = output / "checksums.sha256"
    for path in (report_path, cost_path, yearly_path, checksum_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    expected_files: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        expected_files[name.strip()] = digest
    if set(expected_files) != {"report.json", "cost_summary.csv", "yearly_cost_summary.csv"}:
        raise ValueError("checksums.sha256 does not enumerate the three expected outputs")
    for name, expected in expected_files.items():
        if sha256(output / name) != expected:
            raise ValueError(f"output checksum mismatch: {name}")

    report = json.loads(report_path.read_text(encoding="utf-8"))
    panel = data_root / "processed" / "crsp_ciz_next_day" / report["dataset_version"]
    panel_manifest_path = panel / "dataset_manifest.json"
    panel_manifest = json.loads(panel_manifest_path.read_text(encoding="utf-8"))
    if sha256(panel_manifest_path) != report["dataset_manifest_sha256"]:
        raise ValueError("panel manifest checksum mismatch")
    observations_path = panel / "observations.parquet"
    expected_observations = panel_manifest["files"]["observations.parquet"]
    if expected_observations != report["observations_sha256"]:
        raise ValueError("report and panel manifest disagree on observation checksum")
    if sha256(observations_path) != expected_observations:
        raise ValueError("panel observations checksum mismatch")
    if sha256(PROTOCOL) != report["protocol_sha256"]:
        raise ValueError("protocol checksum mismatch")
    if sha256(RUN_SCRIPT) != report["script_sha256"]:
        raise ValueError("runner source checksum mismatch")

    cost = pd.read_csv(cost_path)
    yearly = pd.read_csv(yearly_path)
    expected_cost = pd.DataFrame(report["cost_comparison"])
    expected_yearly = pd.DataFrame(report["yearly_cost_comparison"])
    numeric_cost = [
        "mean_candidate_cost",
        "mean_reference_cost",
        "mean_candidate_minus_reference_cost",
        "candidate_long_action_rate",
        "reference_long_action_rate",
        "return_clipped_fraction",
    ]
    if len(cost) != 4 or len(yearly) != 24:
        raise ValueError("unexpected number of aggregate or yearly comparison rows")
    if not np.array_equal(
        cost["transaction_cost_bps_per_turnover"],
        expected_cost["transaction_cost_bps_per_turnover"],
    ):
        raise ValueError("CSV and JSON transaction-cost settings disagree")
    if not np.array_equal(yearly["year"], expected_yearly["year"]):
        raise ValueError("CSV and JSON yearly rows disagree")
    for column in numeric_cost:
        if not np.allclose(cost[column], expected_cost[column], rtol=1e-12, atol=1e-15):
            raise ValueError(f"CSV and JSON disagree for {column}")

    for bps in cost["transaction_cost_bps_per_turnover"]:
        overall = cost.loc[cost.transaction_cost_bps_per_turnover.eq(bps)].iloc[0]
        subset = yearly.loc[yearly.transaction_cost_bps_per_turnover.eq(bps)]
        if int(subset["n"].sum()) != int(overall["n_test_events"]):
            raise ValueError(f"yearly event counts do not sum to total for {bps} bps")
        for annual_column, overall_column in (
            ("candidate_mean_cost", "mean_candidate_cost"),
            ("reference_mean_cost", "mean_reference_cost"),
            ("candidate_minus_reference_cost", "mean_candidate_minus_reference_cost"),
        ):
            weighted = np.average(subset[annual_column], weights=subset["n"])
            if not np.isclose(weighted, overall[overall_column], rtol=1e-11, atol=1e-14):
                raise ValueError(f"yearly and overall {annual_column} disagree for {bps} bps")

    checks = {
        "status": "passed_artifact_provenance_and_aggregate_consistency",
        "output": str(output.resolve()),
        "dataset_version": report["dataset_version"],
        "test_events": report["test_rows"],
        "test_permnos": report["test_permno_count"],
        "model_device": report["model_device"],
        "output_files_verified": sorted(expected_files),
        "panel_manifest_verified": True,
        "panel_observations_sha256_verified": True,
        "protocol_sha256_verified": True,
        "runner_sha256_verified": True,
        "annual_weighted_aggregates_match": True,
        "scope": "artifact integrity check; does not independently refit policies or validate inferential assumptions",
    }
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    result = verify(args.output.resolve(), args.data_root.resolve())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
