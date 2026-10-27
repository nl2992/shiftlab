"""Run the frozen Upworthy headline selection evaluation once on official holdout."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn

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
TRAIN_AUDIT = ROOT / "data/reports/upworthy_exploratory_audit.json"
HOLDOUT_MANIFEST = ROOT / "data/reports/upworthy_holdout_acquisition_manifest.json"
PROTOCOL = ROOT / "papers/shiftguard_unified/upworthy_policy_selection_protocol_v1.md"
OUTPUT = ROOT / "outputs/shiftguard_unified/real_data_development/upworthy_policy_v1"
TRAIN_SHA256 = "8368313b060f4015a0c6fb34e6d788163cee29554144aba9390b14922eb9d8ce"
HOLDOUT_SHA256 = "93832660b831aca16bbe314c60dba4a6815b0a5f9cdded1217671cfbfa5186ea"
PROTOCOL_SHA256 = "a8b6bb74a627674b9b007023bea562991eff78d3a5fa017931e73a146b82715f"
TRAIN_ROWS = 22_666
TRAIN_TESTS = 4_873
HOLDOUT_ROWS = 22_600
HOLDOUT_TESTS = 4_871
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


def load_source(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, usecols=lambda column: column in USECOLS or column == "Problem")


def run() -> dict[str, Any]:
    if OUTPUT.exists():
        raise FileExistsError(f"Refusing to overwrite existing evaluation: {OUTPUT}")
    if not all(
        path.is_file() for path in (TRAIN, HOLDOUT, TRAIN_AUDIT, HOLDOUT_MANIFEST, PROTOCOL)
    ):
        raise FileNotFoundError("A source, source manifest, audit, or frozen protocol is missing")
    train_hash = sha256(TRAIN)
    holdout_hash = sha256(HOLDOUT)
    if train_hash != TRAIN_SHA256 or holdout_hash != HOLDOUT_SHA256:
        raise ValueError("Source checksum differs from the frozen partition")
    train_audit = json.loads(TRAIN_AUDIT.read_text(encoding="utf-8"))
    holdout_manifest = json.loads(HOLDOUT_MANIFEST.read_text(encoding="utf-8"))
    if train_audit["source"]["sha256"] != train_hash:
        raise ValueError("Exploratory acquisition manifest does not match its source")
    if (
        holdout_manifest["sha256"] != holdout_hash
        or not holdout_manifest["data_opened_after_protocol_freeze"]
    ):
        raise ValueError("Holdout acquisition manifest is missing or inconsistent")
    protocol_hash = sha256(PROTOCOL)
    if not PROTOCOL_SHA256 or protocol_hash != PROTOCOL_SHA256:
        raise ValueError("Protocol has changed since the runner was frozen")

    train_raw = load_source(TRAIN)
    holdout_raw = load_source(HOLDOUT)
    if len(train_raw) != TRAIN_ROWS or train_raw["clickability_test_id"].nunique() != TRAIN_TESTS:
        raise ValueError("Exploratory partition rows or test count differ from protocol")
    if (
        len(holdout_raw) != HOLDOUT_ROWS
        or holdout_raw["clickability_test_id"].nunique() != HOLDOUT_TESTS
    ):
        raise ValueError("Holdout partition rows or test count differ from protocol")
    overlap = set(train_raw["clickability_test_id"]) & set(holdout_raw["clickability_test_id"])
    if overlap:
        raise ValueError(f"Source partitions share {len(overlap)} experiment IDs")

    train, train_counts = filter_eligible_tests(train_raw)
    holdout, holdout_counts = filter_eligible_tests(holdout_raw)
    started = datetime.now(UTC)
    policy, cv_scores = tune_and_fit(train)
    predictions = policy.predict(package_text(holdout))
    contrasts = equal_test_contrasts(holdout, predictions)
    bootstrap = week_cluster_bootstrap(contrasts)
    ended = datetime.now(UTC)

    selected_mean = float(contrasts["selected_ctr"].mean())
    uniform_mean = float(contrasts["uniform_reference_ctr"].mean())
    delta = float(contrasts["delta_ctr"].mean())
    total_impressions = contrasts["total_impressions"].to_numpy(dtype="float64")
    impression_weighted_delta = float(
        np.average(contrasts["delta_ctr"].to_numpy(dtype="float64"), weights=total_impressions)
    )
    summary: dict[str, Any] = {
        "schema_version": "1.0.0",
        "status": "completed_frozen_fixed_horizon_holdout_evaluation",
        "created_at_utc": ended.isoformat(),
        "protocol": {
            "path": PROTOCOL.relative_to(ROOT).as_posix(),
            "sha256": protocol_hash,
            "primary_null": "equal-test mean selected-package CTR minus uniform-over-packages CTR <= 0",
            "candidate": "text-only regularized binomial logistic CTR predictor",
            "reference": "uniform random choice over eligible packages within each test",
            "c_grid": [0.01, 0.1, 1.0, 10.0],
            "risk_window_inclusive": ["2013-06-24", "2014-01-11"],
            "bootstrap": bootstrap,
        },
        "source": {
            "dataset": "Upworthy Research Archive",
            "license": "CC BY 4.0",
            "training_partition": {
                "filename": TRAIN.name,
                "sha256": train_hash,
                "raw_rows": len(train_raw),
                "raw_tests": TRAIN_TESTS,
                "eligibility": train_counts,
            },
            "evaluation_partition": {
                "filename": HOLDOUT.name,
                "sha256": holdout_hash,
                "raw_rows": len(holdout_raw),
                "raw_tests": HOLDOUT_TESTS,
                "eligibility": holdout_counts,
                "experiment_id_overlap_with_training": 0,
            },
        },
        "model": {
            "selected_C": policy.c_value,
            "grouped_cv_mean_delta_by_C": cv_scores,
            "features": ["headline", "excerpt"],
            "vectorizer": {
                "ngram_range": [1, 2],
                "min_df": 3,
                "max_features": 50_000,
                "sublinear_tf": True,
            },
            "estimator": "LogisticRegression(solver='liblinear', max_iter=1000, random_state=20261026; sample weights = clicks/non-clicks)",
            "inference_device": "CPU sparse linear model; dense GPU conversion not justified for this small text corpus",
        },
        "results": {
            "eligible_tests": len(contrasts),
            "eligible_arms": int(holdout_counts["eligible_arms"]),
            "equal_test_selected_ctr": selected_mean,
            "equal_test_uniform_ctr": uniform_mean,
            "equal_test_delta_ctr": delta,
            "impression_weighted_delta_ctr": impression_weighted_delta,
            "evaluator_only_best_arm_ctr": float(contrasts["best_arm_ctr_evaluator_only"].mean()),
            "evaluation_impressions": int(total_impressions.sum()),
            "primary_lower_bound_above_zero": bootstrap["delta_one_sided_lower_95"] > 0.0,
        },
        "limitations": [
            "The holdout partition is public and project-relative, not globally secret.",
            "The archive provides aggregate randomized arm outcomes, not impression-level feedback.",
            "The result is fixed-horizon package choice only; no sequential monitoring, delayed feedback, or resource-allocation claim.",
            "CTR is not revenue, welfare, or net business utility.",
            "A date-based exclusion addresses the publisher-reported suspected assignment issue but is not a corrected row-level Problem flag.",
            "Experiment-level transport to future stories is not established by this historical archive.",
        ],
        "runtime": {"started_at_utc": started.isoformat(), "finished_at_utc": ended.isoformat()},
        "software": {"scikit_learn": sklearn.__version__, "pandas": pd.__version__},
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    metrics_path = OUTPUT / "per_test_metrics.csv"
    contrasts.to_csv(metrics_path, index=False)
    summary_path = OUTPUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    report_path = OUTPUT / "report.md"
    report_path.write_text(
        "# Upworthy headline policy selection — frozen holdout\n\n"
        "**Status:** fixed-horizon project-held-out evaluation; aggregate CTR only.\n\n"
        f"Eligible holdout tests: {len(contrasts):,} across {holdout_counts['eligible_arms']:,} package arms.\n\n"
        f"The text-only policy achieved equal-test CTR {selected_mean:.6f}; uniform package choice achieved {uniform_mean:.6f}; paired difference was {delta:+.6f}.\n\n"
        f"The week-clustered 95% interval for the difference was [{bootstrap['delta_ci_95'][0]:+.6f}, {bootstrap['delta_ci_95'][1]:+.6f}], with one-sided 95% lower bound {bootstrap['delta_one_sided_lower_95']:+.6f}.\n\n"
        f"Selected `C`: {policy.c_value:g}. Grouped-CV contrasts by `C`: `{cv_scores}`.\n\n"
        "This does not test online monitoring, delayed labels, intervention costs, or net business utility. See `summary.json` and `per_test_metrics.csv` for aggregate evidence and provenance.\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "1.0.0",
        "protocol_sha256": protocol_hash,
        "runner_sha256": sha256(Path(__file__).resolve()),
        "implementation_sha256": sha256(ROOT / "src/shiftlab/dive/upworthy_policy_selection.py"),
        "training_sha256": train_hash,
        "holdout_sha256": holdout_hash,
        "outputs": {path.name: sha256(path) for path in (metrics_path, summary_path, report_path)},
        "evaluation_tests": len(contrasts),
        "evaluation_arms": int(holdout_counts["eligible_arms"]),
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    main()
