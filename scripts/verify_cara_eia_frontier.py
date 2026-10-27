"""Independently check CARA EIA frontier integrity and timing invariants."""

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


def _file_hash(path: Path) -> str:
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
    if manifest["protocol_sha256"] != _file_hash(output_dir / "protocol_snapshot.md"):
        raise ValueError("protocol snapshot hash mismatch")

    for artifact, expected in manifest["artifacts"].items():
        if _file_hash(output_dir / artifact) != expected:
            raise ValueError(f"artifact hash mismatch: {artifact}")
    for source, expected in manifest["execution_source_hashes"].items():
        basename = Path(source).name
        if _file_hash(output_dir / "execution_sources" / basename) != expected:
            raise ValueError(f"execution source snapshot mismatch: {source}")

    cara_metrics = pd.read_parquet(output_dir / "cara_period_metrics.parquet")
    matched = pd.read_parquet(output_dir / "matched_period_metrics.parquet")
    summary = pd.read_csv(output_dir / "summary.csv")
    methods = set(manifest["methods"])
    expected_methods = {
        "never",
        "always",
        "periodic_2",
        "periodic_4",
        "error_threshold",
        "upf",
        "rccda_paper_rule",
        "oracle",
        *cara.CARA_METHODS,
    }
    if methods != expected_methods:
        raise ValueError(f"unexpected method set: {methods ^ expected_methods}")
    expected_cara_rows = (
        2
        * len(upf.LABEL_DELAYS_HOURS)
        * upf.N_ALPHA_POINTS
        * len(cara.CARA_METHODS)
        * (upf.N_PERIODS - upf.ONLINE_START)
    )
    expected_total = expected_cara_rows + 2 * len(
        upf.LABEL_DELAYS_HOURS
    ) * upf.N_ALPHA_POINTS * 8 * (upf.N_PERIODS - upf.ONLINE_START)
    if len(cara_metrics) != expected_cara_rows or len(matched) != expected_total:
        raise ValueError("metric row count mismatch")
    key_columns = ["domain_id", "delay_hours", "method", "alpha", "period"]
    if matched.duplicated(key_columns).any():
        raise ValueError("duplicate matched metric keys")
    if not set(matched.period.unique()).issubset(set(range(upf.ONLINE_START, upf.N_PERIODS))):
        raise ValueError("offline rows leaked into online metrics")
    if (cara_metrics.active_model_period > cara_metrics.period).any():
        raise ValueError("a policy used a candidate trained after its decision time")
    if not np.array_equal(
        cara_metrics.retrained.to_numpy(dtype=bool),
        (cara_metrics.active_model_period == cara_metrics.period).to_numpy(dtype=bool),
    ):
        raise ValueError("retrain flag does not match active candidate")

    frame = pd.read_parquet(observations)
    expected_counts: dict[tuple[str, int, int], int] = {}
    for domain, group in frame.groupby("domain_id", sort=True):
        data = upf._period_data(group)
        for delay in upf.LABEL_DELAYS_HOURS:
            for period in range(upf.ONLINE_START, upf.N_PERIODS):
                expected_counts[(str(domain), delay, period)] = int(
                    cara._maturity_indices(data, period, delay).size
                )
    for row in cara_metrics.itertuples(index=False):
        expected = expected_counts[(str(row.domain_id), int(row.delay_hours), int(row.period))]
        if int(row.mature_current_prefix_rows) != expected:
            raise ValueError("recorded current-prefix maturity count mismatch")

    grouped = matched.groupby(["domain_id", "delay_hours", "alpha", "period"])
    if not grouped.evaluation_rows.nunique().eq(1).all():
        raise ValueError("methods do not use matched evaluation row counts")
    online = matched.loc[matched.method != "oracle"]
    oracle = matched.loc[matched.method == "oracle"]
    cost_cols = ["domain_id", "delay_hours", "alpha"]
    online = online.assign(
        objective=online.bounded_loss + online.alpha * online.retrained.astype(int)
    )
    oracle = oracle.assign(
        objective=oracle.bounded_loss + oracle.alpha * oracle.retrained.astype(int)
    )
    online_cost = online.groupby(cost_cols).objective.sum()
    oracle_cost = oracle.groupby(cost_cols).objective.sum()
    if (oracle_cost > online_cost.groupby(level=cost_cols).min() + 1e-10).any():
        raise ValueError("evaluator oracle is not a lower bound on feasible methods")
    if summary.duplicated(["domain_id", "delay_hours", "method", "alpha"]).any():
        raise ValueError("duplicate summary cells")
    return {
        "status": "passed",
        "cara_rows": len(cara_metrics),
        "matched_rows": len(matched),
        "domains": sorted(matched.domain_id.astype(str).unique().tolist()),
        "methods": sorted(methods),
        "gpu": manifest["gpu_name"],
        "oracle_cost_cells_checked": len(oracle_cost),
        "source_and_artifact_hashes_checked": len(manifest["artifacts"])
        + len(manifest["execution_source_hashes"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/cara_eia_frontier_v1"),
    )
    parser.add_argument(
        "--dataset-path", type=Path, default=Path("data/processed/eia/e47bdef8b208f8e7d788")
    )
    args = parser.parse_args()
    result = verify(args.output_dir, args.dataset_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
