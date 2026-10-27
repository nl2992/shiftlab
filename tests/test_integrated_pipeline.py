"""Tests for the staged integrated development runner's information contract."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.special import ndtr

import shiftlab.dive.integrated_pipeline as integrated
from shiftlab.decision_harm_experiment import SCENARIOS


def test_integrated_boundary_stream_uses_fresh_stages_and_respects_total_budget():
    scenario = next(item for item in SCENARIOS if item.name == "boundary_local_harm")
    result = integrated.run_seed(scenario=scenario, seed=2026102700, device="cpu")

    assert result["monitor_triggered"]
    assert result["scout_cert_ran"]
    assert result["monitor_trigger_event"] >= integrated.STAGES["fit_end"]
    assert result["monitor_trigger_event"] < integrated.STAGES["monitor_end"]
    assert result["monitor_events_processed"] <= (
        integrated.STAGES["monitor_end"] - integrated.STAGES["fit_end"]
    )
    assert result["monitor_labels"] <= integrated.MONITOR_LABEL_CAP
    assert result["scout_cert_labels"] <= result["scout_cert_label_cap"]
    expected_scout_cap = min(
        integrated.SCOUT_CERT_LABEL_CAP,
        integrated.TOTAL_LABEL_CAP - result["monitor_labels"] - integrated.ROLLBACK_LABEL_CAP,
    )
    assert result["scout_cert_label_cap"] == expected_scout_cap
    assert result["total_labels"] <= integrated.TOTAL_LABEL_CAP
    assert not result["rollback_event"]
    assert result["candidate_promoted"] == result["scout_certified"]
    if result["candidate_promoted"]:
        assert result["scout_selected_candidate"]


def test_oracle_expected_costs_do_not_change_integrated_decisions(monkeypatch):
    scenario = next(item for item in SCENARIOS if item.name == "boundary_local_harm")
    original = integrated._fit_candidate_family
    base = integrated.run_seed(scenario=scenario, seed=2026102700, device="cpu")

    def mutate_evaluator_oracle(**kwargs):
        family = original(**kwargs)
        family["h_truth"] = np.full_like(family["h_truth"], 1e9)
        return family

    monkeypatch.setattr(integrated, "_fit_candidate_family", mutate_evaluator_oracle)
    changed = integrated.run_seed(scenario=scenario, seed=2026102700, device="cpu")

    for key in (
        "monitor_trigger_event",
        "scout_cert_ran",
        "candidate_promoted",
        "candidate_by_context",
        "scout_cert_labels",
        "rollback_event",
        "rollback_labels",
        "total_labels",
    ):
        assert base[key] == changed[key]
    assert (
        changed["scout_expected_net_gain_on_certification"]
        != base["scout_expected_net_gain_on_certification"]
    )


def test_rollback_after_label_maturity_takes_effect_on_next_event():
    active = integrated._candidate_active_mask(100, 105, rollback_alarm_index=102)

    assert active.tolist() == [True, True, True, False, False]


def test_controller_uses_only_queried_certification_outcomes_and_respects_certificate():
    family = {
        "contexts": np.zeros(8, dtype=int),
        "incumbent": np.zeros(8, dtype=int),
        "actions": np.ones((1, 8), dtype=int),
    }
    labels = np.asarray([0, 0, 0, 1, 0, 1, 0, 0], dtype=int)
    uniforms = np.asarray([0.9, 0.9, 0.9, 0.1, 0.9, 0.1, 0.9, 0.9])
    action, estimate = integrated._controller_decision(
        family=family,
        y=labels,
        selected_by_context={0: 0},
        certification_start=3,
        certification_events=4,
        query_uniforms=uniforms,
        query_rate=0.5,
        fn_cost=1.0,
        fp_cost=1.0,
        deployment_horizon=8,
        promotion_certified=True,
    )
    assert action.value == "promote"
    assert estimate == 8.0

    changed_unqueried = labels.copy()
    changed_unqueried[[4, 6]] = 1
    action_changed, estimate_changed = integrated._controller_decision(
        family=family,
        y=changed_unqueried,
        selected_by_context={0: 0},
        certification_start=3,
        certification_events=4,
        query_uniforms=uniforms,
        query_rate=0.5,
        fn_cost=1.0,
        fp_cost=1.0,
        deployment_horizon=8,
        promotion_certified=True,
    )
    assert (action_changed, estimate_changed) == (action, estimate)

    blocked, _ = integrated._controller_decision(
        family=family,
        y=labels,
        selected_by_context={0: 0},
        certification_start=3,
        certification_events=4,
        query_uniforms=uniforms,
        query_rate=0.5,
        fn_cost=1.0,
        fp_cost=1.0,
        deployment_horizon=8,
        promotion_certified=False,
    )
    assert blocked.value == "continue"


def test_post_promotion_reversal_is_future_only_and_can_trigger_rollback():
    scenario = next(item for item in SCENARIOS if item.name == "harmful_adaptation")
    seed = 2026102700
    before_reversal = integrated.run_seed(
        scenario=scenario,
        seed=seed,
        device="cpu",
        method="full_pipeline",
        profile="harmful_adaptation_at_monitor",
    )
    after_reversal = integrated.run_seed(
        scenario=scenario,
        seed=seed,
        device="cpu",
        method="full_pipeline",
        profile="post_promotion_reversal",
    )

    for key in (
        "monitor_trigger_event",
        "candidate_promoted",
        "candidate_by_context",
        "scout_cert_labels",
    ):
        assert before_reversal[key] == after_reversal[key]
    assert after_reversal["candidate_promoted"]
    assert after_reversal["rollback_event"] >= integrated.STAGES["scout_cert_end"]
    assert after_reversal["rollback_queried_harm_events_evaluator"] > 0
    assert after_reversal["rollback_labels"] <= integrated.ROLLBACK_LABEL_CAP


def test_native_harmful_adaptation_starts_after_q1_monitor_window():
    scenario = next(item for item in SCENARIOS if item.name == "harmful_adaptation")
    result = integrated.run_seed(
        scenario=scenario,
        seed=2026102700,
        device="cpu",
        method="full_pipeline",
        profile="harmful_adaptation_native",
    )

    assert result["scenario"] == "harmful_adaptation_native"
    assert not result["monitor_triggered"]
    assert not result["scout_cert_ran"]


def test_integrated_candidate_null_family_is_nonidentical_and_pointwise_nonimproving():
    from scipy.special import ndtri

    score_cut = 0.3 * ndtri(1.0 / 6.0)
    scores = np.asarray([score_cut - 0.05, score_cut, score_cut + 0.05, score_cut + 0.3])
    x = np.zeros((len(scores), 16), dtype=float)
    x[:, 0] = scores
    family = {
        "actions": np.ones((4, len(scores)), dtype=int),
        "incumbent": np.ones(len(scores), dtype=int),
    }
    probability = ndtr(scores / 0.3)

    integrated._install_pointwise_null_candidate_family(
        x=x,
        family=family,
        probability_hat=probability,
        probability_true=probability,
        fn=5.0,
        fp=1.0,
    )

    assert np.all(family["actions"][:, 0] == 1)
    assert np.any(family["actions"] != family["incumbent"][None, :])
    expected_gain = (1 - probability[None, :]) * family["z0"] + probability[None, :] * family["z1"]
    assert np.all(expected_gain <= 1e-12)


def test_fixed_candidate_certification_uses_fresh_labels_without_scout():
    scenario = next(item for item in SCENARIOS if item.name == "boundary_local_harm")
    result = integrated.run_seed(
        scenario=scenario,
        seed=2026102700,
        device="cpu",
        method="fixed_candidate_certification",
    )

    assert not result["monitor_triggered"]
    assert result["monitor_events_processed"] == 0
    assert result["scout_cert_ran"]
    assert result["scout_events_processed"] == 0
    assert result["candidate_selection_source"] == "initial_validation_fixed"
    assert result["scout_cert_labels"] <= result["scout_cert_label_cap"]
    assert result["total_labels"] <= integrated.TOTAL_LABEL_CAP
    learner = pd.DataFrame(result["learner_event_log"])
    q2 = learner[
        learner.event_index.between(
            integrated.STAGES["monitor_end"], integrated.STAGES["scout_cert_end"] - 1
        )
    ]
    assert not q2.query_stage.eq("candidate_scout").any()
    assert q2.candidate_selection_available.all()
    assert q2.selected_candidate_id.notna().all()


def test_full_fixed_certification_runs_q1_before_fresh_certification():
    scenario = next(item for item in SCENARIOS if item.name == "harmful_adaptation")
    result = integrated.run_seed(
        scenario=scenario,
        seed=2026102700,
        device="cpu",
        method="full_pipeline_fixed_certification",
        profile="harmful_adaptation_at_monitor",
    )

    assert result["monitor_triggered"]
    assert result["candidate_selection_source"] == "initial_validation_fixed"
    assert result["scout_cert_ran"]
    assert result["scout_events_processed"] == 0
    assert result["scout_cert_labels"] <= result["scout_cert_label_cap"]
    assert result["total_labels"] <= integrated.TOTAL_LABEL_CAP
