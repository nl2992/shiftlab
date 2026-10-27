"""Independently validate the frozen Timans paired-cost run artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/timans_unknown_shift_paired_cost_v1"
PROTOCOL = ROOT / "papers/shiftguard_unified/timans_unknown_shift_paired_cost_protocol_v1.md"
NULL_SCENARIOS = ("stationary", "benign_nuisance")
ALTERNATIVE_SCENARIOS = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
METHODS = (
    "shiftlab_fixed_stake_mixture",
    "timans_approx_grapa",
    "timans_grapa_grid",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(output: Path = OUTPUT, reference_source: Path | None = None) -> dict[str, Any]:
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "registered_synthetic_comparator_development_complete":
        raise ValueError("manifest does not indicate a completed registered run")
    if manifest["protocol"]["sha256"] != _sha256(PROTOCOL):
        raise ValueError("frozen protocol hash does not match the run manifest")
    for relative, expected in manifest["artifact_sha256"].items():
        if _sha256(output / relative) != expected:
            raise ValueError(f"artifact hash mismatch: {relative}")

    config = manifest["config"]
    null_seeds = int(config["null_seeds_per_scenario"])
    alternative_seeds = int(config["alternative_seeds_per_scenario"])
    start = int(config["null_seed_range_inclusive"][0])
    expected_rows = len(METHODS) * (
        len(NULL_SCENARIOS) * null_seeds + len(ALTERNATIVE_SCENARIOS) * alternative_seeds
    )
    metrics = pd.read_parquet(output / "metrics.parquet")
    summary = pd.read_parquet(output / "summary.parquet")
    paired = pd.read_parquet(output / "paired_detection_comparisons.parquet")
    if len(metrics) != expected_rows or metrics.duplicated(["scenario", "seed", "method"]).any():
        raise ValueError("metric row count or scenario-seed-method uniqueness failed")
    expected_cells: set[tuple[str, int, str]] = set()
    for scenario in NULL_SCENARIOS:
        expected_cells.update(
            (scenario, seed, method)
            for seed in range(start, start + null_seeds)
            for method in METHODS
        )
    alt_start = int(config["alternative_seed_range_inclusive"][0])
    for scenario in ALTERNATIVE_SCENARIOS:
        expected_cells.update(
            (scenario, seed, method)
            for seed in range(alt_start, alt_start + alternative_seeds)
            for method in METHODS
        )
    actual_cells = set(zip(metrics.scenario, metrics.seed.astype(int), metrics.method, strict=True))
    if actual_cells != expected_cells:
        raise ValueError("scenario or seed coverage differs from the registered seed blocks")
    if not metrics.events_processed.eq(config["events_per_stream"]).all():
        raise ValueError("one or more stream rows have an incomplete event horizon")
    if not metrics.generator_device.eq(config["device"]).all():
        raise ValueError("generator device does not match the manifest")
    if metrics.score_lower.min() < -1e-12 or metrics.score_upper.max() > 1 + 1e-12:
        raise ValueError("transformed risk scores left [0, 1]")
    if (metrics.first_crossing_relative.notna() & (metrics.first_crossing_relative < 0)).any():
        raise ValueError("invalid negative alarm time")
    if len(summary) != len(NULL_SCENARIOS + ALTERNATIVE_SCENARIOS) * len(METHODS):
        raise ValueError("summary cell count is incomplete")
    for row in summary.to_dict(orient="records"):
        group = metrics.loc[metrics.scenario.eq(row["scenario"]) & metrics.method.eq(row["method"])]
        is_null = row["scenario"] in NULL_SCENARIOS
        expected_count = (
            int(group.alarm.sum()) if is_null else int(group.post_onset_detection.sum())
        )
        count_key = "alarms" if is_null else "post_onset_detections"
        if int(row[count_key]) != expected_count or int(row["streams"]) != len(group):
            raise ValueError(f"summary count mismatch for {row['scenario']}/{row['method']}")
        if is_null and float(row["simultaneous_cp_upper"]) > 0.05:
            raise ValueError(
                f"familywise null upper bound exceeds alpha for {row['scenario']}/{row['method']}"
            )
    if len(paired) != 12 or paired.holm_adjusted_mcnemar_p.isna().any():
        raise ValueError("paired comparison family is incomplete")
    if reference_source is not None:
        import subprocess

        commit = subprocess.check_output(
            ["git", "-C", str(reference_source), "rev-parse", "HEAD"], text=True
        ).strip()
        if commit != manifest["source"]["commit"]:
            raise ValueError("reference checkout commit differs from the recorded source commit")
        for relative, expected in manifest["source"]["sha256"].items():
            if _sha256(reference_source / relative) != expected:
                raise ValueError(f"reference source hash mismatch: {relative}")
    return {
        "status": "verified",
        "metric_rows": len(metrics),
        "summary_cells": len(summary),
        "paired_comparisons": len(paired),
        "null_false_alarms": int(metrics.loc[metrics.scenario.isin(NULL_SCENARIOS), "alarm"].sum()),
        "protocol_sha256": manifest["protocol"]["sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--reference-source", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.output_dir, args.reference_source), indent=2))


if __name__ == "__main__":
    main()
