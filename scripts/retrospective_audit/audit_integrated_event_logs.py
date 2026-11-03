"""Stream archived integrated logs and reconcile event facts with seed metrics."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT.parent
    / "shift-research-starter/outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1"
)
DEST = ROOT / "docs/retrospective_audit_2026_11_01/INTEGRATED_EVENT_LOG_AUDIT.json"
LEARNER_COLUMNS = [
    "scenario",
    "seed",
    "method",
    "event_index",
    "feature_available_index",
    "prediction_decision_index",
    "stage",
    "action",
    "query_requested",
    "candidate_selection_available",
    "selected_candidate_id",
    "label_available_index",
    "observed_label",
    "q1_triggered_here",
    "promotion_certified_here",
    "rollback_triggered_here",
    "label_resource_units",
    "intervention_cost_units",
]
EVALUATOR_COLUMNS = [
    "scenario",
    "seed",
    "method",
    "event_index",
    "true_label",
    "deployed_action",
    "realized_incumbent_minus_deployed_gain",
    "expected_incumbent_minus_deployed_gain",
    "intervention_cost_units",
    "evaluator_only",
]


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run() -> dict[str, object]:
    learner = pq.ParquetFile(SOURCE / "learner_event_log.parquet")
    evaluator = pq.ParquetFile(SOURCE / "evaluator_event_log.parquet")
    metrics = pd.read_parquet(SOURCE / "integrated_pipeline_seed_metrics.parquet")
    keyed = metrics.set_index(["scenario", "seed", "method"])
    _check(keyed.index.is_unique, "duplicate seed metric key")
    _check(
        learner.metadata.num_row_groups == evaluator.metadata.num_row_groups == len(keyed),
        "row groups",
    )
    _check(
        learner.metadata.num_rows == evaluator.metadata.num_rows == len(keyed) * 3200, "event count"
    )
    seen: set[tuple[str, int, str]] = set()
    total_labels = 0
    selection_before_available = 0
    max_expected_error = 0.0
    max_realized_error = 0.0
    for group in range(len(keyed)):
        a = learner.read_row_group(group, columns=LEARNER_COLUMNS).to_pydict()
        b = evaluator.read_row_group(group, columns=EVALUATOR_COLUMNS).to_pydict()
        key = (a["scenario"][0], a["seed"][0], a["method"][0])
        _check(key in keyed.index and key not in seen, f"unknown/duplicate group {key}")
        seen.add(key)
        row = keyed.loc[key]
        events = np.arange(3200)
        for field in ("scenario", "seed", "method"):
            _check(len(set(a[field])) == len(set(b[field])) == 1, f"nonconstant key {key}")
            _check(a[field][0] == b[field][0], f"learner/evaluator key {key}")
        for field in ("event_index", "feature_available_index", "prediction_decision_index"):
            _check(np.array_equal(a[field], events), f"learner {field} {key}")
        _check(np.array_equal(b["event_index"], events), f"evaluator event index {key}")
        _check(all(b["evaluator_only"]), f"evaluator flag {key}")
        _check(a["stage"][:800] == ["fit_validation"] * 800, f"fit stage {key}")
        _check(a["stage"][800:1600] == ["incumbent_monitor"] * 800, f"monitor stage {key}")
        _check(a["stage"][2400:] == ["deployment_rollback"] * 800, f"deploy stage {key}")
        queried = np.asarray(a["query_requested"], dtype=bool)
        _check(np.array_equal(a["label_resource_units"], queried.astype(int)), f"label units {key}")
        _check(sum(queried) == int(row.total_labels) <= 640, f"label cap/count {key}")
        total_labels += int(sum(queried))
        for index in range(3200):
            if queried[index]:
                _check(a["label_available_index"][index] == index, f"label timing {key}/{index}")
                _check(
                    a["observed_label"][index] == b["true_label"][index],
                    f"observed label {key}/{index}",
                )
            else:
                _check(a["label_available_index"][index] is None, f"unqueried timing {key}/{index}")
                _check(a["observed_label"][index] is None, f"unqueried label {key}/{index}")
            if (
                a["selected_candidate_id"][index] is not None
                and not a["candidate_selection_available"][index]
            ):
                selection_before_available += 1
        _check(np.array_equal(a["action"], b["deployed_action"]), f"action {key}")
        _check(
            np.allclose(a["intervention_cost_units"], b["intervention_cost_units"], atol=0, rtol=0),
            f"cost {key}",
        )
        cost = sum(a["intervention_cost_units"])
        _check(abs(cost - float(row.intervention_cost)) < 1e-9, f"seed intervention cost {key}")
        expected = sum(b["expected_incumbent_minus_deployed_gain"]) - cost
        realized = sum(b["realized_incumbent_minus_deployed_gain"]) - cost
        max_expected_error = max(
            max_expected_error, abs(expected - float(row.expected_incremental_utility))
        )
        max_realized_error = max(
            max_realized_error, abs(realized - float(row.realized_incremental_utility))
        )
        _check(max_expected_error < 1e-8 and max_realized_error < 1e-8, f"seed utility {key}")
        trigger = [i for i, value in enumerate(a["q1_triggered_here"]) if value]
        rollback = [i for i, value in enumerate(a["rollback_triggered_here"]) if value]
        _check(
            trigger
            == ([] if pd.isna(row.monitor_trigger_event) else [int(row.monitor_trigger_event)]),
            f"trigger {key}",
        )
        _check(
            rollback == ([] if pd.isna(row.rollback_event) else [int(row.rollback_event)]),
            f"rollback {key}",
        )
    _check(len(seen) == len(keyed), "missing groups")
    _check(selection_before_available == 0, "candidate selection exposed before available")
    return {
        "scope": "Archived row groups and event-level arithmetic; not a simulator replay or proof of causal filtration",
        "seed_method_streams": len(seen),
        "learner_events": learner.metadata.num_rows,
        "evaluator_events": evaluator.metadata.num_rows,
        "queried_labels": total_labels,
        "candidate_id_before_available": selection_before_available,
        "max_expected_utility_error": max_expected_error,
        "max_realized_utility_error": max_realized_error,
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result)
