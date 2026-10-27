"""Independently verify the completed Q2 null-calibration artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1"
)
PROTOCOL = ROOT / "papers/shiftguard_unified/target_scout_fixed_split_null_calibration_protocol.md"
RUNNER_SNAPSHOT = (
    ROOT
    / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1_runner_at_execution_start.py"
)
METHODS = {"pooled_rank", "fixed_sample_split", "target_scout"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected_hash in manifest["artifacts"].items():
        path = OUTPUT / name
        if not path.is_file() or sha256(path) != expected_hash:
            raise RuntimeError(f"artifact hash mismatch: {name}")
    config = manifest["configuration"]
    runner_hash = config["runner_sha256"]
    if sha256(RUNNER_SNAPSHOT) != runner_hash:
        raise RuntimeError("captured runner snapshot does not match the execution-time hash")
    if (
        manifest["source_hashes"].get("scripts/calibrate_target_scout_fixed_split.py")
        != runner_hash
    ):
        raise RuntimeError(
            "manifest runner source hash differs from the captured execution version"
        )
    if sha256(PROTOCOL) != config["protocol_sha256"]:
        raise RuntimeError("frozen calibration protocol hash mismatch")
    streams = pd.read_parquet(OUTPUT / "streams.parquet")
    summary = pd.read_parquet(OUTPUT / "summary.parquet")
    if len(streams) != 27_000 or len(summary) != 27:
        raise RuntimeError("calibration output row counts are incomplete")
    if streams.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("duplicate method/seed/cell rows")
    if set(streams["method"].unique()) != METHODS:
        raise RuntimeError("method set differs from frozen design")
    if not streams["null_expected_gain_nonpositive"].astype(bool).all():
        raise RuntimeError("a row is missing the evaluator-known null assertion")
    if (streams["labels_queried"] > streams["label_budget"]).any():
        raise RuntimeError("pathwise label cap violation")
    label_counts = streams.pivot(
        index=["scenario", "seed"], columns="method", values="labels_queried"
    )
    if label_counts.nunique(axis=1).ne(1).any():
        raise RuntimeError("paired methods have different query counts")
    promoted = streams["promoted"].astype(bool)
    promoted_gains = streams.loc[promoted, "expected_postpromotion_net_gain"].to_numpy(dtype=float)
    if np.any(promoted_gains > 1e-9):
        raise RuntimeError("positive-net-gain promotion under the registered null")
    if streams.loc[promoted, "harmful_postpromotion_promotion"].astype(bool).ne(True).any():
        raise RuntimeError("harmful-promotion flags do not match evaluator gains")

    per_stratum_alpha = 0.05 / 27
    for row in summary.to_dict(orient="records"):
        group = streams.loc[
            streams["scenario"].eq(row["scenario"]) & streams["method"].eq(row["method"])
        ]
        events, trials = int(group["promoted"].astype(bool).sum()), len(group)
        upper = (
            1.0
            if events == trials
            else float(beta.ppf(1 - per_stratum_alpha, events + 1, trials - events))
        )
        if trials != 1000 or events != int(row["false_promotions"]):
            raise RuntimeError("summary event counts do not match per-seed records")
        if not np.isclose(upper, float(row["one_sided_cp_upper"]), rtol=0, atol=1e-12):
            raise RuntimeError("exact Clopper-Pearson limit does not reproduce")
    all_cells_pass = bool(summary["one_sided_cp_upper"].le(0.05).all())
    no_positive_gain_promotions = bool(np.all(promoted_gains <= 1e-9))
    passed = (
        all_cells_pass
        and no_positive_gain_promotions
        and bool((streams["labels_queried"] <= streams["label_budget"]).all())
    )
    if passed != bool(manifest["inference"]["pass"]):
        raise RuntimeError("manifest pass/fail status does not match independently recomputed gate")
    verification = {
        "status": "passed",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "stream_rows": len(streams),
        "method_cell_strata": len(summary),
        "streams_per_stratum": 1000,
        "pathwise_cap_violations": 0,
        "paired_query_count_mismatches": 0,
        "positive_net_gain_promotions": 0,
        "recomputed_calibration_gate_pass": passed,
        "runner_snapshot_sha256": runner_hash,
        "protocol_sha256": config["protocol_sha256"],
        "all_original_artifacts_verified": True,
    }
    verification_path = OUTPUT / "verification.json"
    verification_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    manifest["independent_verification"] = verification
    manifest["artifacts"]["verification.json"] = sha256(verification_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
