"""Exploratory CUVET-style policy development on sampled train-only rows.

Reads bounded byte ranges from the pinned CUVET-policy training CSV, fits
quantile-tree adaptations on is_val=0 rows, and reports IPW estimates on
is_val=1 rows. The validation rows are used for model selection and scoring,
so these results are development evidence only. The official test is never
requested by this script, and raw records are not written to disk.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import subprocess
import time
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from shiftlab.dive.cuvet import CuvetQuantileTree

REPO_ID = "anonadata/CUVET-policy"
REVISION = "36583ac60379ed83fd375c84d2bf8ce1c73869c1"
TRAIN_FILE = "cuvet_policy_train.csv"
TRAIN_BYTES = 10_317_675_360
TRAIN_OID = "f3700741375c68a267de6ed8eae6b05652766ec8"
BASE_URL = f"https://huggingface.co/datasets/{REPO_ID}/resolve/{REVISION}/{TRAIN_FILE}"
RANGE_BYTES = 1024 * 1024
RANGE_COUNT = 128
SEED = 20261026
ARMS = np.asarray([0.8, 0.9, 1.0, 1.1, 1.2], dtype=np.float64)
FEATURES = ["f0", "f1", "f2", "f3", "f4"]
HEADER = ["", "f3", "f0", "f1", "f4", "f2", "policy", "spend", "value", "is_val"]
REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "data" / "reports" / "cuvet_policy_sample_development.json"


def source_sample() -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    request = urllib.request.Request(
        BASE_URL, method="HEAD", headers={"User-Agent": "ShiftLab-CUVET-dev/1.0"}
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        actual_size = int(response.headers.get("Content-Length", "0"))
        etag = response.headers.get("ETag")
    if actual_size != TRAIN_BYTES:
        raise RuntimeError(f"Pinned train size mismatch: {actual_size} != {TRAIN_BYTES}")

    rng = random.Random(SEED)
    offsets: set[int] = set()
    while len(offsets) < RANGE_COUNT:
        offsets.add(rng.randrange(1, actual_size - RANGE_BYTES))

    records: dict[str, list[Any]] = {
        "features": [],
        "arms": [],
        "values": [],
        "costs": [],
        "is_val": [],
        "range": [],
    }
    outcome_sign_counts = {
        outcome: {"negative": 0, "zero": 0, "positive": 0} for outcome in ("value", "spend")
    }
    malformed = 0
    started = time.monotonic()
    for group, offset in enumerate(sorted(offsets)):
        range_request = urllib.request.Request(
            BASE_URL,
            headers={
                "Accept-Encoding": "identity",
                "Range": f"bytes={offset}-{offset + RANGE_BYTES - 1}",
                "User-Agent": "ShiftLab-CUVET-dev/1.0",
            },
        )
        with urllib.request.urlopen(range_request, timeout=60) as response:
            if response.status != 206:
                raise RuntimeError(f"Expected HTTP 206, got {response.status}")
            chunk = response.read(RANGE_BYTES)
        lines = chunk.split(b"\n")
        if len(lines) < 3:
            malformed += 1
            continue
        text = b"\n".join(lines[1:-1]).decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text, newline=""))
        for row in reader:
            if not row:
                continue
            if len(row) != len(HEADER):
                malformed += 1
                continue
            try:
                feature = [float(row[HEADER.index(key)]) for key in FEATURES]
                alpha = float(row[HEADER.index("policy")])
                value = float(row[HEADER.index("value")])
                cost = float(row[HEADER.index("spend")])
                is_val = int(row[HEADER.index("is_val")])
            except (ValueError, IndexError):
                malformed += 1
                continue
            if not np.isfinite(feature).all() or alpha not in ARMS or is_val not in (0, 1):
                malformed += 1
                continue
            for name, observation in (("value", value), ("spend", cost)):
                sign = "negative" if observation < 0 else "positive" if observation > 0 else "zero"
                outcome_sign_counts[name][sign] += 1
            records["features"].append(feature)
            records["arms"].append(alpha)
            records["values"].append(value)
            records["costs"].append(cost)
            records["is_val"].append(is_val)
            records["range"].append(group)
        if (group + 1) % 32 == 0:
            print(
                json.dumps(
                    {
                        "stage": "bounded_train_sample",
                        "ranges_read": group + 1,
                        "rows_in_memory": len(records["arms"]),
                        "elapsed_seconds": round(time.monotonic() - started, 1),
                    }
                ),
                flush=True,
            )

    arrays = {
        "features": np.asarray(records["features"], dtype=np.float64),
        "arms": np.asarray(records["arms"], dtype=np.float64),
        "values": np.asarray(records["values"], dtype=np.float64),
        "costs": np.asarray(records["costs"], dtype=np.float64),
        "is_val": np.asarray(records["is_val"], dtype=np.int8),
        "range": np.asarray(records["range"], dtype=np.int16),
    }
    provenance = {
        "source_revision": REVISION,
        "train_file": TRAIN_FILE,
        "train_file_bytes": actual_size,
        "train_git_oid": TRAIN_OID,
        "etag": etag,
        "ranges_read": len(offsets),
        "range_bytes": RANGE_BYTES,
        "bytes_read_upper_bound": len(offsets) * RANGE_BYTES,
        "rows_sampled": len(arrays["arms"]),
        "malformed_or_boundary_rows_skipped": malformed,
        "sampled_outcome_sign_counts": outcome_sign_counts,
        "range_selection_seed": SEED,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "raw_rows_persisted": False,
        "official_test_requested": False,
        "source_rows_sorted_or_used_as_predictors": False,
    }
    return arrays, provenance


def policy_ipw(
    assigned: np.ndarray,
    outcome: np.ndarray,
    target: np.ndarray,
    propensities: np.ndarray,
) -> np.ndarray:
    arm_indices = np.abs(target[:, None] - ARMS[None, :]).argmin(axis=1)
    observed = np.abs(assigned[:, None] - ARMS[None, :]).argmin(axis=1)
    selected = observed == arm_indices
    return selected * outcome / propensities[arm_indices]


def block_bootstrap_difference(
    contributions: np.ndarray,
    groups: np.ndarray,
    *,
    seed: int,
    replications: int = 500,
) -> dict[str, float]:
    unique_groups = np.unique(groups)
    if len(unique_groups) < 10:
        raise ValueError("Need at least ten disjoint byte ranges for block resampling")
    sums = np.asarray([contributions[groups == group].sum() for group in unique_groups])
    counts = np.asarray([(groups == group).sum() for group in unique_groups])
    rng = np.random.default_rng(seed)
    estimates = np.empty(replications, dtype=np.float64)
    for index in range(replications):
        selected = rng.integers(0, len(unique_groups), size=len(unique_groups))
        estimates[index] = sums[selected].sum() / counts[selected].sum()
    return {
        "lower_95_percentile": float(np.quantile(estimates, 0.025)),
        "upper_95_percentile": float(np.quantile(estimates, 0.975)),
        "upper_95_one_sided_percentile": float(np.quantile(estimates, 0.95)),
        "bootstrap_replications": replications,
        "byte_range_clusters": len(unique_groups),
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    arrays, provenance = source_sample()
    fit_mask = arrays["is_val"] == 0
    validation_mask = arrays["is_val"] == 1
    if fit_mask.sum() < 10_000 or validation_mask.sum() < 2_000:
        raise RuntimeError("Sample too small for train/validation development")

    fit_arms = arrays["arms"][fit_mask]
    counts = np.bincount(
        np.abs(fit_arms[:, None] - ARMS[None, :]).argmin(axis=1), minlength=len(ARMS)
    )
    propensities = counts / counts.sum()
    fit_values = arrays["values"][fit_mask]
    fit_costs = arrays["costs"][fit_mask]
    arm_mean_diagnostics: dict[str, Any] = {}
    mean_values = np.empty(len(ARMS), dtype=np.float64)
    mean_costs = np.empty(len(ARMS), dtype=np.float64)
    for arm_index, arm in enumerate(ARMS):
        selected = fit_arms == arm
        mean_values[arm_index] = fit_values[selected].mean()
        mean_costs[arm_index] = fit_costs[selected].mean()
        arm_mean_diagnostics[str(arm)] = {
            "n": int(selected.sum()),
            "mean_value": float(mean_values[arm_index]),
            "mean_spend": float(mean_costs[arm_index]),
        }
    if np.all(mean_values > 0) and np.all(mean_costs > 0):
        gamma, value_intercept = np.polyfit(np.log(ARMS), np.log(mean_values), deg=1)
        eta, cost_intercept = np.polyfit(np.log(ARMS), np.log(mean_costs), deg=1)
        arm_mean_diagnostics["power_law_fit"] = {
            "value_elasticity_gamma": float(gamma),
            "cost_elasticity_eta": float(eta),
            "reference_mean_value": float(np.exp(value_intercept)),
            "reference_mean_spend": float(np.exp(cost_intercept)),
            "source_assumptions_hold_at_root": bool(gamma > 0 and eta > gamma),
        }
    else:
        arm_mean_diagnostics["power_law_fit"] = {
            "source_assumptions_hold_at_root": False,
            "reason": "at least one treatment-arm mean is nonpositive",
        }
    val_arms = arrays["arms"][validation_mask]
    val_values = arrays["values"][validation_mask]
    val_costs = arrays["costs"][validation_mask]
    val_groups = arrays["range"][validation_mask]
    ref_target = np.full(len(val_arms), 1.0)
    ref_value = policy_ipw(val_arms, val_values, ref_target, propensities)
    ref_cost = policy_ipw(val_arms, val_costs, ref_target, propensities)

    results: list[dict[str, Any]] = []
    for depth in (0, 1, 2, 3):
        candidate_started = time.monotonic()
        try:
            tree = CuvetQuantileTree(
                max_depth=depth,
                candidate_count=8,
                min_samples_leaf=10_000,
                min_samples_per_arm=50,
                alpha_bounds=(0.8, 1.2),
            ).fit(
                arrays["features"][fit_mask],
                fit_arms,
                fit_values,
                fit_costs,
            )
        except ValueError as error:
            results.append(
                {
                    "candidate": f"quantile_cuvet_clipped_depth_{depth}",
                    "status": "not_fit",
                    "reason": str(error),
                }
            )
            print(
                json.dumps(
                    {
                        "stage": "candidate_rejected",
                        "depth": depth,
                        "reason": str(error),
                        "elapsed_seconds": round(time.monotonic() - candidate_started, 1),
                    }
                ),
                flush=True,
            )
            continue
        predicted_continuous = tree.predict(arrays["features"][validation_mask])
        predicted_arms = ARMS[np.abs(predicted_continuous[:, None] - ARMS[None, :]).argmin(axis=1)]
        value_contribution = policy_ipw(val_arms, val_values, predicted_arms, propensities)
        cost_contribution = policy_ipw(val_arms, val_costs, predicted_arms, propensities)
        value_delta = value_contribution - ref_value
        cost_delta = cost_contribution - ref_cost
        results.append(
            {
                "candidate": f"quantile_cuvet_clipped_depth_{depth}",
                "depth_limit": depth,
                "leaf_count": int(np.unique(predicted_continuous).size),
                "selected_arm_shares": {
                    str(arm): float(np.mean(predicted_arms == arm)) for arm in ARMS
                },
                "ipw_estimated_value_per_row": float(value_contribution.mean()),
                "ipw_estimated_spend_per_row": float(cost_contribution.mean()),
                "value_uplift_vs_reference": float(value_delta.mean() / ref_value.mean()),
                "spend_difference_per_row_vs_reference": float(cost_delta.mean()),
                "spend_uplift_vs_reference": float(cost_delta.mean() / ref_cost.mean()),
                "value_difference_block_bootstrap": block_bootstrap_difference(
                    value_delta, val_groups, seed=SEED + depth
                ),
                "spend_difference_block_bootstrap": block_bootstrap_difference(
                    cost_delta, val_groups, seed=SEED + 100 + depth
                ),
            }
        )
        print(
            json.dumps(
                {
                    "stage": "candidate_scored",
                    "depth": depth,
                    "selected_actions": int(np.unique(predicted_arms).size),
                    "elapsed_seconds": round(time.monotonic() - candidate_started, 1),
                }
            ),
            flush=True,
        )

    output = {
        "audit": "exploratory_cuvet_quantile_tree_train_sample",
        "created_utc": datetime.now(UTC).isoformat(),
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "script_sha256": sha256(Path(__file__).resolve()),
        "source": provenance,
        "information_contract": {
            "fit_rows": int(fit_mask.sum()),
            "validation_rows": int(validation_mask.sum()),
            "fit_split": "is_val=0 only",
            "validation_split": "is_val=1; used for both candidate reporting and selection, so development-only",
            "predictors": FEATURES,
            "outcomes": ["value", "spend"],
            "propensity": "empirical arm shares in sampled is_val=0 rows; working assumption, not documented design probabilities",
            "policy_support": "continuous CUVET-style predictions rounded to nearest randomized arm",
            "official_test_requested": False,
            "raw_rows_persisted": False,
        },
        "sampled_train_propensities": {
            str(arm): float(propensities[index]) for index, arm in enumerate(ARMS)
        },
        "arm_mean_response_diagnostics": arm_mean_diagnostics,
        "reference": {
            "arm": 1.0,
            "ipw_estimated_value_per_row": float(ref_value.mean()),
            "ipw_estimated_spend_per_row": float(ref_cost.mean()),
        },
        "candidates": results,
        "limitations": [
            "The quantile split generator and arm-mean elasticity fit are ShiftLab adaptation choices, not a paper reproduction.",
            "Train validation data are sampled from byte ranges and the same validation rows report/select candidates; no confirmatory claim is allowed.",
            "Exact assignment probabilities and the assignment mechanism are undocumented; IPW values are conditional on the stated working propensity assumption.",
            "Byte-range cluster bootstrap intervals are exploratory and depend on sampled blocks representing independent source regions.",
            "The official test split was not requested or accessed.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"output": str(OUTPUT), "rows": provenance["rows_sampled"], "candidates": len(results)}
        )
    )


if __name__ == "__main__":
    main()
