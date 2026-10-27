"""Independently audit the fresh Comparecast alternative confirmation."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_confirmation_v1"
)
PROTOCOL = ROOT / "papers/shiftguard_unified/comparecast_paired_cost_confirmation_protocol.md"
CALIBRATION = (
    ROOT
    / "outputs/shiftguard_unified/sota_reproductions/comparecast_weak_null_calibration_v2/manifest.json"
)
SCENARIOS = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
    "stationary",
    "benign_nuisance",
)
METHODS = {"comparecast_weak_running_score", "shiftlab_conditional_bounded_mean"}
SEED_START = 99_100_000
EXPECTED_COMMIT = "52748c86e0429a9612dc79892c3be6156a524132"
EXPECTED_EPROCESS = "f07eb4496b61e89e03be22fa2f3554ea3ed25b045e0ff4c796d6a6dba4e30307"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cp_interval(
    events: int, trials: int, *, family_alpha: float = 0.05, family_cells: int = 8
) -> tuple[float, float]:
    tail = family_alpha / (2 * family_cells)
    lower = 0.0 if events == 0 else float(beta.ppf(tail, events, trials - events + 1))
    upper = 1.0 if events == trials else float(beta.ppf(1 - tail, events + 1, trials - events))
    return lower, upper


def main() -> None:
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest["artifact_sha256"].items():
        path = OUTPUT / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"artifact hash mismatch: {name}")
    if manifest.get("status") != "independent_alternative_confirmation":
        raise RuntimeError("run is not marked as the registered confirmation")
    if manifest.get("experiment") != "comparecast_paired_cost_independent_confirmation":
        raise RuntimeError("manifest experiment identity is not the independent confirmation")
    confirmation = manifest["confirmation"]
    orchestrator = ROOT / "scripts/confirm_comparecast_paired_cost.py"
    if confirmation.get("orchestrator_sha256") != sha256(orchestrator):
        raise RuntimeError("confirmation orchestrator hash mismatch")
    if confirmation.get("seed_range") != [SEED_START, SEED_START + 299]:
        raise RuntimeError("confirmation seed block differs from frozen protocol")
    if manifest.get("source", {}).get("commit") != EXPECTED_COMMIT:
        raise RuntimeError("upstream Comparecast commit differs from calibration")
    if (
        manifest.get("source", {}).get("source_sha256", {}).get("comparecast/eprocess.py")
        != EXPECTED_EPROCESS
    ):
        raise RuntimeError("upstream Comparecast e-process differs from calibration")
    if (
        confirmation.get("calibration_source_commit") != EXPECTED_COMMIT
        or confirmation.get("calibration_eprocess_sha256") != EXPECTED_EPROCESS
    ):
        raise RuntimeError("confirmation and calibration source identities differ")
    if sha256(PROTOCOL) != confirmation["protocol_sha256"]:
        raise RuntimeError("frozen protocol hash mismatch")
    calibration_hash = sha256(CALIBRATION)
    if calibration_hash != confirmation["calibration_manifest_sha256"]:
        raise RuntimeError("calibration manifest hash mismatch")
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    if not calibration.get("population_null_audit_pass") or not calibration.get(
        "simultaneous_exact_binomial_calibration_pass"
    ):
        raise RuntimeError("linked weak-null calibration no longer passes")

    metrics = pd.read_parquet(OUTPUT / "metrics.parquet")
    if len(metrics) != 3600 or metrics.duplicated(["scenario", "seed", "method"]).any():
        raise RuntimeError("expected 3,600 unique scenario/seed/method rows")
    if (
        set(metrics["scenario"].unique()) != set(SCENARIOS)
        or set(metrics["method"].unique()) != METHODS
    ):
        raise RuntimeError("scenario or method set differs from frozen protocol")
    if not metrics["events_processed"].eq(1600).all():
        raise RuntimeError("one or more streams did not process all 1,600 events")
    counts = metrics.groupby(["scenario", "method"]).size()
    if not counts.eq(300).all():
        raise RuntimeError("every method/scenario cell must contain 300 streams")
    expected_seeds = set(range(SEED_START, SEED_START + 300))
    for scenario in SCENARIOS:
        for method in METHODS:
            observed = set(
                metrics.loc[
                    metrics["scenario"].eq(scenario) & metrics["method"].eq(method), "seed"
                ].astype(int)
            )
            if observed != expected_seeds:
                raise RuntimeError(f"seed block mismatch for {scenario}/{method}")
    comparecast = metrics.loc[metrics["method"].eq("comparecast_weak_running_score")]
    if not np.isfinite(comparecast["max_e_value"]).all():
        raise RuntimeError("nonfinite official e-value")
    if not comparecast["upstream_warning_count"].eq(1).all():
        raise RuntimeError(
            "captured upstream warning count differs from the registered one per stream"
        )
    if (
        not metrics.loc[
            metrics["method"].eq("shiftlab_conditional_bounded_mean"), "upstream_warning_count"
        ]
        .eq(0)
        .all()
    ):
        raise RuntimeError("unexpected upstream warning recorded for ShiftLab monitor")
    if metrics.loc[metrics["scenario"].isin(SCENARIOS[:4]), "pre_onset_alarm"].astype(bool).any():
        raise RuntimeError("a pre-onset alarm appeared in an alternative stream")
    if metrics.loc[metrics["scenario"].isin(SCENARIOS[4:]), "alarm"].astype(bool).any():
        raise RuntimeError("a control stream alarmed in this confirmation sample")
    onset_eligibility = {}
    for scenario in SCENARIOS[:4]:
        group = metrics.loc[metrics["scenario"].eq(scenario)].drop_duplicates(["seed"])
        has_onset = group["harm_onset_relative"].notna()
        onset_eligibility[scenario] = {
            "streams": len(group),
            "streams_with_evaluator_defined_harm_onset": int(has_onset.sum()),
            "streams_without_realized_material_harm_onset": int((~has_onset).sum()),
        }
    expected_eligible = {
        "boundary_local_harm": 300,
        "residual_variance": 299,
        "recurring_regimes": 300,
        "harmful_adaptation": 300,
    }
    if {
        scenario: values["streams_with_evaluator_defined_harm_onset"]
        for scenario, values in onset_eligibility.items()
    } != expected_eligible:
        raise RuntimeError("evaluator-defined onset eligibility differs from the frozen seed block")

    recorded = pd.read_parquet(OUTPUT / "confirmation_summary.parquet")
    for scenario in SCENARIOS:
        for method in sorted(METHODS):
            group = metrics.loc[metrics["scenario"].eq(scenario) & metrics["method"].eq(method)]
            row = recorded.loc[recorded["scenario"].eq(scenario) & recorded["method"].eq(method)]
            if len(row) != 1:
                raise RuntimeError("confirmation summary cell is missing or duplicated")
            row_dict = row.iloc[0].to_dict()
            events = (
                int(group["post_onset_detection"].astype(bool).sum())
                if scenario in SCENARIOS[:4]
                else int(group["alarm"].astype(bool).sum())
            )
            if events != int(row_dict["post_onset_detections_or_alarms"]):
                raise RuntimeError(f"outcome count mismatch for {scenario}/{method}")
            if not np.isclose(events / 300, float(row_dict["rate"]), rtol=0, atol=1e-12):
                raise RuntimeError(f"outcome rate mismatch for {scenario}/{method}")
            if scenario in SCENARIOS[:4]:
                low, high = cp_interval(events, 300)
                if not np.isclose(
                    low, float(row_dict["simultaneous_cp_lower"]), rtol=0, atol=1e-12
                ):
                    raise RuntimeError(f"lower exact interval mismatch for {scenario}/{method}")
                if not np.isclose(
                    high, float(row_dict["simultaneous_cp_upper"]), rtol=0, atol=1e-12
                ):
                    raise RuntimeError(f"upper exact interval mismatch for {scenario}/{method}")

    verification = {
        "status": "passed",
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "rows": len(metrics),
        "scenarios": len(SCENARIOS),
        "method_scenario_cells": len(counts),
        "seeds_per_cell": 300,
        "all_events_processed": True,
        "finite_comparecast_e_values": True,
        "exact_intervals_recomputed": True,
        "post_onset_detection_denominator": "300 registered streams per cell; the one residual-variance stream without a realized evaluator-defined material-harm onset is counted as no post-onset detection, so the interval is for the joint per-run detection outcome rather than conditional power",
        "onset_eligibility": onset_eligibility,
        "protocol_sha256": confirmation["protocol_sha256"],
        "calibration_manifest_sha256": calibration_hash,
        "verifier_sha256": sha256(Path(__file__).resolve()),
        "all_original_artifacts_verified": True,
    }
    verification_path = OUTPUT / "verification.json"
    verification_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    manifest["independent_verification"] = verification
    manifest["artifact_sha256"]["verification.json"] = sha256(verification_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
