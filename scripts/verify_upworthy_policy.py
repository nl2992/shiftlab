"""Independently reconstruct the frozen Upworthy holdout policy metrics and artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from shiftlab.dive.upworthy_policy_selection import (
    equal_test_contrasts,
    filter_eligible_tests,
    package_text,
    tune_and_fit,
    week_cluster_bootstrap,
)

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data/raw/upworthy/upworthy-archive-exploratory-packages-03.12.2020.csv"
HOLDOUT = ROOT / "data/raw/upworthy/upworthy-archive-holdout-packages-03.12.2020.csv"
PROTOCOL = ROOT / "papers/shiftguard_unified/upworthy_policy_selection_protocol_v1.md"
RUNNER = ROOT / "scripts/evaluate_upworthy_policy.py"
IMPLEMENTATION = ROOT / "src/shiftlab/dive/upworthy_policy_selection.py"
OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/upworthy_policy_v1"
VERIFICATION = OUTPUT / "independent_verification.json"
TRAIN_SHA256 = "8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce"
HOLDOUT_SHA256 = "93832660b831aca16bbe314c60dba4a6815b0a5f9cdded1217671cfbfa5186ea"
USECOLS = {
    "created_at",
    "clickability_test_id",
    "headline",
    "excerpt",
    "impressions",
    "clicks",
    "test_week",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, usecols=lambda column: column in USECOLS or column == "Problem")


def _close(left: float, right: float, *, atol: float = 1e-12) -> bool:
    return bool(np.isclose(left, right, rtol=0.0, atol=atol))


def verify() -> dict[str, Any]:
    if not OUTPUT.is_dir() or VERIFICATION.exists():
        raise FileExistsError("Evaluation output is absent or already independently verified")
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((OUTPUT / "summary.json").read_text(encoding="utf-8"))
    saved = pd.read_csv(OUTPUT / "per_test_metrics.csv", dtype={"clickability_test_id": str})

    source_hashes = {"training": sha256(TRAIN), "holdout": sha256(HOLDOUT)}
    if source_hashes != {"training": TRAIN_SHA256, "holdout": HOLDOUT_SHA256}:
        raise ValueError("Input data hashes differ from the frozen source versions")
    code_hashes = {
        "protocol": sha256(PROTOCOL),
        "runner": sha256(RUNNER),
        "implementation": sha256(IMPLEMENTATION),
    }
    if (
        code_hashes["protocol"] != manifest["protocol_sha256"]
        or code_hashes["runner"] != manifest["runner_sha256"]
        or code_hashes["implementation"] != manifest["implementation_sha256"]
    ):
        raise ValueError("Protocol or implementation source hash mismatch")
    for name, digest in manifest["outputs"].items():
        if sha256(OUTPUT / name) != digest:
            raise ValueError(f"Output checksum mismatch: {name}")

    train_raw = _read(TRAIN)
    holdout_raw = _read(HOLDOUT)
    train, train_counts = filter_eligible_tests(train_raw)
    holdout, holdout_counts = filter_eligible_tests(holdout_raw)
    if set(train_raw["clickability_test_id"]) & set(holdout_raw["clickability_test_id"]):
        raise ValueError("Training and evaluation experiment IDs overlap")
    policy, cv_scores = tune_and_fit(train)
    predictions = policy.predict(package_text(holdout))
    rebuilt = equal_test_contrasts(holdout, predictions)

    if len(saved) != len(rebuilt) or manifest["evaluation_tests"] != len(rebuilt):
        raise ValueError("Per-test metric count does not match the independent reconstruction")
    if (
        saved["clickability_test_id"].astype(str).tolist()
        != rebuilt["clickability_test_id"].astype(str).tolist()
    ):
        raise ValueError("Per-test experiment order or IDs do not match")
    numeric_columns = [
        "test_week",
        "selected_ctr",
        "uniform_reference_ctr",
        "delta_ctr",
        "total_impressions",
        "selected_impressions",
        "n_arms",
        "best_arm_ctr_evaluator_only",
    ]
    for column in numeric_columns:
        left = pd.to_numeric(saved[column], errors="raise").to_numpy(dtype=np.float64)
        right = pd.to_numeric(rebuilt[column], errors="raise").to_numpy(dtype=np.float64)
        if not np.allclose(left, right, rtol=0.0, atol=1e-12):
            raise ValueError(f"Per-test reconstruction mismatch: {column}")

    results = summary["results"]
    expected_scalars = {
        "eligible_tests": len(rebuilt),
        "eligible_arms": holdout_counts["eligible_arms"],
        "equal_test_selected_ctr": float(rebuilt["selected_ctr"].mean()),
        "equal_test_uniform_ctr": float(rebuilt["uniform_reference_ctr"].mean()),
        "equal_test_delta_ctr": float(rebuilt["delta_ctr"].mean()),
        "evaluator_only_best_arm_ctr": float(rebuilt["best_arm_ctr_evaluator_only"].mean()),
        "evaluation_impressions": int(rebuilt["total_impressions"].sum()),
    }
    for key, expected in expected_scalars.items():
        actual = results[key]
        if isinstance(expected, float):
            if not _close(float(actual), expected):
                raise ValueError(f"Summary reconstruction mismatch: {key}")
        elif actual != expected:
            raise ValueError(f"Summary reconstruction mismatch: {key}")
    weighted_delta = float(
        np.average(
            rebuilt["delta_ctr"].to_numpy(dtype=np.float64),
            weights=rebuilt["total_impressions"].to_numpy(dtype=np.float64),
        )
    )
    if not _close(float(results["impression_weighted_delta_ctr"]), weighted_delta):
        raise ValueError("Impression-weighted contrast mismatch")
    if policy.c_value != summary["model"]["selected_C"]:
        raise ValueError("Selected regularization parameter mismatch")
    if cv_scores != summary["model"]["grouped_cv_mean_delta_by_C"]:
        raise ValueError("Grouped-CV scores mismatch")
    bootstrap = week_cluster_bootstrap(rebuilt)
    if bootstrap != summary["protocol"]["bootstrap"]:
        raise ValueError("Bootstrap intervals do not reconstruct exactly")
    if train_counts != summary["source"]["training_partition"]["eligibility"]:
        raise ValueError("Training exclusion counts mismatch")
    if holdout_counts != summary["source"]["evaluation_partition"]["eligibility"]:
        raise ValueError("Holdout exclusion counts mismatch")

    verification = {
        "status": "passed_independent_full_reconstruction",
        "source_sha256": source_hashes,
        "source_code_sha256": code_hashes,
        "output_sha256": {name: sha256(OUTPUT / name) for name in manifest["outputs"]},
        "reconstructed_training_tests": train_counts["eligible_tests"],
        "reconstructed_evaluation_tests": holdout_counts["eligible_tests"],
        "reconstructed_evaluation_arms": holdout_counts["eligible_arms"],
        "reconstructed_delta_ctr": float(rebuilt["delta_ctr"].mean()),
        "reconstructed_bootstrap": bootstrap,
        "verifier_scope": "separate process reran training, policy selection, per-test value, and bootstrap using hash-pinned shared implementation; no holdout tuning",
    }
    VERIFICATION.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    return verification


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
