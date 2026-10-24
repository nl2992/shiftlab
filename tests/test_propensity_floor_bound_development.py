from __future__ import annotations

import numpy as np
import pytest

from scripts.run_propensity_floor_bound_development import _alarm_outcomes, _analyze_trace
from shiftlab.dive.estimators import prediction_powered_bound
from shiftlab.dive.hard_budget import HardBudgetConfig
from shiftlab.dive.query import expected_cost_drift_bound


def test_registered_ppi_bounds_for_the_compared_floors():
    assert prediction_powered_bound(5.1, 0.10) == pytest.approx(96.9)
    assert prediction_powered_bound(5.1, 0.11) == pytest.approx(87.6272727273)


def test_eventwise_bound_reduces_to_registered_bound_at_constant_propensity():
    config = HardBudgetConfig(
        n=3200,
        d=16,
        budget_rate=0.20,
        q_min=0.10,
        q_max=0.80,
        harm_margin=0.10,
        generate_figure=False,
    )
    bound = prediction_powered_bound(5.1, 0.20)
    increments = (0.2, -0.1, 0.3, -0.2)
    trace = [
        {"event_offset": i, "propensity": 0.20, "ppi_increment": value}
        for i, value in enumerate(increments)
    ]
    result = _analyze_trace(
        {
            "processed_events": len(trace),
            "harm_onset_relative": None,
            "single_e_alarm_time": None,
            "eprocess_support_bound": bound,
        },
        trace,
        config,
    )
    assert result["eventwise_bound_mean"] == pytest.approx(bound)
    assert result["eventwise_bound_max"] == pytest.approx(bound)
    assert result["registered_bound_detected"] is False
    assert result["registered_bound_false_escalation"] is False


def test_covariate_dependent_scaling_can_break_a_marginal_null():
    # Z is equally likely to be +1 or -1, so E[Z]=0. If a current-context
    # bound is 1 on positive outcomes and 2 on negative outcomes, E[Z/B]=1/4.
    values = np.array([1.0, -1.0])
    bounds = np.array([1.0, 2.0])
    factors = 1 + 0.5 * values / bounds
    assert values.mean() == 0.0
    assert factors.mean() == pytest.approx(1.125)
    assert factors.mean() > 1.0


def test_selected_high_floor_preserves_cost_neutral_feasibility():
    budget_per_event = 0.20 * 1.4592557674706557
    bound = expected_cost_drift_bound(
        budget_per_event=budget_per_event,
        mixture_weight=1.0,
        cost_min=0.5,
        cost_max=2.5,
        q_min=0.11,
        q_max=0.80,
    )
    assert bound >= 0.0
    with pytest.raises(ValueError, match="infeasible"):
        expected_cost_drift_bound(
            budget_per_event=budget_per_event,
            mixture_weight=1.0,
            cost_min=0.5,
            cost_max=2.5,
            q_min=0.12,
            q_max=0.80,
        )


def test_floor_equal_to_target_query_rate_leaves_no_adaptive_rate_room():
    target = 0.20
    query_probabilities = np.array([target, target, target, target])
    assert np.all(query_probabilities >= target)
    assert query_probabilities.mean() == target
    assert np.all(query_probabilities == target)


def test_alarm_classification_keeps_no_onset_as_no_detection_not_false_alarm():
    assert _alarm_outcomes(None, None) == (False, False)
    assert _alarm_outcomes(4, None) == (False, True)
    assert _alarm_outcomes(4, 5) == (False, True)
    assert _alarm_outcomes(5, 5) == (True, False)
