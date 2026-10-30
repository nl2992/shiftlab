"""Independently verify integrated pipeline null-calibration artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
import torch
from scipy.special import ndtr
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.decision_harm_experiment import SCENARIOS, Scenario  # noqa: E402 -- local script path bootstrap
from shiftlab.dive import integrated_pipeline as integrated  # noqa: E402 -- local script path bootstrap

PROTOCOL = ROOT / "papers/shiftguard_unified/integrated_null_calibration_protocol_v1.md"
ALPHAS = {
    "q1_stationary": 0.02,
    "q1_benign_nuisance": 0.02,
    "q2_promotion": 0.015,
    "q3_rollback": 0.015,
}
FAMILYWISE_DELTA = 0.05
TOTAL_LABEL_CAP = 640
ROLLBACK_COST = 0.05
DEPLOYMENT_LENGTH = 800
Q3_SEVERITY = 3.0
Q3_ORACLE_N = 100_000
Q3_ORACLE_DELTA = 1e-8


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _upper(errors: int, n: int, delta: float) -> float:
    if n <= 0 or not 0 <= errors <= n:
        raise ValueError("invalid binomial endpoint")
    return 1.0 if errors == n else float(beta.ppf(1 - delta, errors + 1, n - errors))


def _replay_q3_stream(
    seed: int, device: str
) -> tuple[dict[str, object], float | None, float | None]:
    """Replay one Q3 seed and independently recompute its population-null bound."""
    original_fit = integrated._fit_candidate_family
    captured: dict[str, Any] = {}

    def capture(**kwargs: Any) -> dict[str, Any]:
        family = original_fit(**kwargs)
        captured["family"] = family
        captured["x"] = np.asarray(kwargs["x"])
        captured["y"] = np.asarray(kwargs["y"])
        return family

    integrated._fit_candidate_family = capture
    try:
        source = next(item for item in SCENARIOS if item.name == "boundary_local_harm")
        scenario = Scenario(
            source.name,
            source.dgp,
            pattern=source.pattern,
            severity=Q3_SEVERITY,
            fn_cost=source.fn_cost,
            fp_cost=source.fp_cost,
            description="Frozen Q3 rollback-null calibration severity.",
        )
        result = integrated.run_seed(
            scenario=scenario,
            seed=seed,
            device=device,
            method="full_pipeline",
        )
    finally:
        integrated._fit_candidate_family = original_fit

    if not result["candidate_promoted"]:
        return result, None, None

    family: dict[str, Any] = captured["family"]
    x = np.asarray(captured["x"])
    y = np.asarray(captured["y"])
    generator = torch.Generator(device=device).manual_seed(seed + 8_000_001)
    x_oracle_tensor = torch.randn((Q3_ORACLE_N, x.shape[1]), generator=generator, device=device)
    x_oracle = x_oracle_tensor.cpu().numpy()
    score = x_oracle[:, 0] - 0.9 * x_oracle[:, 1]
    probability = ndtr((score + Q3_SEVERITY * np.exp(-5 * np.abs(score))) / 0.3)
    incumbent_action = (score >= 0).astype(int)
    contexts = (x_oracle[:, 0] >= 0).astype(int)
    candidate_action = incumbent_action.copy()
    selected = json.loads(str(result["candidate_by_context"]))
    train_end = int(family["train_end"])
    for group in (0, 1):
        candidate_id = selected.get(str(group))
        if candidate_id is None:
            continue
        mask = contexts == group
        if candidate_id == "incumbent_snapshot":
            action = incumbent_action[mask]
        else:
            match = re.fullmatch(r"logistic_C=([^_]+)_threshold_scale=([^_]+)", str(candidate_id))
            if match is None:
                raise ValueError(f"unrecognized selected candidate id: {candidate_id}")
            c_value, scale = map(float, match.groups())
            model = LogisticRegression(C=c_value, max_iter=500)
            model.fit(x[:train_end], y[:train_end])
            action = (model.predict_proba(x_oracle[mask])[:, 1] >= (1.0 / 6.0) * scale).astype(int)
        candidate_action[mask] = action

    incumbent_cost = np.where(incumbent_action == 1, 1.0 * (1 - probability), 5.0 * probability)
    candidate_cost = np.where(candidate_action == 1, 1.0 * (1 - probability), 5.0 * probability)
    estimate = float((incumbent_cost - candidate_cost).mean())
    radius = 5.0 * np.sqrt(2 * np.log(1 / Q3_ORACLE_DELTA) / Q3_ORACLE_N)
    return result, estimate, estimate - radius


def verify(output: Path) -> Path:
    output = output.resolve()
    manifest_path = output / "manifest.json"
    metrics_path = output / "stream_metrics.parquet"
    summary_path = output / "cell_summary.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = pd.read_parquet(metrics_path)
    summary = pd.read_csv(summary_path).set_index("cell")
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

    if metrics.seed.duplicated().any() and metrics.groupby(["cell", "seed"]).size().max() > 1:
        errors.append("duplicate stream key")
    if (metrics.total_labels > TOTAL_LABEL_CAP).any():
        errors.append("hard label cap exceeded")
    if (metrics.total_labels < 0).any() or (metrics.hard_label_cap != TOTAL_LABEL_CAP).any():
        errors.append("invalid resource fields")

    if "q1_stationary" in set(metrics.cell):
        q1 = metrics[metrics.cell == "q1_stationary"]
        if (
            (q1.scenario != "stationary").any()
            or q1.eligible_for_q2.any()
            or q1.eligible_for_q3.any()
        ):
            errors.append("stationary Q1 cell contract mismatch")
    if "q1_benign_nuisance" in set(metrics.cell):
        q1 = metrics[metrics.cell == "q1_benign_nuisance"]
        if (
            (q1.scenario != "benign_nuisance").any()
            or q1.eligible_for_q2.any()
            or q1.eligible_for_q3.any()
        ):
            errors.append("nuisance Q1 cell contract mismatch")

    q2 = metrics[metrics.cell == "q2_promotion"]
    if len(q2):
        if (q2.eligible_for_q2 & ~q2.q2_null_by_evaluator).any():
            errors.append("Q2 eligible stream violates evaluator null flag")
        if (q2.eligible_for_q2 & (~q2.monitor_triggered | ~q2.q2_selected)).any():
            errors.append("Q2 eligible stream did not reach and select at the gate")
        if (q2.eligible_for_q2 & (q2.scenario != "calibration_candidate_null")).any():
            errors.append("Q2 null profile mismatch")

    q3 = metrics[metrics.cell == "q3_rollback"]
    if len(q3):
        cutoff = -ROLLBACK_COST / DEPLOYMENT_LENGTH
        if (q3.eligible_for_q3 & (~q3.candidate_promoted | (q3.oracle_gain_lower < cutoff))).any():
            errors.append("Q3 eligible stream does not satisfy its independent population null")
        if (q3.oracle_mc_n[q3.eligible_for_q3] != 100_000).any():
            errors.append("Q3 oracle Monte Carlo size mismatch")
        if (q3.oracle_mc_delta[q3.eligible_for_q3] != 1e-8).any():
            errors.append("Q3 oracle Monte Carlo confidence error mismatch")

    q3_replayed = 0
    if len(q3):
        device = str(manifest.get("device", "cuda"))
        for row in q3.itertuples(index=False):
            replay, estimate, lower = _replay_q3_stream(int(cast(Any, row.seed)), device)
            q3_replayed += 1
            if bool(replay["candidate_promoted"]) != bool(row.candidate_promoted):
                errors.append(f"Q3 replay promotion mismatch at seed {row.seed}")
            if (replay["rollback_event"] is not None) != bool(row.rollback_triggered):
                errors.append(f"Q3 replay rollback mismatch at seed {row.seed}")
            if int(cast(Any, replay["total_labels"])) != int(cast(Any, row.total_labels)):
                errors.append(f"Q3 replay label-count mismatch at seed {row.seed}")
            if estimate is None or lower is None:
                if row.eligible_for_q3 or int(cast(Any, row.oracle_mc_n)) != 0:
                    errors.append(f"Q3 nonpromoted stream has an oracle score at seed {row.seed}")
            else:
                expected_eligible = lower >= -ROLLBACK_COST / DEPLOYMENT_LENGTH
                if abs(estimate - float(row.oracle_gain_estimate)) > 1e-12:
                    errors.append(f"Q3 oracle gain replay mismatch at seed {row.seed}")
                if abs(lower - float(row.oracle_gain_lower)) > 1e-12:
                    errors.append(f"Q3 oracle lower-bound replay mismatch at seed {row.seed}")
                if bool(expected_eligible) != bool(row.eligible_for_q3):
                    errors.append(f"Q3 eligibility replay mismatch at seed {row.seed}")
            if q3_replayed % 100 == 0:
                print(f"independent Q3 replay: {q3_replayed}/{len(q3)} streams", flush=True)

    n_requested = int(manifest.get("replicates_per_error_cell", 0))
    delta = FAMILYWISE_DELTA / len(ALPHAS)
    recomputed: dict[str, dict[str, float | int | bool]] = {}
    for cell, alpha in ALPHAS.items():
        rows = metrics[metrics.cell == cell]
        eligible_column = (
            None
            if cell.startswith("q1_")
            else ("eligible_for_q2" if cell == "q2_promotion" else "eligible_for_q3")
        )
        if eligible_column is not None:
            eligible = rows[rows[eligible_column]]
        else:
            eligible = rows
        key = {
            "q1_stationary": "monitor_triggered",
            "q1_benign_nuisance": "monitor_triggered",
            "q2_promotion": "candidate_promoted",
            "q3_rollback": "rollback_triggered",
        }[cell]
        count = int(eligible[key].sum()) if len(eligible) else 0
        upper = _upper(count, len(eligible), delta) if len(eligible) else 1.0
        passed = bool(len(eligible) == n_requested and upper <= alpha)
        recomputed[cell] = {
            "errors": count,
            "eligible_streams": len(eligible),
            "exact_one_sided_upper": upper,
            "pass": passed,
        }
        if cell not in summary.index:
            errors.append(f"missing summary row: {cell}")
            continue
        for name, value in recomputed[cell].items():
            observed = summary.loc[cell, name]
            if isinstance(value, float):
                if abs(float(observed) - value) > 1e-12:
                    errors.append(f"summary mismatch {cell}.{name}")
            elif bool(observed) != value if isinstance(value, bool) else int(observed) != value:
                errors.append(f"summary mismatch {cell}.{name}")

    is_registered = (
        n_requested == 1_000 and manifest.get("q3_oracle_mc", {}).get("max_streams") == 2_500
    )
    calibration_pass = bool(is_registered and all(item["pass"] for item in recomputed.values()))
    if manifest.get("calibration_pass") != calibration_pass:
        errors.append("manifest calibration_pass mismatch")
    if not is_registered and manifest.get("status") != "development_pilot_only":
        errors.append("nonregistered sample incorrectly labeled as a calibration")

    report = {
        "verified": not errors,
        "errors": errors,
        "manifest_status": manifest.get("status"),
        "calibration_pass": calibration_pass,
        "recomputed_cells": recomputed,
        "rows": len(metrics),
        "q3_streams_replayed": q3_replayed,
        "protocol_sha256": _sha256(PROTOCOL),
        "metrics_sha256": _sha256(metrics_path),
    }
    verification_path = output / "verification.json"
    verification_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if errors:
        raise RuntimeError("integrated calibration verification failed: " + "; ".join(errors))
    return verification_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v1",
    )
    args = parser.parse_args()
    result = verify(args.output)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(result)


if __name__ == "__main__":
    main()
