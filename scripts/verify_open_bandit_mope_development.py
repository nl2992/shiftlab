"""Independently reconstruct and verify the aggregate OBD/MOPE development run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd
from fast_mope_optimizer import solve_gd_exact

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "data/reports/open_bandit_full_acquisition_manifest.json"
OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/open_bandit_mope_v1"
MOPE_REPO = ROOT / "tmp/mope_reference"
MOPE_COMMIT = "a4b8584b622f3a8296932568c520c1bb3e1957f0"
VALIDATION = (
    ROOT
    / "outputs/shiftguard_unified/sota_reproductions/mope_fast_solver_validation_v2"
    / "reference_qp_and_path_validation.json"
)
PROTOCOL = ROOT / "papers/shiftguard_unified/open_bandit_mope_development_protocol_v1.md"
TRAIN_DATES = {"2019-11-24", "2019-11-25", "2019-11-26"}
EVAL_DATES = {"2019-11-27", "2019-11-28", "2019-11-29", "2019-11-30"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def close(actual: float, expected: float, label: str) -> None:
    if not np.isclose(actual, expected, rtol=0.0, atol=1e-12):
        raise AssertionError(f"{label}: {actual} != {expected}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    summary_path = output / "summary.json"
    daily_path = output / "daily_metrics.csv"
    report_path = output / "report.md"
    manifest_path = output / "manifest.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not report_path.is_file():
        raise AssertionError("Run report is missing")
    acquisition = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    source_info = acquisition["random_all"]
    source_path = ROOT / source_info["parquet_path"]
    if sha256(source_path) != source_info["parquet_sha256"]:
        raise AssertionError("Processed Random/all source hash differs from acquisition manifest")
    if sha256(SOURCE_MANIFEST) != summary["source"]["source_manifest_sha256"]:
        raise AssertionError("Source-manifest hash differs from run summary")
    if sha256(PROTOCOL) != summary["protocol"]["sha256"]:
        raise AssertionError("Protocol hash differs from run summary")

    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    solver_path = Path(__file__).with_name("fast_mope_optimizer.py")
    if (
        validation["status"] != "passed"
        or sha256(solver_path) != validation["fast_solver_file_sha256"]
    ):
        raise AssertionError("Fast optimizer differs from its passing reference validation")
    if sha256(VALIDATION) != summary["method"]["fast_optimizer_validation_sha256"]:
        raise AssertionError("Fast optimizer validation artifact hash differs from run summary")

    frame = pd.read_parquet(
        source_path,
        columns=["timestamp", "item_id", "position", "click", "propensity_score"],
    )
    if len(frame) != int(source_info["rows"]):
        raise AssertionError("Random/all row count differs from its source manifest")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="raise")
    frame = frame.sort_values("timestamp", kind="mergesort", ignore_index=True)
    frame["date_utc"] = frame["timestamp"].dt.strftime("%Y-%m-%d")
    if set(frame["date_utc"].unique()) != TRAIN_DATES | EVAL_DATES:
        raise AssertionError("Observed UTC date window differs from frozen protocol")
    if not np.allclose(frame["propensity_score"].to_numpy(), 1.0 / 80.0, rtol=0.0, atol=1e-12):
        raise AssertionError("Logged Random propensities do not equal 1/80")
    if not np.isin(frame["position"].to_numpy(), [1, 2, 3]).all():
        raise AssertionError("Unexpected display position")
    if not np.isin(frame["click"].to_numpy(), [0, 1]).all():
        raise AssertionError("Unexpected click value")

    train = frame.loc[frame["date_utc"].isin(TRAIN_DATES) & (frame["position"] == 1)]
    evaluation = frame.loc[
        frame["date_utc"].isin(EVAL_DATES) & (frame["position"] == 1)
    ].reset_index(drop=True)
    train_items = train["item_id"].to_numpy(dtype=np.int64)
    train_clicks = train["click"].to_numpy(dtype=np.int64)
    counts = np.bincount(train_items, minlength=80)
    clicks_by_item = np.bincount(train_items, weights=train_clicks, minlength=80)
    if np.any(counts == 0):
        raise AssertionError("A candidate item lacks training support")
    target = int(np.argmax(clicks_by_item / counts))
    if target != summary["training"]["selected_item_id"]:
        raise AssertionError("Independently reconstructed candidate differs from run summary")
    if not np.array_equal(counts, np.asarray(summary["training"]["item_counts"])):
        raise AssertionError("Training action counts differ from run summary")
    if not np.array_equal(clicks_by_item, np.asarray(summary["training"]["item_clicks"])):
        raise AssertionError("Training click counts differ from run summary")

    items = evaluation["item_id"].to_numpy(dtype=np.int64)
    rewards = evaluation["click"].to_numpy(dtype=np.float64)
    weights = (items == target).astype(np.float64) * 80.0
    wr = np.column_stack((weights, rewards))
    scores = weights * rewards - rewards
    if not np.isin(weights, [0.0, 80.0]).all() or not np.isin(rewards, [0.0, 1.0]).all():
        raise AssertionError("Reconstructed score stream is outside the frozen support")

    revision = subprocess.run(
        ["git", "-C", str(MOPE_REPO), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if revision != MOPE_COMMIT or revision != summary["method"]["commit"]:
        raise AssertionError("MOPE source checkout differs from the recorded pinned commit")
    sys.path.insert(0, str(MOPE_REPO))
    # The pinned module imports these optional packages at module scope, but the
    # verifier replaces its QP solver and only needs the published recursion.
    # If the optional acceleration/solver packages are absent, identity/no-op
    # shims preserve the Python/NumPy recursion without changing its equations.
    try:
        tqdm: Any = importlib.import_module("tqdm")
    except ModuleNotFoundError as error:
        if error.name != "tqdm":
            raise
        tqdm = ModuleType("tqdm")
        sys.modules["tqdm"] = tqdm
    tqdm.tqdm = lambda iterable, **_kwargs: iterable

    try:
        importlib.import_module("numba")
    except ModuleNotFoundError as error:
        if error.name != "numba":
            raise
        numba = ModuleType("numba")
        numba.njit = lambda function=None, **_kwargs: (
            (lambda wrapped: wrapped) if function is None else function
        )
        sys.modules["numba"] = numba

    try:
        importlib.import_module("cvxpy")
    except ModuleNotFoundError as error:
        if error.name != "cvxpy":
            raise
        sys.modules["cvxpy"] = ModuleType("cvxpy")

    mope_module: Any = importlib.import_module("opebetrp")
    mope_module.solve_gd = solve_gd_exact
    lower, upper = mope_module.wealth_lb_gd(wr, 0.0, 80.0, 0.05)
    lower = np.asarray(lower, dtype=np.float64)
    upper = np.asarray(upper, dtype=np.float64)
    if lower.shape != (len(evaluation),) or upper.shape != lower.shape:
        raise AssertionError("Recomputed confidence path has an unexpected length")
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise AssertionError("Recomputed confidence path is non-finite")
    if np.any(np.diff(lower) < -1e-9) or np.any(np.diff(upper) > 1e-9):
        raise AssertionError("Recomputed confidence path is not nested")

    empty = np.flatnonzero(lower > upper + 1e-9)
    crossings = np.flatnonzero(lower > 0.0)
    first_empty = int(empty[0]) if empty.size else None
    first_crossing = int(crossings[0]) if crossings.size else None
    result = summary["results"]
    if (first_empty + 1 if first_empty is not None else None) != result[
        "mope_first_empty_set_event"
    ]:
        raise AssertionError("First empty-set event differs from stored summary")
    if (first_crossing + 1 if first_crossing is not None else None) != result[
        "mope_first_lower_crossing_event"
    ]:
        raise AssertionError("First lower-bound crossing differs from stored summary")
    if bool(
        first_crossing is not None and (first_empty is None or first_crossing < first_empty)
    ) != bool(result["mope_promoted_before_empty_set"]):
        raise AssertionError("Promotion decision differs from stored summary")
    close(float(scores.mean()), result["candidate_minus_incumbent_ipw"], "IPW contrast")
    close(
        float(weights.dot(rewards) / len(weights)), result["candidate_ipw_value"], "candidate IPW"
    )
    close(float(rewards.mean()), result["incumbent_observed_click_rate"], "logger click rate")
    close(float(lower[-1]), result["mope_lower_at_horizon"], "MOPE lower horizon")
    close(float(upper[-1]), result["mope_upper_at_horizon"], "MOPE upper horizon")

    fixed_lower = float(scores.mean() - 80.0 * np.sqrt(np.log(1.0 / 0.05) / (2.0 * len(scores))))
    close(fixed_lower, result["fixed_horizon_hoeffding_lower_at_horizon"], "Hoeffding lower")
    if bool(fixed_lower > 0.0) != bool(result["fixed_horizon_hoeffding_promoted"]):
        raise AssertionError("Fixed-horizon decision differs from stored summary")

    with daily_path.open(newline="", encoding="utf-8") as stream:
        daily = list(csv.DictReader(stream))
    if len(daily) != len(EVAL_DATES):
        raise AssertionError("Daily output does not contain exactly four evaluation dates")
    date_values = evaluation["date_utc"].to_numpy()
    for row in daily:
        endpoint = int(row["events_through_day"])
        if date_values[endpoint - 1] != row["date_utc"]:
            raise AssertionError("Stored daily endpoint does not align with evaluation dates")
        close(float(row["mope_lower"]), float(lower[endpoint - 1]), "daily MOPE lower")
        close(float(row["mope_upper"]), float(upper[endpoint - 1]), "daily MOPE upper")
        close(
            float(row["running_value_difference"]), float(scores[:endpoint].mean()), "daily score"
        )

    for filename, expected_hash in manifest["artifacts"].items():
        if sha256(output / filename) != expected_hash:
            raise AssertionError(f"Artifact hash mismatch: {filename}")
    print(
        json.dumps(
            {
                "status": "independently_verified",
                "evaluation_events": len(evaluation),
                "target_item": target,
                "first_empty_set_event": first_empty + 1 if first_empty is not None else None,
                "promotion_before_empty": result["mope_promoted_before_empty_set"],
                "fast_solver_matches_pinned_reference_on_validation_grid": validation["status"],
                "all_recorded_artifact_hashes_match": True,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
