"""Independently recompute the Q2 paired-confirmation metrics and hashes."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_confirmation_v1"
)
PROTOCOL = ROOT / "papers/shiftguard_unified/target_scout_fixed_split_confirmation_protocol.md"
CALIBRATION = (
    ROOT
    / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1/manifest.json"
)
METHODS = {"pooled_rank", "fixed_sample_split", "target_scout"}
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 2_026_102_699


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute_contrasts(streams: pd.DataFrame) -> dict[str, dict[str, float]]:
    cells = sorted(streams["scenario"].unique())
    seeds = np.sort(streams["seed"].unique())
    if len(cells) != 18 or len(seeds) != 300:
        raise RuntimeError("confirmation must contain 18 cells and 300 paired seeds")
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    results: dict[str, dict[str, float]] = {}
    for label, comparator in (
        ("target_scout_minus_fixed_sample_split", "fixed_sample_split"),
        ("target_scout_minus_pooled_rank", "pooled_rank"),
    ):
        matrix = np.empty((len(cells), len(seeds)), dtype=float)
        for index, cell in enumerate(cells):
            wide = (
                streams.loc[streams["scenario"].eq(cell)]
                .pivot(index="seed", columns="method", values="expected_postpromotion_net_gain")
                .reindex(index=seeds)
            )
            if wide[list(METHODS)].isna().any().any():
                raise RuntimeError(f"unmatched paired methods in {cell}")
            matrix[index] = wide["target_scout"].to_numpy() - wide[comparator].to_numpy()
        bootstrap = np.empty(BOOTSTRAP_DRAWS, dtype=float)
        for start in range(0, BOOTSTRAP_DRAWS, 100):
            stop = min(BOOTSTRAP_DRAWS, start + 100)
            indices = rng.integers(0, len(seeds), size=(stop - start, len(seeds)))
            bootstrap[start:stop] = np.take(matrix, indices, axis=1).mean(axis=(0, 2))
        low, high = np.quantile(bootstrap, [0.0125, 0.9875])
        results[label] = {
            "mean_paired_difference": float(matrix.mean()),
            "bootstrap_ci_low": float(low),
            "bootstrap_ci_high": float(high),
            "material_benefit_confirmed": bool(low > 1.0),
        }
    return results


def main() -> None:
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected_hash in manifest["artifacts"].items():
        path = OUTPUT / name
        if not path.is_file() or sha256(path) != expected_hash:
            raise RuntimeError(f"artifact hash mismatch: {name}")
    config = manifest["configuration"]
    if sha256(PROTOCOL) != config["protocol_sha256"]:
        raise RuntimeError("frozen confirmation protocol hash mismatch")
    if sha256(CALIBRATION) != manifest["calibration_manifest_sha256"]:
        raise RuntimeError("calibration gate artifact hash mismatch")
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    if not calibration.get("inference", {}).get("pass", False):
        raise RuntimeError("linked calibration no longer passes")
    runner = ROOT / "scripts/confirm_target_scout_fixed_split.py"
    runner_hash = sha256(runner)
    if config["runner_sha256"] != runner_hash:
        raise RuntimeError("confirmation runner hash mismatch")
    if manifest["source_hashes"].get("scripts/confirm_target_scout_fixed_split.py") != runner_hash:
        raise RuntimeError("manifest source hash differs from confirmation runner")

    streams = pd.read_parquet(OUTPUT / "streams.parquet")
    if len(streams) != 16_200 or streams.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("confirmation rows are incomplete or duplicated")
    if set(streams["method"].unique()) != METHODS:
        raise RuntimeError("method set differs from frozen confirmation")
    if not streams["signal"].gt(0).all():
        raise RuntimeError("confirmation contains a zero-signal control")
    counts = streams.groupby(["scenario", "method"]).size()
    if not counts.eq(300).all():
        raise RuntimeError("every positive-signal method/cell needs 300 seeds")
    if (streams["labels_queried"] > streams["label_budget"]).any():
        raise RuntimeError("pathwise label cap violation")
    paired_labels = streams.pivot(
        index=["scenario", "seed"], columns="method", values="labels_queried"
    )
    if paired_labels.nunique(axis=1).ne(1).any():
        raise RuntimeError("paired query counts differ")

    method_summary = streams.groupby("method", as_index=False).agg(
        streams=("seed", "count"),
        promotions=("promoted", "sum"),
        harmful_promotions=("harmful_postpromotion_promotion", "sum"),
        promotion_rate=("promoted", "mean"),
        mean_labels=("labels_queried", "mean"),
        mean_expected_net_gain=("expected_postpromotion_net_gain", "mean"),
        mean_realized_net_gain=("realized_postpromotion_net_gain", "mean"),
    )
    saved_summary = (
        pd.read_parquet(OUTPUT / "method_summary.parquet")
        .sort_values("method")
        .reset_index(drop=True)
    )
    method_summary = method_summary.sort_values("method").reset_index(drop=True)
    if not saved_summary.equals(method_summary):
        raise RuntimeError("method-level summary does not reproduce from stream metrics")
    recorded_summary = sorted(manifest["method_summary"], key=lambda row: row["method"])
    if len(recorded_summary) != len(method_summary):
        raise RuntimeError("manifest method summary is incomplete")
    for record, (_, row) in zip(recorded_summary, method_summary.iterrows(), strict=True):
        for key, value in row.items():
            if isinstance(value, str):
                if record[key] != value:
                    raise RuntimeError("manifest summary method mismatch")
            elif not np.isclose(float(record[key]), float(value), rtol=0, atol=1e-10):
                raise RuntimeError(f"manifest method summary mismatch for {key}")

    recomputed = recompute_contrasts(streams)
    recorded = {row["contrast"]: row for row in manifest["primary_contrasts"]}
    for name, values in recomputed.items():
        for metric, expected in values.items():
            observed = recorded[name][metric]
            if isinstance(expected, bool):
                if bool(observed) != expected:
                    raise RuntimeError(f"confirmation decision mismatch for {name}")
            elif not np.isclose(float(observed), expected, rtol=0, atol=1e-10):
                raise RuntimeError(f"bootstrap contrast mismatch for {name}: {metric}")
    verification = {
        "status": "passed",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "stream_rows": len(streams),
        "positive_signal_cells": 18,
        "seeds_per_method_cell": 300,
        "pathwise_cap_violations": 0,
        "paired_query_count_mismatches": 0,
        "recomputed_primary_contrasts": recomputed,
        "runner_sha256": runner_hash,
        "protocol_sha256": config["protocol_sha256"],
        "calibration_manifest_sha256": manifest["calibration_manifest_sha256"],
        "all_original_artifacts_verified": True,
        "verifier_sha256": sha256(Path(__file__).resolve()),
    }
    verification_path = OUTPUT / "verification.json"
    verification_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    manifest["independent_verification"] = verification
    manifest["artifacts"]["verification.json"] = sha256(verification_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
