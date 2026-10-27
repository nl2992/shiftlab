"""Independently verify the ADWIN/DDM EIA frontier artifacts and cutoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import evaluate_cara_eia_frontier as cara
import evaluate_upf_eia_frontier as upf
import numpy as np
import pandas as pd

from shiftlab.data.provenance import sha256

ROOT = Path(__file__).resolve().parents[1]
CARA_OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/cara_eia_frontier_v1"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(output_dir: Path, dataset_path: Path) -> dict[str, object]:
    output_dir = output_dir.resolve()
    dataset_path = dataset_path.resolve()
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    dataset_manifest = dataset_path / "dataset_manifest.json"
    observations = dataset_path / "observations.parquet"
    if manifest["dataset_manifest_sha256"] != sha256(dataset_manifest):
        raise ValueError("dataset manifest hash mismatch")
    if manifest["observations_sha256"] != sha256(observations):
        raise ValueError("observation hash mismatch")
    if manifest["protocol_sha256"] != _hash(output_dir / "protocol_snapshot.md"):
        raise ValueError("protocol snapshot hash mismatch")
    cara_manifest_path = CARA_OUTPUT / "manifest.json"
    if manifest["cara_manifest_sha256"] != sha256(cara_manifest_path):
        raise ValueError("CARA manifest hash mismatch")
    cara_metrics = CARA_OUTPUT / "matched_period_metrics.parquet"
    if manifest["cara_matched_metrics_sha256"] != _hash(cara_metrics):
        raise ValueError("CARA input frontier hash mismatch")

    for artifact, expected in manifest["artifacts"].items():
        if _hash(output_dir / artifact) != expected:
            raise ValueError(f"artifact hash mismatch: {artifact}")
    for source, expected in manifest["execution_source_hashes"].items():
        if _hash(output_dir / "execution_sources" / Path(source).name) != expected:
            raise ValueError(f"execution source snapshot mismatch: {source}")

    detector = pd.read_parquet(output_dir / "detector_period_metrics.parquet")
    matched = pd.read_parquet(output_dir / "matched_period_metrics.parquet")
    summary = pd.read_csv(output_dir / "summary.csv")
    expected_methods = {
        "never",
        "always",
        "periodic_2",
        "periodic_4",
        "error_threshold",
        "upf",
        "rccda_paper_rule",
        "oracle",
        "cara_threshold",
        "cara_cumulative_threshold",
        "cara_periodic",
        "adwin_bounded_loss",
        "ddm_tail_error",
    }
    if (
        set(manifest["methods"]) != expected_methods
        or set(matched.method.unique()) != expected_methods
    ):
        raise ValueError("method set mismatch")
    expected_detector = (
        2
        * len(upf.LABEL_DELAYS_HOURS)
        * upf.N_ALPHA_POINTS
        * 2
        * (upf.N_PERIODS - upf.ONLINE_START)
    )
    expected_matched = (
        2
        * len(upf.LABEL_DELAYS_HOURS)
        * upf.N_ALPHA_POINTS
        * len(expected_methods)
        * (upf.N_PERIODS - upf.ONLINE_START)
    )
    if len(detector) != expected_detector or len(matched) != expected_matched:
        raise ValueError("detector or matched row count mismatch")
    key_cols = ["domain_id", "delay_hours", "method", "alpha", "period"]
    if matched.duplicated(key_cols).any():
        raise ValueError("duplicate matched metric keys")
    if not set(detector.period.unique()).issubset(set(range(upf.ONLINE_START, upf.N_PERIODS))):
        raise ValueError("detector rows include an offline evaluation period")
    if (detector.active_model_period > detector.period).any():
        raise ValueError("a detector policy used a future candidate model")
    if not np.array_equal(
        detector.retrained.to_numpy(dtype=bool),
        (detector.active_model_period == detector.period).to_numpy(dtype=bool),
    ):
        raise ValueError("detector retrain flags do not match active model periods")

    frame = pd.read_parquet(observations)
    expected_counts: dict[tuple[str, int, int], int] = {}
    for domain, group in frame.groupby("domain_id", sort=True):
        data = upf._period_data(group)
        for delay in upf.LABEL_DELAYS_HOURS:
            for period in range(upf.ONLINE_START, upf.N_PERIODS):
                expected_counts[(str(domain), delay, period)] = int(
                    cara._maturity_indices(data, period, delay).size
                )
    for row in detector.itertuples(index=False):
        expected = expected_counts[(str(row.domain_id), int(row.delay_hours), int(row.period))]
        if int(row.mature_current_prefix_rows) != expected:
            raise ValueError("detector received an unexpected maturity count")

    groups = matched.groupby(["domain_id", "delay_hours", "alpha", "period"])
    if not groups.evaluation_rows.nunique().eq(1).all():
        raise ValueError("methods do not share identical evaluation row counts")
    objective = matched.assign(
        objective=matched.bounded_loss + matched.alpha * matched.retrained.astype(int)
    )
    totals = objective.groupby(["domain_id", "delay_hours", "alpha", "method"]).objective.sum()
    for keys, cell in totals.groupby(level=[0, 1, 2]):
        cell = cell.droplevel([0, 1, 2])
        if cell["oracle"] > cell.drop("oracle").min() + 1e-10:
            raise ValueError(f"oracle is not a lower bound in cell {keys}")
    if summary.duplicated(["domain_id", "delay_hours", "method", "alpha"]).any():
        raise ValueError("duplicate summary cells")
    return {
        "status": "passed",
        "detector_rows": len(detector),
        "matched_rows": len(matched),
        "methods": sorted(expected_methods),
        "gpu": manifest["gpu_name"],
        "river_version": manifest["river_version"],
        "oracle_cost_cells_checked": 40,
        "artifact_and_source_hashes_checked": len(manifest["artifacts"])
        + len(manifest["execution_source_hashes"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/eia_drift_detectors_v1"),
    )
    parser.add_argument(
        "--dataset-path", type=Path, default=Path("data/processed/eia/e47bdef8b208f8e7d788")
    )
    args = parser.parse_args()
    print(json.dumps(verify(args.output_dir, args.dataset_path), indent=2))


if __name__ == "__main__":
    main()
