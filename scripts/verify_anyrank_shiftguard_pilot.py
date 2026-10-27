"""Independently verify the saved AnyRank ShiftGuard pilot artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/anyrank_shiftguard_pilot_v2"
EXPECTED_METHODS = {
    "pooled_fixed_mixture",
    "source_validation_fixed_split",
    "target_scout",
    "anyrank_full_information_contextual",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(output: Path) -> dict[str, object]:
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    protocol = ROOT / manifest["protocol"]["path"]
    if _sha256(protocol) != manifest["protocol"]["sha256"]:
        raise RuntimeError("protocol checksum mismatch")
    if manifest["source_hashes"].get("runner_sha256_at_execution") is None:
        raise RuntimeError("execution-time runner hash is missing")
    if manifest["status"] != "invalid_implementation_cost_mapping":
        current_runner_hash = _sha256(ROOT / "scripts/reproduce_anyrank_shiftguard.py")
        if manifest["source_hashes"].get("runner_sha256_current") != current_runner_hash:
            raise RuntimeError("current runner hash mismatch")
        current_verifier_hash = _sha256(Path(__file__).resolve())
        if manifest["source_hashes"].get("verifier_sha256_current") != current_verifier_hash:
            raise RuntimeError("current verifier hash mismatch")

    anyrank_root = ROOT / "tmp/AnyRank-source-audit"
    commit = subprocess.run(
        ["git", "-C", str(anyrank_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if commit != manifest["anyrank_source"]["commit"]:
        raise RuntimeError("AnyRank source commit mismatch")
    for relative, expected_hash in manifest["anyrank_source"]["files"].items():
        if _sha256(anyrank_root / relative) != expected_hash:
            raise RuntimeError(f"AnyRank source checksum mismatch: {relative}")

    files = manifest.get("files", [])
    required_files = {
        "streams.csv",
        "streams.parquet",
        "summary.csv",
        "summary.parquet",
        "results.md",
        "reproduce_anyrank_shiftguard_at_execution.py",
    }
    if not required_files.issubset(files):
        raise RuntimeError("required output artifacts are missing from the manifest")
    for name in files:
        expected = manifest.get("file_sha256", {}).get(name)
        if expected is None or _sha256(output / name) != expected:
            raise RuntimeError(f"output file checksum mismatch: {name}")
    execution_snapshot_hash = _sha256(output / "reproduce_anyrank_shiftguard_at_execution.py")
    if execution_snapshot_hash != manifest["source_hashes"]["runner_sha256_at_execution"]:
        raise RuntimeError("execution-time source snapshot does not match its recorded hash")
    detail = pd.read_csv(output / "streams.csv")
    summary = pd.read_csv(output / "summary.csv")
    expected_seeds = set(range(20_310_000, 20_310_006))
    if set(detail["seed"].astype(int)) != expected_seeds:
        raise RuntimeError("pilot seed block is incomplete or unexpected")
    if set(detail["method"].astype(str)) != EXPECTED_METHODS:
        raise RuntimeError("method set is incomplete or unexpected")
    if len(detail) != 24 or detail.duplicated(["seed", "method"]).any():
        raise RuntimeError("stream table has missing or duplicate rows")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise RuntimeError("a method exceeded the hard label cap")
    if not detail.groupby("seed")["label_budget"].nunique().eq(1).all():
        raise RuntimeError("methods do not share a per-stream label ceiling")
    if not detail.groupby("seed")["labels_queried"].nunique().eq(1).all():
        raise RuntimeError("methods were not charged the same acquired labels")
    if len(summary) != 8 or not summary["streams"].eq(3).all():
        raise RuntimeError("summary does not match the six-stream, two-cell design")

    anyrank = detail.loc[detail["method"].eq("anyrank_full_information_contextual")]
    for encoded in anyrank["anyrank_context_diagnostics"]:
        context_diagnostics = json.loads(encoded)
        if set(context_diagnostics) != {"0", "1"}:
            raise RuntimeError("AnyRank context diagnostics are incomplete")
        if sum(item["pairwise_hypothesis_count"] for item in context_diagnostics.values()) != 24:
            raise RuntimeError("AnyRank did not test the 12 challengers in both contexts")
        if sum(item["queried_events"] for item in context_diagnostics.values()) < 1:
            raise RuntimeError("AnyRank received no queried observations")

    result = {
        "status": "artifact_integrity_verified",
        "methodological_status": manifest["status"],
        "streams": len(detail),
        "seeds": len(expected_seeds),
        "cells": int(detail["cell"].nunique()),
        "methods": sorted(EXPECTED_METHODS),
        "all_methods_zero_promotions": bool(not detail["promoted"].astype(bool).any()),
        "label_cap_respected": bool((detail["labels_queried"] <= detail["label_budget"]).all()),
        "common_query_counts_matched": bool(
            detail.groupby("seed")["labels_queried"].nunique().eq(1).all()
        ),
        "protocol_and_source_hashes": "verified",
        "output_hashes": "verified",
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(verify(args.output), indent=2))


if __name__ == "__main__":
    main()
