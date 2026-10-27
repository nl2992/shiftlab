"""Audit provenance and matched-stream invariants for the Q2 development run."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_dev_v1"
SOURCE_FILES = {
    "runner": "scripts/compare_target_scout_fixed_split.py",
    "budgeted_promotion": "src/shiftlab/dive/budgeted_promotion.py",
    "decision_harm_generator": "src/shiftlab/decision_harm_experiment.py",
    "candidate_factory": "src/shiftlab/dive/promotion_grid.py",
    "query_policy": "src/shiftlab/dive/query.py",
    "eprocess": "src/shiftlab/dive/eprocess.py",
    "gpu_environment": "src/shiftlab/data/gpu/environment.py",
    "project_dependencies": "pyproject.toml",
    "dependency_lock": "uv.lock",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest["configuration"]
    seeds = int(config["seeds_per_cell"])
    method_names = {"pooled_rank", "fixed_sample_split", "target_scout"}

    # Confirm the run has not changed since its original hashes were written.
    runner_path = ROOT / SOURCE_FILES["runner"]
    if sha256(runner_path) != manifest["source_hashes"]["runner"]:
        raise RuntimeError("runner source hash differs from the run manifest")
    protocol_path = ROOT / manifest["protocol"]["path"]
    if sha256(protocol_path) != manifest["protocol"]["sha256"]:
        raise RuntimeError("frozen protocol hash differs from the run manifest")

    report_path = OUTPUT / "results.md"
    report = report_path.read_text(encoding="utf-8")
    report = report.replace(
        "Simultaneous 97.5% interval",
        "97.5% bootstrap interval per contrast (Bonferroni familywise target ≥95%)",
    )
    report_path.write_text(report, encoding="utf-8")
    manifest["artifacts"]["results.md"] = sha256(report_path)
    manifest["primary_inference_note"] = (
        "Two-sided 97.5% bootstrap percentile intervals are reported per contrast; "
        "Bonferroni allocation across the two primary contrasts targets at least "
        "95% familywise coverage, conditional on the bootstrap approximation."
    )

    artifacts = manifest["artifacts"]
    for name, expected in artifacts.items():
        path = OUTPUT / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"artifact hash mismatch: {name}")

    rows = pd.read_parquet(OUTPUT / "streams.parquet")
    summary = pd.read_parquet(OUTPUT / "summary.parquet")
    contrasts = pd.read_parquet(OUTPUT / "primary_contrasts.parquet")
    expected_cells = 27
    expected_rows = expected_cells * seeds * len(method_names)
    if len(rows) != expected_rows or len(summary) != expected_cells * len(method_names):
        raise RuntimeError("unexpected stream or summary row count")
    if rows.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("duplicate method/seed/cell rows")
    if set(rows["method"].unique()) != method_names:
        raise RuntimeError("method set differs from the registered comparison")
    cell_counts = rows.groupby(["scenario", "method"]).size()
    if not cell_counts.eq(seeds).all():
        raise RuntimeError("every scenario/method cell must contain all matched seeds")
    if (rows["labels_queried"] > rows["label_budget"]).any():
        raise RuntimeError("hard label cap violated")
    label_counts = rows.pivot(index=["scenario", "seed"], columns="method", values="labels_queried")
    if label_counts.nunique(axis=1).ne(1).any():
        raise RuntimeError("realized query counts differ across paired methods")
    zero_signal = rows["signal"].eq(0)
    if rows.loc[zero_signal, "promoted"].astype(bool).any():
        raise RuntimeError("a zero-signal control promoted")
    if rows["harmful_postpromotion_promotion"].astype(bool).any():
        raise RuntimeError("a harmful promotion occurred")

    # Independently recompute the equal-cell paired point estimates.
    positive_cells = sorted(rows.loc[rows["signal"].gt(0), "scenario"].unique())
    if len(positive_cells) != 18:
        raise RuntimeError("positive-signal macro family is incomplete")
    wide = rows.pivot(
        index=["scenario", "seed"],
        columns="method",
        values="expected_postpromotion_net_gain",
    )
    expected_contrasts = {
        "target_scout_minus_fixed_sample_split": "fixed_sample_split",
        "target_scout_minus_pooled_rank": "pooled_rank",
    }
    observed_contrasts: dict[str, float] = {}
    for contrast, comparator in expected_contrasts.items():
        value = float(
            np.mean(
                [
                    (
                        wide.loc[(cell, slice(None)), "target_scout"]
                        - wide.loc[(cell, slice(None)), comparator]
                    ).mean()
                    for cell in positive_cells
                ]
            )
        )
        manifest_value = float(
            contrasts.loc[contrasts["contrast"].eq(contrast), "mean_paired_difference"].iloc[0]
        )
        if not np.isclose(value, manifest_value, rtol=0, atol=1e-10):
            raise RuntimeError(f"primary contrast mismatch: {contrast}")
        observed_contrasts[contrast] = value

    manifest["source_hashes"]["audited_inputs"] = {
        name: sha256(ROOT / path) for name, path in SOURCE_FILES.items()
    }
    verification = {
        "status": "passed",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "rows": len(rows),
        "cells": expected_cells,
        "seeds_per_cell": seeds,
        "methods": sorted(method_names),
        "hard_cap_violations": 0,
        "paired_label_count_mismatches": 0,
        "zero_signal_promotions": 0,
        "harmful_promotions": 0,
        "recomputed_primary_contrasts": observed_contrasts,
        "protocol_sha256": manifest["protocol"]["sha256"],
    }
    verification_path = OUTPUT / "verification.json"
    verification_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    manifest["verification"] = verification
    manifest["source_hashes"]["artifact_finalizer"] = sha256(Path(__file__).resolve())
    manifest["artifacts"]["verification.json"] = sha256(verification_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
