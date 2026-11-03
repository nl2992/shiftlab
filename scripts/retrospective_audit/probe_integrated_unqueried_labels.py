"""Probe one archived-design stream for unqueried-label decision interference."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive import integrated_pipeline as pipeline

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "docs/retrospective_audit_2026_11_01/INTEGRATED_UNQUERIED_PROBE.json"
ARCHIVE = (
    ROOT.parent
    / "shift-research-starter/outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/integrated_pipeline_seed_metrics.parquet"
)
SEED = 2026104000
FIELDS = (
    "event_index",
    "feature_available_index",
    "prediction_decision_index",
    "stage",
    "policy_version",
    "action",
    "query_requested",
    "query_probability",
    "query_stage",
    "candidate_selection_available",
    "selected_candidate_id",
    "label_available_index",
    "observed_label",
    "q1_log_e_value",
    "certification_log_e_value",
    "rollback_log_e_value",
    "q1_triggered_here",
    "promotion_certified_here",
    "rollback_triggered_here",
    "controller_action",
    "label_resource_units",
    "intervention_cost_units",
)


def run() -> dict[str, object]:
    scenario = next(s for s in SCENARIOS if s.name == "boundary_local_harm")
    original_generate = pipeline._generate
    baseline = pipeline.run_seed(
        scenario=scenario, seed=SEED, device="cuda", method="full_pipeline"
    )
    archived = pd.read_parquet(ARCHIVE)
    archived = archived.loc[
        (archived.scenario == scenario.name)
        & (archived.seed == SEED)
        & (archived.method == "full_pipeline")
    ].iloc[0]
    for field in (
        "candidate_promoted",
        "total_labels",
        "monitor_trigger_event",
        "expected_incremental_utility",
    ):
        if abs(float(baseline[field]) - float(archived[field])) > 1e-9:
            raise AssertionError(f"CUDA baseline differs from archived {field}")
    uniform = np.random.default_rng(SEED + 700_001).random(3200)
    altered = (np.arange(3200) >= 800) & (uniform >= 0.4)

    def with_flipped_labels(mask: np.ndarray):
        def modified_generate(*args: object, **kwargs: object) -> tuple[object, ...]:
            generated = list(original_generate(*args, **kwargs))
            frame = generated[1].copy()
            target = frame["target"].to_numpy()
            frame.loc[mask, "target"] = np.where(target[mask] > 0, -1.0, 1.0)
            generated[1] = frame
            return tuple(generated)

        return modified_generate

    try:
        pipeline._generate = with_flipped_labels(altered)
        perturbed = pipeline.run_seed(
            scenario=scenario, seed=SEED, device="cuda", method="full_pipeline"
        )
        future = np.arange(3200) >= 2400
        pipeline._generate = with_flipped_labels(future)
        future_perturbed = pipeline.run_seed(
            scenario=scenario, seed=SEED, device="cuda", method="full_pipeline"
        )
    finally:
        pipeline._generate = original_generate

    before = baseline["learner_event_log"]
    after = perturbed["learner_event_log"]
    if len(before) != len(after) or len(before) != 3200:
        raise AssertionError("event log length changed")
    mismatches = []
    for event, (left, right) in enumerate(zip(before, after, strict=True)):
        for field in FIELDS:
            if left[field] != right[field]:
                mismatches.append((event, field))
    if mismatches:
        raise AssertionError(f"decision trace changed: {mismatches[:10]}")
    if sum(altered) < 1000:
        raise AssertionError("too few labels changed")
    if sum(a["query_requested"] for a in before if altered[a["event_index"]]) != 0:
        raise AssertionError("perturbation touched a queried label")
    future_before = before[:2400]
    future_after = future_perturbed["learner_event_log"][:2400]
    future_prefix_mismatches = [
        (event, field)
        for event, (left, right) in enumerate(zip(future_before, future_after, strict=True))
        for field in FIELDS
        if left[field] != right[field]
    ]
    if future_prefix_mismatches:
        raise AssertionError(
            f"future labels changed predeployment decisions: {future_prefix_mismatches[:10]}"
        )
    future_queried = sum(a["query_requested"] for a in before[2400:])
    if future_queried == 0:
        raise AssertionError("future perturbation did not include queried outcomes")
    return {
        "scope": "One archived CUDA stream and two fixed label perturbations; diagnostic only, not a filtration proof",
        "scenario": scenario.name,
        "seed": SEED,
        "method": "full_pipeline",
        "altered_unqueried_postfit_labels": int(sum(altered)),
        "learner_trace_events_compared": len(before),
        "decision_trace_field_mismatches": 0,
        "future_labels_flipped": 800,
        "future_queried_labels_flipped": future_queried,
        "predeployment_events_compared_after_future_flip": 2400,
        "predeployment_trace_field_mismatches": 0,
        "baseline_promoted": bool(baseline["candidate_promoted"]),
        "baseline_total_labels": int(baseline["total_labels"]),
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result)
