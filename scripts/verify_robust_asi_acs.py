"""Independently verify Robust ASI ACS run shape, metrics, budgets, and hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_METHODS = {"uniform", "active", "robust_active"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(run_dir: Path) -> dict[str, Any]:
    manifest_path = run_dir / "manifest.json"
    trial_path = run_dir / "robust_asi_acs_trials.parquet"
    summary_path = run_dir / "robust_asi_acs_summary.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "reproduction_run_single_sample_monte_carlo":
        raise ValueError("manifest is not a completed reproduction run")
    trials = pd.read_parquet(trial_path)
    stored_summary = pd.read_csv(summary_path)
    expected_trial_count = (
        len(manifest["configuration"]["budget_rates"])
        * len(EXPECTED_METHODS)
        * manifest["configuration"]["evaluation_trials"]
    )
    if len(trials) != expected_trial_count:
        raise ValueError(f"expected {expected_trial_count} trial rows, got {len(trials)}")
    if set(trials["method"].unique()) != EXPECTED_METHODS:
        raise ValueError("method set differs from the frozen three-arm comparison")
    group_sizes = trials.groupby(["budget_index", "method"], observed=True).size()
    if not (group_sizes == manifest["configuration"]["evaluation_trials"]).all():
        raise ValueError("one or more budget-method groups have incomplete trial counts")
    numeric = [
        "estimate",
        "standard_error",
        "ci_lower",
        "ci_upper",
        "true_theta",
        "expected_pool_labels",
        "labels_queried",
        "min_propensity",
        "max_propensity",
    ]
    if not np.isfinite(trials[numeric].to_numpy(dtype=float)).all():
        raise ValueError("non-finite value found in a primary metric or propensity summary")
    if (trials["min_propensity"] <= 0).any() or (trials["max_propensity"] > 1).any():
        raise ValueError("propensity support constraints were violated")

    budget_checks: list[dict[str, Any]] = []
    for budget_index, budget_group in trials.groupby("budget_index", observed=True):
        expected_values = budget_group["expected_pool_labels"].to_numpy(dtype=float)
        if not np.allclose(expected_values, expected_values[0], rtol=0, atol=1e-8):
            raise ValueError(f"expected spend differs among methods at budget {budget_index}")
        expected_budget = float(expected_values[0])
        requested = int(budget_group["budget_requested"].iloc[0])
        if not np.isclose(expected_budget, requested, rtol=0, atol=1e-8):
            raise ValueError(f"expected query budget mismatch at budget {budget_index}")
        budget_checks.append(
            {
                "budget_index": int(budget_index),
                "expected_pool_labels": expected_budget,
                "requested_pool_labels": requested,
                "max_realized_over_budget": int(budget_group["labels_queried"].max()),
            }
        )

    computed = (
        trials.assign(
            error=trials["estimate"] - trials["true_theta"],
            interval_width=trials["ci_upper"] - trials["ci_lower"],
        )
        .groupby(["budget_index", "method"], observed=True)
        .agg(
            bias=("error", "mean"),
            rmse=("error", lambda x: float(np.sqrt(np.mean(np.square(x))))),
            empirical_90_coverage=("covered", "mean"),
            mean_interval_width=("interval_width", "mean"),
            mean_expected_pool_labels=("expected_pool_labels", "mean"),
            mean_realized_pool_labels=("labels_queried", "mean"),
        )
        .reset_index()
    )
    stored_cols = [
        "budget_index",
        "method",
        "bias",
        "rmse",
        "empirical_90_coverage",
        "mean_interval_width",
        "mean_expected_pool_labels",
        "mean_realized_pool_labels",
    ]
    merged = computed.merge(
        stored_summary[stored_cols],
        on=["budget_index", "method"],
        suffixes=("_computed", "_stored"),
        validate="one_to_one",
    )
    metric_names = stored_cols[2:]
    max_metric_diff = {}
    for name in metric_names:
        difference = np.max(np.abs(merged[f"{name}_computed"] - merged[f"{name}_stored"]))
        max_metric_diff[name] = float(difference)
        if difference > 1e-9:
            raise ValueError(f"stored summary does not reproduce for {name}: {difference}")

    paired = trials.pivot(index=["budget_index", "trial"], columns="method", values="estimate")
    mean_rmse = (
        trials.assign(error=trials["estimate"] - trials["true_theta"])
        .groupby(["budget_index", "method"], observed=True)["error"]
        .apply(lambda x: float(np.sqrt(np.mean(np.square(x)))))
        .unstack()
    )
    propensity_ranges = trials.groupby(["budget_index", "method"], observed=True).agg(
        min_q=("min_propensity", "first"), max_q=("max_propensity", "first")
    )
    if not (
        propensity_ranges.loc[(slice(None), "active"), "max_q"].to_numpy()
        > propensity_ranges.loc[(slice(None), "active"), "min_q"].to_numpy()
    ).all():
        raise ValueError("active allocation collapsed to uniform at one or more budgets")

    source_checks = {}
    for rel_path, expected in manifest["source_sha256"].items():
        path = ROOT / Path(rel_path.replace("\\", "/"))
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"source hash mismatch for {rel_path}")
        source_checks[rel_path] = actual
    artifact_checks = {}
    for rel_path, expected in manifest["artifacts_sha256"].items():
        actual = sha256(run_dir / rel_path)
        if actual != expected:
            raise ValueError(f"artifact hash mismatch for {rel_path}")
        artifact_checks[rel_path] = actual
    data_path = ROOT / Path(manifest["data"]["path"])
    if sha256(data_path) != manifest["data"]["sha256"]:
        raise ValueError("source data hash does not match run manifest")
    receipt = json.loads(
        data_path.with_suffix(data_path.suffix + ".receipt.json").read_text(encoding="utf-8")
    )
    if receipt.get("sha256") != manifest["data"]["sha256"]:
        raise ValueError("source receipt digest does not match source data")

    paired_differences = {
        "active_minus_uniform_rmse_by_budget": {
            str(int(i)): float(mean_rmse.loc[i, "active"] - mean_rmse.loc[i, "uniform"])
            for i in mean_rmse.index
        },
        "robust_minus_uniform_rmse_by_budget": {
            str(int(i)): float(mean_rmse.loc[i, "robust_active"] - mean_rmse.loc[i, "uniform"])
            for i in mean_rmse.index
        },
        "max_abs_paired_estimate_difference_active_vs_uniform": float(
            np.max(np.abs(paired["active"] - paired["uniform"]))
        ),
        "max_abs_paired_estimate_difference_robust_vs_uniform": float(
            np.max(np.abs(paired["robust_active"] - paired["uniform"]))
        ),
    }
    return {
        "status": "passed",
        "run_dir": str(run_dir.relative_to(ROOT)),
        "trial_rows": len(trials),
        "budget_method_groups": len(group_sizes),
        "budget_checks": budget_checks,
        "summary_max_absolute_recomputation_differences": max_metric_diff,
        "paired_method_differences": paired_differences,
        "source_sha256_verified": source_checks,
        "artifact_sha256_verified": artifact_checks,
        "data_sha256_verified": manifest["data"]["sha256"],
        "active_allocation_nonuniform_every_budget": True,
        "limitations": [
            "Repeated query trials condition on one seeded 20,000-record sample and are not independent dataset replications.",
            "Empirical sandwich interval coverage is descriptive and is not a finite-sample guarantee.",
            "The reproduction is fixed-horizon and does not establish sequential or intervention guarantees.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/shiftguard_unified/sota_reproductions/robust_asi_acs_v2",
    )
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    result = verify(run_dir)
    target = run_dir / "verification.json"
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"verified {result['trial_rows']} trials; wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
