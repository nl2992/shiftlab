"""Independently replay and verify the fixed-candidate null calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from scipy.special import ndtr
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive import integrated_pipeline as integrated

PROTOCOL = ROOT / "papers/shiftguard_unified/fixed_candidate_null_protocol_v1.md"
ALPHA = integrated.PROMOTION_ALPHA
SEED_START = 2_026_116_000


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replay(
    seed: int, device: str
) -> tuple[dict[str, Any], np.ndarray, np.ndarray, dict[str, Any]]:
    captured: dict[str, Any] = {}
    original_fit = integrated._fit_candidate_family

    def capture(**kwargs: Any) -> dict[str, Any]:
        family = original_fit(**kwargs)
        captured["family"] = family
        captured["x"] = np.asarray(kwargs["x"])
        return family

    scenario = next(item for item in SCENARIOS if item.name == "harmful_adaptation")
    integrated._fit_candidate_family = capture
    try:
        result = integrated.run_seed(
            scenario=scenario,
            seed=seed,
            device=device,
            method="full_pipeline_fixed_certification",
            profile="calibration_candidate_null",
        )
    finally:
        integrated._fit_candidate_family = original_fit
    family: dict[str, Any] = captured["family"]
    x = np.asarray(captured["x"])
    start, end = integrated.STAGES["monitor_end"], integrated.STAGES["scout_cert_end"]
    indices = np.arange(start, end)
    score = x[indices, 0] - 0.9 * x[indices, 1]
    probability = ndtr(score / 0.3)
    incumbent = np.asarray(family["incumbent"], dtype=int)[indices]
    candidate = np.asarray(family["actions"], dtype=int)[0, indices]

    def cost(action: np.ndarray, label: int) -> np.ndarray:
        return np.where(action == 1, 1.0 * (1 - label), 5.0 * label)

    gain_if_zero = cost(incumbent, 0) - cost(candidate, 0)
    gain_if_one = cost(incumbent, 1) - cost(candidate, 1)
    pointwise_gain = (1 - probability) * gain_if_zero + probability * gain_if_one
    return result, indices, pointwise_gain, family


def verify(output: Path) -> Path:
    output = output.resolve()
    manifest_path = output / "manifest.json"
    metrics_path = output / "stream_metrics.parquet"
    summary_path = output / "summary.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = pd.read_parquet(metrics_path)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if manifest.get("protocol_sha256") != _sha256(PROTOCOL):
        errors.append("protocol hash mismatch")
    if manifest.get("metrics_sha256") != _sha256(metrics_path):
        errors.append("metrics hash mismatch")
    if manifest.get("summary_sha256") != _sha256(summary_path):
        errors.append("summary hash mismatch")
    for relpath, expected in manifest.get("source_sha256", {}).items():
        path = ROOT / relpath
        if not path.is_file() or _sha256(path) != expected:
            errors.append(f"source hash mismatch: {relpath}")
    if rows.seed.duplicated().any():
        errors.append("duplicate seed rows")
    if rows.seed.tolist() != list(range(SEED_START, SEED_START + len(rows))):
        errors.append("seed sequence is not the registered consecutive block")
    if (rows.total_labels > integrated.TOTAL_LABEL_CAP).any():
        errors.append("label cap exceeded")

    device = str(manifest.get("device", "cuda"))
    replayed = 0
    for row in rows.itertuples(index=False):
        seed = int(cast(Any, row.seed))
        result, indices, pointwise_gain, family = _replay(seed, device)
        replayed += 1
        pointwise_net = pointwise_gain - integrated.SWITCH_COST / family["deployment_length"]
        pointwise_null_holds = bool(np.all(pointwise_net <= 1e-12))
        q2_is_null = bool(result["scout_certificate_null_by_oracle"] and pointwise_null_holds)
        eligible = bool(result["monitor_triggered"] and result["scout_cert_ran"] and q2_is_null)
        if np.any(pointwise_gain > 1e-12):
            errors.append(f"pointwise Q2 null violated at seed {seed}")
        checks = {
            "eligible": eligible,
            "q1_triggered": bool(result["monitor_triggered"]),
            "q2_ran": bool(result["scout_cert_ran"]),
            "q2_is_null": q2_is_null,
            "candidate_selection_source": "initial_validation_fixed",
            "candidate_promoted": bool(result["candidate_promoted"]),
            "q1_labels": int(result["monitor_labels"]),
            "q2_labels": int(result["scout_cert_labels"]),
            "total_labels": int(result["total_labels"]),
            "q1_trigger_event": result["monitor_trigger_event"],
        }
        for key, actual in checks.items():
            observed = getattr(row, key)
            if key == "q1_trigger_event" and pd.isna(observed) and actual is None:
                continue
            if actual != observed:
                errors.append(f"replay mismatch {key} at seed {seed}")
        if len(indices) != 800:
            errors.append("Q2 certification event range changed")

    eligible_rows = rows[rows.eligible]
    errors_count = int(eligible_rows.candidate_promoted.sum()) if len(eligible_rows) else 0
    n = len(eligible_rows)
    upper = (
        1.0
        if n == 0 or errors_count == n
        else float(beta.ppf(0.95, errors_count + 1, n - errors_count))
    )
    passed = bool(
        n == int(manifest.get("replicates", 0))
        and upper <= ALPHA
        and (rows.total_labels <= integrated.TOTAL_LABEL_CAP).all()
    )
    if summary.get("eligible_streams") != n or summary.get("false_promotions") != errors_count:
        errors.append("summary counts mismatch")
    if abs(float(summary.get("exact_clopper_pearson_upper", 1.0)) - upper) > 1e-12:
        errors.append("summary exact upper bound mismatch")
    if bool(manifest.get("calibration_pass")) != passed or bool(summary.get("pass")) != passed:
        errors.append("calibration pass flag mismatch")
    if manifest.get("status") != (
        "diagnostic_calibration_complete"
        if manifest.get("replicates") == 1_000
        else "development_pilot_only"
    ):
        errors.append("sample size/status mismatch")

    report = {
        "verified": not errors,
        "errors": errors,
        "replayed_streams": replayed,
        "eligible_streams": n,
        "false_promotions": errors_count,
        "exact_one_sided_95pct_upper": upper,
        "alpha": ALPHA,
        "calibration_pass": passed,
    }
    path = output / "verification.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if errors:
        raise RuntimeError("fixed-candidate calibration verification failed: " + "; ".join(errors))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.output)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(result)


if __name__ == "__main__":
    main()
