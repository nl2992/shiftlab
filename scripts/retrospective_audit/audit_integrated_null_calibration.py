"""Reconcile integrated null-calibration cells from archived stream metrics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT.parent
    / "shift-research-starter/outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v2"
)
PREDECESSOR = SOURCE.parent / "integrated_null_calibration_v1"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/INTEGRATED_NULL_CALIBRATION_AUDIT.json"
CELLS = {
    "q1_stationary": (2026112000, 1000, None, "monitor_triggered", 0.02),
    "q1_benign_nuisance": (2026113000, 1000, None, "monitor_triggered", 0.02),
    "q2_promotion": (2026114000, 1089, "eligible_for_q2", "candidate_promoted", 0.015),
    "q3_rollback": (2026115000, 1266, "eligible_for_q3", "rollback_triggered", 0.015),
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict[str, object]:
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    detail = pd.read_parquet(SOURCE / "stream_metrics.parquet")
    summary = pd.read_csv(SOURCE / "cell_summary.csv").set_index("cell")
    if not summary.index.is_unique:
        raise AssertionError("duplicate calibration summary cell")
    receipt = json.loads((SOURCE / "verification.json").read_text(encoding="utf-8"))
    if _sha(SOURCE / "stream_metrics.parquet") != manifest["metrics_sha256"]:
        raise AssertionError("calibration metrics hash mismatch")
    if _sha(SOURCE / "cell_summary.csv") != manifest["summary_sha256"]:
        raise AssertionError("calibration summary hash mismatch")
    if (
        _sha(ROOT / "papers/shiftguard_unified/integrated_null_calibration_protocol_v1.md")
        != manifest["protocol_sha256"]
    ):
        raise AssertionError("calibration protocol hash mismatch")
    if len(detail) != 4355 or set(detail.cell) != set(CELLS):
        raise AssertionError("unexpected calibration cells or row count")
    if detail.duplicated(["cell", "seed"]).any():
        raise AssertionError("duplicate calibration stream")
    if (detail.total_labels > 640).any() or (detail.total_labels < 0).any():
        raise AssertionError("calibration label cap violation")
    if (detail.hard_label_cap != 640).any():
        raise AssertionError("wrong recorded label cap")
    rows = []
    max_error = 0.0
    confidence_error = 0.05 / len(CELLS)
    for cell, (seed_start, attempts, eligibility, event, alpha) in CELLS.items():
        group = detail.loc[detail.cell == cell]
        if len(group) != attempts or set(group.seed) != set(
            range(seed_start, seed_start + attempts)
        ):
            raise AssertionError(f"seed coverage mismatch {cell}")
        eligible = group if eligibility is None else group.loc[group[eligibility]]
        if len(eligible) != 1000:
            raise AssertionError(f"eligible count mismatch {cell}")
        errors = int(eligible[event].sum())
        upper = 1 - confidence_error ** (1 / len(eligible)) if errors == 0 else None
        if upper is None:
            raise AssertionError(f"nonzero errors require general beta inversion: {cell}")
        values = {
            "errors": errors,
            "eligible_streams": len(eligible),
            "attempted_streams": attempts,
            "nominal_alpha": alpha,
            "familywise_confidence": 1 - confidence_error,
            "exact_one_sided_upper": upper,
            "pass": upper <= alpha,
        }
        for field, value in values.items():
            archived = summary.loc[cell, field]
            error = abs(float(archived) - float(value))
            max_error = max(max_error, error)
            if error > 1e-12:
                raise AssertionError(f"summary mismatch {cell}/{field}")
        if receipt["recomputed_cells"][cell]["errors"] != errors:
            raise AssertionError(f"receipt mismatch {cell}")
        rows.append({"cell": cell, **values, "max_labels": int(group.total_labels.max())})
    q2 = detail.loc[detail.cell == "q2_promotion"]
    if int(q2.monitor_triggered.sum()) != 1062 or int(q2.scout_selected_candidate.sum()) != 1000:
        raise AssertionError("Q2 attempt waterfall mismatch")
    if (
        q2.eligible_for_q2
        & ~(q2.monitor_triggered & q2.scout_selected_candidate & q2.q2_null_by_evaluator)
    ).any():
        raise AssertionError("Q2 eligibility mismatch")
    q3 = detail.loc[detail.cell == "q3_rollback"]
    if (
        int(q3.candidate_promoted.sum()) != 1000
        or (q3.eligible_for_q3 & ~q3.candidate_promoted).any()
    ):
        raise AssertionError("Q3 promotion eligibility mismatch")
    scored = q3.loc[q3.candidate_promoted]
    radius = 5 * np.sqrt(2 * np.log(1 / 1e-8) / 100000)
    if not np.allclose(scored.oracle_gain_radius, radius, rtol=0, atol=1e-12):
        raise AssertionError("Q3 oracle radius mismatch")
    if not np.allclose(
        scored.oracle_gain_lower, scored.oracle_gain_estimate - radius, rtol=0, atol=1e-12
    ):
        raise AssertionError("Q3 oracle lower-bound mismatch")
    if not (scored.oracle_gain_lower >= -0.05 / 800).all():
        raise AssertionError("Q3 eligibility cutoff mismatch")
    if not (scored.oracle_mc_n == 100000).all() or not (scored.oracle_mc_delta == 1e-8).all():
        raise AssertionError("Q3 oracle metadata mismatch")
    predecessor_manifest = json.loads((PREDECESSOR / "manifest.json").read_text(encoding="utf-8"))
    predecessor_identical = {
        name: _sha(PREDECESSOR / name) == _sha(SOURCE / name)
        for name in ("stream_metrics.parquet", "cell_summary.csv", "verification.json")
    }
    source_matches = {
        rel: _sha(ROOT / rel) == expected for rel, expected in manifest["source_sha256"].items()
    }
    return {
        "scope": "Archived stream and eligibility arithmetic; historical Q3 replay receipt checked but not rerun",
        "stream_rows": len(detail),
        "cells": rows,
        "q2_triggered_attempts": int(q2.monitor_triggered.sum()),
        "q2_selected_attempts": int(q2.scout_selected_candidate.sum()),
        "q3_promoted_attempts": int(q3.candidate_promoted.sum()),
        "q3_min_oracle_lower": float(scored.oracle_gain_lower.min()),
        "q3_oracle_radius": float(radius),
        "max_numeric_error": max_error,
        "historical_q3_replay_receipt": int(receipt["q3_streams_replayed"]),
        "source_hash_matching_audit_tree": source_matches,
        "v1_v2_same_bytes": predecessor_identical,
        "v1_runner_sha256": predecessor_manifest["source_sha256"][
            "src\\shiftlab\\dive\\integrated_pipeline.py"
        ],
        "v2_runner_sha256": manifest["source_sha256"][
            "src\\shiftlab\\dive\\integrated_pipeline.py"
        ],
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"{result['stream_rows']} streams, {len(result['cells'])} cells, max error {result['max_numeric_error']}"
    )
