"""Independently verify the matched OPI/MOPE experiment artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/molitor_mope_matched_v1"
METHODS = {
    "opi_anytime",
    "fixed_horizon_policy_selection",
    "official_mope_gate",
    "fixed_horizon_gate",
}
ENDPOINTS = {
    "false_optimal_eliminated_anytime": "false_optimal_eliminated_anytime",
    "false_optimal_excluded_at_horizon": "false_optimal_excluded_at_horizon",
    "unique_stopped": "unique_stops",
    "correct_singleton_at_horizon": "correct_singletons",
    "promoted": "promotions",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def interval(events: int, trials: int) -> tuple[float, float]:
    return (
        0.0 if events == 0 else float(beta.ppf(0.025, events, trials - events + 1)),
        1.0 if events == trials else float(beta.ppf(0.975, events + 1, trials - events)),
    )


def close(actual: Any, expected: float) -> bool:
    return bool(np.isclose(float(actual), expected, rtol=1e-10, atol=1e-12))


def normalize_nulls(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in normalized.columns:
        values = normalized[column].astype(object)
        normalized[column] = values.where(pd.notna(values), None)
    return normalized


def verify() -> dict[str, int]:
    manifest_path = OUTPUT / "manifest.json"
    metrics_path = OUTPUT / "per_stream_metrics.parquet"
    summary_path = OUTPUT / "summary.parquet"
    for path in (manifest_path, metrics_path, summary_path):
        if not path.is_file():
            raise FileNotFoundError(path)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["status"] != "complete":
        raise AssertionError("run manifest is not marked complete")
    config = manifest["configuration"]
    if config["alpha"] != 0.05 or config["horizon"] != 200:
        raise AssertionError("registered alpha/horizon changed")
    if config["null_streams"] != 1000 or config["alternative_streams"] != 300:
        raise AssertionError("registered stream counts changed")
    if manifest["device"] != "cuda" or not manifest["gpu_name"]:
        raise AssertionError("CUDA generation was available but was not recorded")
    if manifest["reference_implementation"]["commit"] != "a4b8584b622f3a8296932568c520c1bb3e1957f0":
        raise AssertionError("MOPE source revision is not the registered commit")

    source_snapshots = manifest.get("source_snapshots", {})
    for relative, expected_hash in manifest["source_sha256"].items():
        snapshot_relative = source_snapshots.get(relative)
        source = OUTPUT / snapshot_relative if snapshot_relative else ROOT / relative
        if not source.is_file() or sha256(source) != expected_hash:
            raise AssertionError(f"source hash mismatch: {relative}")
    for name, expected_hash in manifest["output_sha256"].items():
        path = OUTPUT / name
        if not path.is_file() or sha256(path) != expected_hash:
            raise AssertionError(f"output hash mismatch: {name}")
    for audit_name, audit in manifest.get("followup_audits", {}).items():
        audit_script = ROOT / audit["script"]
        audit_artifact = OUTPUT / audit["artifact"]
        if not audit_script.is_file() or sha256(audit_script) != audit["script_sha256"]:
            raise AssertionError(f"follow-up audit source hash mismatch: {audit_name}")
        if not audit_artifact.is_file() or sha256(audit_artifact) != audit["artifact_sha256"]:
            raise AssertionError(f"follow-up audit artifact hash mismatch: {audit_name}")

    metrics = pd.read_parquet(metrics_path)
    summary = pd.read_parquet(summary_path)
    csv_metrics = pd.read_csv(OUTPUT / "per_stream_metrics.csv")
    csv_summary = pd.read_csv(OUTPUT / "summary.csv")
    pd.testing.assert_frame_equal(
        normalize_nulls(metrics), normalize_nulls(csv_metrics), check_dtype=False
    )
    pd.testing.assert_frame_equal(
        normalize_nulls(summary), normalize_nulls(csv_summary), check_dtype=False
    )

    expected_scenarios = {
        "all_tied_null": int(config["null_streams"]),
        "unique_best_action_1": int(config["alternative_streams"]),
    }
    expected_rows = sum(expected_scenarios.values()) * len(METHODS)
    if len(metrics) != expected_rows or len(summary) != len(expected_scenarios) * len(METHODS):
        raise AssertionError("unexpected per-stream or summary row count")
    if set(metrics["method"].unique()) != METHODS:
        raise AssertionError("method set differs from the frozen protocol")
    if set(metrics["scenario"].unique()) != set(expected_scenarios):
        raise AssertionError("scenario set differs from the frozen protocol")
    if metrics.duplicated(["scenario", "replication_id", "method"]).any():
        raise AssertionError("duplicate scenario/replication/method key")

    for scenario, count in expected_scenarios.items():
        frame = metrics[metrics["scenario"] == scenario]
        if len(frame) != count * len(METHODS):
            raise AssertionError(f"wrong row count for {scenario}")
        if set(frame["replication_id"].astype(int)) != set(range(count)):
            raise AssertionError(f"replication ids are incomplete for {scenario}")
        if frame["stream_sha256"].isna().any():
            raise AssertionError(f"missing stream hash for {scenario}")
        hashes_per_stream = frame.groupby("replication_id")["stream_sha256"].nunique()
        if not hashes_per_stream.eq(1).all():
            raise AssertionError(f"methods did not receive identical streams in {scenario}")
        if frame.groupby("replication_id")["method"].nunique().ne(len(METHODS)).any():
            raise AssertionError(f"incomplete method pairing in {scenario}")

    if not metrics["labels_used"].between(1, int(config["horizon"])).all():
        raise AssertionError("label counts fall outside the registered horizon")
    mope = metrics[metrics["method"] == "official_mope_gate"]
    fixed_gate = metrics[metrics["method"] == "fixed_horizon_gate"]
    if mope["promoted"].isna().any() or fixed_gate["promoted"].isna().any():
        raise AssertionError("candidate-vs-logger gate endpoint is missing")
    if not fixed_gate["labels_used"].eq(int(config["horizon"])).all():
        raise AssertionError("fixed-horizon gate did not use the full horizon")
    null_opi = metrics[
        (metrics["scenario"] == "all_tied_null") & (metrics["method"] == "opi_anytime")
    ]
    if null_opi["false_optimal_eliminated_anytime"].astype(bool).any():
        raise AssertionError("OPI eliminated a true optimum in a null stream")

    # Recompute every aggregate and exact binomial interval from stream rows.
    summary_keys = set(zip(summary["scenario"], summary["method"], strict=True))
    expected_keys = {(scenario, method) for scenario in expected_scenarios for method in METHODS}
    if summary_keys != expected_keys:
        raise AssertionError("summary cell keys are incomplete")
    for row in summary.itertuples(index=False):
        cell = metrics[(metrics["scenario"] == row.scenario) & (metrics["method"] == row.method)]
        if int(row.streams) != len(cell):
            raise AssertionError("summary stream count mismatch")
        if not close(row.mean_labels_used, float(cell["labels_used"].mean())):
            raise AssertionError("summary mean-label count mismatch")
        if int(row.empty_confidence_sets) != int(cell["empty_confidence_set"].fillna(False).sum()):
            raise AssertionError("summary empty-set count mismatch")
        for endpoint, prefix in ENDPOINTS.items():
            values = cell[endpoint].dropna().astype(bool)
            if values.empty:
                continue
            successes, trials = int(values.sum()), len(values)
            lo, hi = interval(successes, trials)
            if int(getattr(row, f"{prefix}_count")) != successes:
                raise AssertionError(f"summary count mismatch: {endpoint}")
            if not close(getattr(row, f"{prefix}_rate"), successes / trials):
                raise AssertionError(f"summary rate mismatch: {endpoint}")
            if not close(getattr(row, f"{prefix}_ci95_low"), lo):
                raise AssertionError(f"summary lower interval mismatch: {endpoint}")
            if not close(getattr(row, f"{prefix}_ci95_high"), hi):
                raise AssertionError(f"summary upper interval mismatch: {endpoint}")

    return {"stream_method_rows": len(metrics), "summary_cells": len(summary)}


if __name__ == "__main__":
    counts = verify()
    print(
        f"Verified {counts['stream_method_rows']:,} paired stream-method rows, "
        f"{counts['summary_cells']} aggregate cells, method pairing, CUDA/source "
        "provenance, exact binomial intervals, and Parquet/CSV hashes."
    )
