"""Calibrate the fixed-candidate promotion gate on a registered pointwise null."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive import integrated_pipeline as integrated

PROTOCOL = ROOT / "papers/shiftguard_unified/fixed_candidate_null_protocol_v1.md"
SEED_START = 2_026_116_000
ALPHA = integrated.PROMOTION_ALPHA
MAX_ATTEMPTS_PER_REPLICATE = 3


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*, replicates: int, output: Path, device: str) -> Path:
    if replicates < 1:
        raise ValueError("replicates must be positive")
    device = resolve_device(device, n=integrated.STAGES["stream_end"], d=16, chunk_size=2048)
    if device != "cuda":
        raise RuntimeError("the registered fixed-candidate calibration requires CUDA generation")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output}")

    scenario = next(item for item in SCENARIOS if item.name == "harmful_adaptation")
    rows: list[dict[str, Any]] = []
    eligible_count = 0
    attempts = 0
    max_attempts = MAX_ATTEMPTS_PER_REPLICATE * replicates
    while eligible_count < replicates and attempts < max_attempts:
        seed = SEED_START + attempts
        result = integrated.run_seed(
            scenario=scenario,
            seed=seed,
            device=device,
            method="full_pipeline_fixed_certification",
            profile="calibration_candidate_null",
        )
        eligible = bool(
            result["monitor_triggered"]
            and result["scout_cert_ran"]
            and result["scout_certificate_null_by_oracle"]
            and result["candidate_selection_source"] == "initial_validation_fixed"
        )
        reason = (
            "q1_trigger_fixed_candidate_q2_null"
            if eligible
            else "q1_not_triggered"
            if not result["monitor_triggered"]
            else "q2_not_eligible_under_oracle_null"
        )
        rows.append(
            {
                "cell": "fixed_candidate_q2_promotion",
                "seed": seed,
                "eligible": eligible,
                "eligibility_reason": reason,
                "q1_triggered": bool(result["monitor_triggered"]),
                "q2_ran": bool(result["scout_cert_ran"]),
                "q2_is_null": bool(result["scout_certificate_null_by_oracle"]),
                "candidate_selection_source": result["candidate_selection_source"],
                "candidate_promoted": bool(result["candidate_promoted"]),
                "q1_labels": int(result["monitor_labels"]),
                "q2_labels": int(result["scout_cert_labels"]),
                "total_labels": int(result["total_labels"]),
                "label_cap": int(result["hard_label_cap"]),
                "q1_trigger_event": result["monitor_trigger_event"],
                "q2_net_expected_gain": result["scout_expected_net_gain_on_certification"],
            }
        )
        attempts += 1
        eligible_count += int(eligible)
        if attempts % 100 == 0:
            print(f"eligible={eligible_count}/{replicates}; attempts={attempts}", flush=True)
    if eligible_count < replicates:
        raise RuntimeError(
            f"only {eligible_count}/{replicates} eligible streams in {attempts} attempts"
        )

    metrics_path = output / "stream_metrics.parquet"
    metrics = pd.DataFrame(rows)
    metrics.to_parquet(metrics_path, index=False)
    eligible_rows = metrics[metrics.eligible]
    errors = int(eligible_rows.candidate_promoted.sum())
    upper = (
        1.0
        if errors == len(eligible_rows)
        else float(beta.ppf(0.95, errors + 1, len(eligible_rows) - errors))
    )
    passed = bool(
        len(eligible_rows) == replicates
        and upper <= ALPHA
        and (metrics.total_labels <= metrics.label_cap).all()
    )
    summary_path = output / "summary.json"
    summary = {
        "cell": "fixed_candidate_q2_promotion",
        "eligible_streams": len(eligible_rows),
        "attempted_streams": len(metrics),
        "false_promotions": errors,
        "alpha": ALPHA,
        "one_sided_confidence": 0.95,
        "exact_clopper_pearson_upper": upper,
        "max_labels": int(metrics.total_labels.max()),
        "hard_label_cap": integrated.TOTAL_LABEL_CAP,
        "pass": passed,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    source_paths = (
        Path("src/shiftlab/dive/integrated_pipeline.py"),
        Path("src/shiftlab/dive/budgeted_promotion.py"),
        Path("src/shiftlab/dive/eprocess.py"),
        Path("src/shiftlab/decision_harm_experiment.py"),
        Path("scripts/calibrate_fixed_candidate_null.py"),
        Path("scripts/verify_fixed_candidate_null_calibration.py"),
    )
    manifest = {
        "experiment": "fixed_candidate_q2_pointwise_null_calibration_v1",
        "status": "diagnostic_calibration_complete"
        if replicates == 1_000
        else "development_pilot_only",
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": _sha256(PROTOCOL),
        "source_sha256": {str(path): _sha256(ROOT / path) for path in source_paths},
        "created_utc": datetime.now(UTC).isoformat(),
        "seed_start": SEED_START,
        "replicates": replicates,
        "attempts": attempts,
        "eligible_streams": eligible_count,
        "device": device,
        "hardware": environment(),
        "metrics_sha256": _sha256(metrics_path),
        "summary_sha256": _sha256(summary_path),
        "calibration_pass": passed,
        "limitations": [
            "This is a diagnostic simulation under the registered iid pointwise-null construction, not a proof.",
            "The result does not establish efficacy, power, real-data validity, delayed-feedback validity, or dependent-stream validity.",
        ],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if replicates == 1_000 and not passed:
        raise RuntimeError("fixed-candidate null calibration did not pass its registered threshold")
    print(json.dumps(summary, indent=2))
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=1_000)
    parser.add_argument("--device", choices=("cuda", "auto"), default="cuda")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = run(replicates=args.replicates, output=args.output, device=args.device)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(manifest)


if __name__ == "__main__":
    main()
