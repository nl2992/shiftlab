"""Run the frozen integrated Q1/Q2/Q3 conditional-null calibration protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from scipy.special import ndtr
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.data.gpu.environment import environment, resolve_device
from shiftlab.decision_harm_experiment import SCENARIOS, Scenario
from shiftlab.dive import integrated_pipeline as integrated

PROTOCOL = ROOT / "papers/shiftguard_unified/integrated_null_calibration_protocol_v1.md"
SOURCE_FILES = (
    Path("src/shiftlab/dive/integrated_pipeline.py"),
    Path("src/shiftlab/dive/budgeted_promotion.py"),
    Path("src/shiftlab/dive/eprocess.py"),
    Path("src/shiftlab/dive/promotion_grid.py"),
    Path("src/shiftlab/decision_harm_experiment.py"),
    Path("src/shiftlab/data/synthetic/generators.py"),
    Path("scripts/calibrate_integrated_pipeline.py"),
)
Q1_STATIONARY_SEED = 2_026_112_000
Q1_NUISANCE_SEED = 2_026_113_000
Q2_NULL_SEED = 2_026_114_000
Q3_ROLLBACK_SEED = 2_026_115_000
Q3_SEVERITY = 3.0
Q3_ORACLE_N = 100_000
Q3_ORACLE_DELTA = 1e-8
Q3_MAX_STREAMS = 2_500
NULLS = {
    "q1_stationary": 0.02,
    "q1_benign_nuisance": 0.02,
    "q2_promotion": 0.015,
    "q3_rollback": 0.015,
}
FAMILYWISE_CONFIDENCE_ERROR = 0.05
FN_COST = 5.0
FP_COST = 1.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exact_upper(errors: int, streams: int, delta: float) -> float:
    if streams < 1 or not 0 <= errors <= streams or not 0 < delta < 1:
        raise ValueError("invalid binomial count or confidence error")
    if errors == streams:
        return 1.0
    return float(beta.ppf(1 - delta, errors + 1, streams - errors))


def _capture_family_run(
    *, scenario: Scenario, seed: int, device: str, profile: str | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    captured: dict[str, Any] = {}
    original = integrated._fit_candidate_family

    def capture(**kwargs: Any) -> dict[str, Any]:
        family = original(**kwargs)
        captured["family"] = family
        captured["x"] = np.asarray(kwargs["x"])
        captured["y"] = np.asarray(kwargs["y"])
        return family

    integrated._fit_candidate_family = capture
    try:
        result = integrated.run_seed(
            scenario=scenario,
            seed=seed,
            device=device,
            method="full_pipeline",
            profile=profile,
        )
    finally:
        integrated._fit_candidate_family = original
    return result, captured


def _selected_policy_gain_lower_bound(
    *,
    result: dict[str, Any],
    captured: dict[str, Any],
    seed: int,
    device: str,
) -> tuple[float, float, float]:
    """Evaluate the selected frozen policy on independent oracle covariates."""
    family = captured["family"]
    x = captured["x"]
    y = captured["y"]
    n = Q3_ORACLE_N
    torch_generator = torch.Generator(device=device).manual_seed(seed + 8_000_001)
    x_oracle = torch.randn((n, x.shape[1]), generator=torch_generator, device=device).cpu().numpy()
    score = x_oracle[:, 0] - 0.9 * x_oracle[:, 1]
    severity = Q3_SEVERITY
    mean = score + severity * np.exp(-5 * np.abs(score))
    probability = ndtr(mean / 0.3)
    incumbent_action = (score >= 0).astype(int)
    incumbent_cost = np.where(
        incumbent_action == 1,
        FP_COST * (1 - probability),
        FN_COST * probability,
    )

    selected = json.loads(str(result["candidate_by_context"]))
    contexts = (x_oracle[:, 0] >= 0).astype(int)
    candidate_action = incumbent_action.copy()
    train_end = int(family["train_end"])
    for group in (0, 1):
        candidate_id = selected.get(str(group))
        if candidate_id is None:
            continue
        candidate_id = str(candidate_id)
        mask = contexts == group
        if candidate_id == "incumbent_snapshot":
            action = incumbent_action[mask]
        else:
            match = re.fullmatch(r"logistic_C=([^_]+)_threshold_scale=([^_]+)", candidate_id)
            if match is None:
                raise ValueError(f"unrecognized registered candidate id: {candidate_id}")
            c_value, scale = map(float, match.groups())
            model = LogisticRegression(C=c_value, max_iter=500)
            model.fit(x[:train_end], y[:train_end])
            cutoff = FP_COST / (FN_COST + FP_COST) * scale
            action = (model.predict_proba(x_oracle[mask])[:, 1] >= cutoff).astype(int)
        candidate_action[mask] = action

    candidate_cost = np.where(
        candidate_action == 1,
        FP_COST * (1 - probability),
        FN_COST * probability,
    )
    gain = incumbent_cost - candidate_cost
    estimate = float(gain.mean())
    # Each bounded paired-cost difference lies in [-M, M]. This independent,
    # evaluator-only MC lower bound is for eligibility and is never learner input.
    bound = max(FN_COST, FP_COST)
    radius = bound * np.sqrt(2 * np.log(1 / Q3_ORACLE_DELTA) / n)
    lower_bound = estimate - radius
    return estimate, lower_bound, radius


def _cell_summary(
    cell: str, values: list[dict[str, Any]], *, eligible_key: str | None = None
) -> dict[str, Any]:
    eligible = values if eligible_key is None else [row for row in values if row[eligible_key]]
    error_key = {
        "q1_stationary": "monitor_triggered",
        "q1_benign_nuisance": "monitor_triggered",
        "q2_promotion": "candidate_promoted",
        "q3_rollback": "rollback_triggered",
    }[cell]
    errors = sum(bool(row[error_key]) for row in eligible)
    n = len(eligible)
    delta = FAMILYWISE_CONFIDENCE_ERROR / len(NULLS)
    alpha = NULLS[cell]
    upper = _exact_upper(errors, n, delta) if n else 1.0
    return {
        "cell": cell,
        "error_event": error_key,
        "errors": errors,
        "eligible_streams": n,
        "attempted_streams": len(values),
        "nominal_alpha": alpha,
        "familywise_confidence": 1 - delta,
        "exact_one_sided_upper": upper,
        "pass": bool(n and upper <= alpha),
    }


def run(*, replicates: int, output: Path, device: str, max_q3_streams: int) -> Path:
    if replicates < 1 or max_q3_streams < replicates:
        raise ValueError("replicates must be positive and Q3 maximum must be at least replicates")
    if not PROTOCOL.is_file():
        raise FileNotFoundError(PROTOCOL)
    device = resolve_device(device, n=integrated.STAGES["stream_end"], d=16, chunk_size=2048)
    if device != "cuda":
        raise RuntimeError("the registered calibration uses CUDA generation")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "status.json").write_text(
        json.dumps({"status": "running", "started_utc": datetime.now(UTC).isoformat()}),
        encoding="utf-8",
    )

    rows: list[dict[str, Any]] = []
    stationary = next(item for item in SCENARIOS if item.name == "stationary")
    benign = next(item for item in SCENARIOS if item.name == "benign_nuisance")
    harm = next(item for item in SCENARIOS if item.name == "harmful_adaptation")
    boundary = next(item for item in SCENARIOS if item.name == "boundary_local_harm")

    def add_row(cell: str, result: dict[str, Any], **extra: Any) -> None:
        rows.append(
            {
                "cell": cell,
                "scenario": result["scenario"],
                "seed": int(result["seed"]),
                "monitor_triggered": bool(result["monitor_triggered"]),
                "scout_selected_candidate": bool(result["scout_selected_candidate"]),
                "candidate_promoted": bool(result["candidate_promoted"]),
                "q2_selected": bool(result["scout_selected_candidate"]),
                "eligible_for_q2": bool(extra.get("eligible_for_q2", False)),
                "eligible_for_q3": bool(extra.get("eligible_for_q3", False)),
                "q2_null_by_evaluator": bool(result["scout_certificate_null_by_oracle"]),
                "rollback_triggered": result["rollback_event"] is not None,
                "total_labels": int(result["total_labels"]),
                "hard_label_cap": int(result["hard_label_cap"]),
                **extra,
            }
        )

    for cell, scenario, start, profile in (
        ("q1_stationary", stationary, Q1_STATIONARY_SEED, None),
        ("q1_benign_nuisance", benign, Q1_NUISANCE_SEED, None),
    ):
        for i in range(replicates):
            result = integrated.run_seed(
                scenario=scenario,
                seed=start + i,
                device=device,
                method="full_pipeline",
                profile=profile,
            )
            add_row(cell, result)
            if (i + 1) % 100 == 0:
                print(f"{cell}: {i + 1}/{replicates}", flush=True)

    q2_eligible = 0
    q2_attempted = 0
    while q2_eligible < replicates and q2_attempted < 3 * replicates:
        seed = Q2_NULL_SEED + q2_attempted
        result = integrated.run_seed(
            scenario=harm,
            seed=seed,
            device=device,
            method="full_pipeline",
            profile="calibration_candidate_null",
        )
        selected_and_null = (
            result["monitor_triggered"]
            and result["scout_selected_candidate"]
            and result["scout_certificate_null_by_oracle"]
        )
        add_row(
            "q2_promotion",
            result,
            eligible_for_q2=selected_and_null,
            eligibility_reason=("selected_candidate_null" if selected_and_null else "not_eligible"),
        )
        q2_attempted += 1
        q2_eligible += int(selected_and_null)
        if q2_attempted % 100 == 0:
            print(
                f"q2_promotion: {q2_eligible}/{replicates} eligible; {q2_attempted} attempted",
                flush=True,
            )
    if q2_eligible < replicates:
        raise RuntimeError(
            f"Q2 calibration reached only {q2_eligible}/{replicates} eligible streams"
        )

    boundary = Scenario(
        boundary.name,
        boundary.dgp,
        pattern=boundary.pattern,
        severity=Q3_SEVERITY,
        fn_cost=boundary.fn_cost,
        fp_cost=boundary.fp_cost,
        description="Frozen Q3 rollback-null calibration severity.",
    )
    q3_eligible = 0
    q3_attempted = 0
    while q3_eligible < replicates and q3_attempted < max_q3_streams:
        seed = Q3_ROLLBACK_SEED + q3_attempted
        result, captured = _capture_family_run(scenario=boundary, seed=seed, device=device)
        eligible = False
        gain_estimate = gain_lower = gain_radius = np.nan
        if result["candidate_promoted"]:
            gain_estimate, gain_lower, gain_radius = _selected_policy_gain_lower_bound(
                result=result, captured=captured, seed=seed, device=device
            )
            eligible = gain_lower >= -integrated.ROLLBACK_COST / (
                integrated.STAGES["stream_end"] - integrated.STAGES["scout_cert_end"]
            )
        add_row(
            "q3_rollback",
            result,
            eligible_for_q3=eligible,
            eligibility_reason=(
                "promoted_policy_meets_population_null" if eligible else "not_eligible"
            ),
            oracle_gain_estimate=gain_estimate,
            oracle_gain_lower=gain_lower,
            oracle_gain_radius=gain_radius,
            oracle_mc_n=Q3_ORACLE_N if np.isfinite(gain_estimate) else 0,
            oracle_mc_delta=Q3_ORACLE_DELTA if np.isfinite(gain_estimate) else None,
        )
        q3_attempted += 1
        q3_eligible += int(eligible)
        if q3_attempted % 100 == 0:
            print(
                f"q3_rollback: {q3_eligible}/{replicates} eligible; {q3_attempted} attempted",
                flush=True,
            )
    if q3_eligible < replicates:
        raise RuntimeError(
            f"Q3 calibration reached only {q3_eligible}/{replicates} eligible streams"
        )

    detail = pd.DataFrame(rows)
    detail_path = output / "stream_metrics.parquet"
    detail.to_parquet(detail_path, index=False)
    summaries = [
        _cell_summary("q1_stationary", detail[detail.cell == "q1_stationary"].to_dict("records")),
        _cell_summary(
            "q1_benign_nuisance", detail[detail.cell == "q1_benign_nuisance"].to_dict("records")
        ),
        _cell_summary(
            "q2_promotion",
            detail[detail.cell == "q2_promotion"].to_dict("records"),
            eligible_key="eligible_for_q2",
        ),
        _cell_summary(
            "q3_rollback",
            detail[detail.cell == "q3_rollback"].to_dict("records"),
            eligible_key="eligible_for_q3",
        ),
    ]
    summary_path = output / "cell_summary.csv"
    pd.DataFrame(summaries).to_csv(summary_path, index=False)
    source_hashes = {str(path): _sha256(ROOT / path) for path in SOURCE_FILES}
    manifest = {
        "experiment": "integrated_q1_q2_q3_conditional_null_calibration_v1",
        "status": (
            "diagnostic_calibration_complete"
            if replicates == 1_000 and max_q3_streams == Q3_MAX_STREAMS
            else "development_pilot_only"
        ),
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": _sha256(PROTOCOL),
        "source_sha256": source_hashes,
        "created_utc": datetime.now(UTC).isoformat(),
        "replicates_per_error_cell": replicates,
        "device": device,
        "hardware": environment(),
        "seed_blocks": {
            "q1_stationary": {"start": Q1_STATIONARY_SEED, "count": replicates},
            "q1_benign_nuisance": {"start": Q1_NUISANCE_SEED, "count": replicates},
            "q2_candidate_null": {
                "start": Q2_NULL_SEED,
                "attempts": q2_attempted,
                "eligible": q2_eligible,
            },
            "q3_rollback_null": {
                "start": Q3_ROLLBACK_SEED,
                "attempts": q3_attempted,
                "eligible": q3_eligible,
            },
        },
        "q3_oracle_mc": {"n": Q3_ORACLE_N, "delta": Q3_ORACLE_DELTA, "max_streams": max_q3_streams},
        "null_targets": NULLS,
        "familywise_confidence_error": FAMILYWISE_CONFIDENCE_ERROR,
        "metrics_sha256": _sha256(detail_path),
        "summary_sha256": _sha256(summary_path),
        "calibration_pass": bool(
            replicates == 1_000
            and max_q3_streams == Q3_MAX_STREAMS
            and all(item["pass"] for item in summaries)
        ),
        "limitations": [
            "Monte Carlo calibration diagnoses implementation under registered synthetic nulls; it is not a proof.",
            "The Q2 pointwise-null candidate family is a calibration construction, not an efficacy baseline.",
            "Q3 population-null eligibility is certified by an independent finite Monte Carlo lower bound with recorded delta.",
            "Delayed, dependent, recurring, performative, and real-data regimes are outside this calibration.",
        ],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "status.json").write_text(
        json.dumps(
            {
                "status": "complete" if replicates == 1_000 else "complete_pilot",
                "finished_utc": datetime.now(UTC).isoformat(),
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replicates", type=int, default=1_000)
    parser.add_argument("--max-q3-streams", type=int, default=Q3_MAX_STREAMS)
    parser.add_argument("--device", choices=("cuda", "auto"), default="cuda")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v1",
    )
    args = parser.parse_args()
    manifest = run(
        replicates=args.replicates,
        max_q3_streams=args.max_q3_streams,
        device=args.device,
        output=args.output,
    )
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(manifest)


if __name__ == "__main__":
    main()
