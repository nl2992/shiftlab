"""Reconstruct and inspect MOPE confidence paths flagged as empty."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.reproduce_molitor_mope_matched import generate_streams
from scripts.reproduce_mope_gated_null_smoke import load_official_mope

OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1"
MOPE_REPO = ROOT / "tmp/mope_reference"
MOPE_COMMIT = "a4b8584b622f3a8296932568c520c1bb3e1957f0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def call_quietly(function: Any, data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    null_fd = os.open(os.devnull, os.O_WRONLY)
    saved_stdout = os.dup(1)
    try:
        os.dup2(null_fd, 1)
        lower, upper = function(data, 0.0, 2.0, 0.05)
    finally:
        os.dup2(saved_stdout, 1)
        os.close(saved_stdout)
        os.close(null_fd)
    return np.asarray(lower, dtype=np.float64), np.asarray(upper, dtype=np.float64)


def main() -> None:
    metrics = pd.read_parquet(OUTPUT / "per_stream_metrics.parquet")
    flagged = metrics[
        (metrics["scenario"] == "all_tied_null")
        & (metrics["method"] == "official_mope_gate")
        & metrics["empty_confidence_set"]
    ].sort_values("replication_id")
    if flagged.empty:
        raise RuntimeError("No flagged MOPE paths to audit")

    actions_all, rewards_all, hashes = generate_streams(
        scenario="all_tied_null",
        streams=1000,
        seed=101_026,
        mu0=0.5,
        mu1=0.5,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    )
    function, revision = load_official_mope(MOPE_REPO)
    if revision != MOPE_COMMIT:
        raise AssertionError(f"Unexpected MOPE commit: {revision}")

    audits: list[dict[str, object]] = []
    for row in flagged.itertuples(index=False):
        replication_id = int(row.replication_id)
        if hashes[replication_id] != row.stream_sha256:
            raise AssertionError(f"Input stream hash mismatch for replication {replication_id}")
        actions = actions_all[replication_id]
        rewards = rewards_all[replication_id]
        weights = np.where(actions == 1, 2.0, 0.0)
        lower, upper = call_quietly(function, np.column_stack((weights, rewards)))
        if lower.shape != (200,) or upper.shape != (200,):
            raise AssertionError("MOPE returned an unexpected confidence-path shape")
        empty_indices = np.flatnonzero(lower > upper + 1e-10)
        crossing_indices = np.flatnonzero(lower > 0.0)
        promotion_event = int(crossing_indices[0] + 1) if crossing_indices.size else None
        if bool(empty_indices.size) != bool(row.empty_confidence_set):
            raise AssertionError("Reconstructed empty-set flag differs from saved result")
        if bool(crossing_indices.size) != bool(row.promoted):
            raise AssertionError("Reconstructed promotion differs from saved result")
        if int(row.labels_used) != (promotion_event or 200):
            raise AssertionError("Reconstructed label count differs from saved result")
        audits.append(
            {
                "replication_id": replication_id,
                "stream_sha256": hashes[replication_id],
                "promoted": bool(row.promoted),
                "promotion_event": promotion_event,
                "empty_event_count": int(empty_indices.size),
                "first_empty_event": int(empty_indices[0] + 1) if empty_indices.size else None,
                "maximum_lower_minus_upper": float(np.max(lower - upper)),
                "final_lower": float(lower[-1]),
                "final_upper": float(upper[-1]),
            }
        )

    artifact = {
        "source": "reconstructed CUDA null streams from registered seed",
        "mope_commit": revision,
        "alpha": 0.05,
        "horizon": 200,
        "flagged_stream_count": len(audits),
        "audits": audits,
    }
    path = OUTPUT / "mope_empty_confidence_set_audit.json"
    path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(artifact, indent=2))
    print(f"audit_sha256={sha256(path)}")


if __name__ == "__main__":
    main()
