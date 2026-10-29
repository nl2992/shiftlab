"""Exact information/safety checks; no new-method or broad empirical claim."""

from fractions import Fraction as F
from itertools import product

import pytest

from shiftlab.dive.delayed_regime_information import (
    DelayedRegimeInformation,
    RegimeFeedback,
    RegimeModel,
)


def brute_posterior(model, time, observed):
    total, positive = F(0), F(0)
    for states in product((0, 1), repeat=time + 1):
        weight = model.prior1 if states[0] else 1 - model.prior1
        for s in range(1, time + 1):
            p = 1 - model.transition10 if states[s - 1] else model.transition01
            weight *= p if states[s] else 1 - p
        for s, y in observed.items():
            p = model.emission1 if states[s] else model.emission0
            weight *= p if y else 1 - p
        total += weight
        positive += weight * states[-1]
    return positive / total


@pytest.mark.parametrize("transition", [(F(1, 10), F(1, 10)), (F(1, 5), F(2, 5)), (0, 0)])
@pytest.mark.parametrize("labels", [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_delayed_filter_matches_hidden_path_enumeration_with_skipped_queries(transition, labels):
    model = RegimeModel(transition01=transition[0], transition10=transition[1], prior1=F(1, 3))
    learner = DelayedRegimeInformation(horizon=7, budget=2, delay=2, model=model)
    requested = {1: labels[0], 4: labels[1]}
    observed = {}
    for time in range(1, 8):
        feedback = []
        if time - 2 in requested:
            s = time - 2
            observed[s] = requested[s]
            feedback = [RegimeFeedback(s, requested[s])]
        learner.start_round(time, feedback)
        assert learner.current_probability1 == brute_posterior(model, time, observed)
        if time in requested:
            learner.request()
    assert learner.requested == learner.observed == 2


def test_feedback_and_budget_validation_are_atomic():
    learner = DelayedRegimeInformation(horizon=5, budget=2, delay=2, model=RegimeModel())
    with pytest.raises(ValueError, match="start a round"):
        learner.request()
    learner.start_round(1)
    learner.request()
    with pytest.raises(ValueError, match="already requested"):
        learner.request()
    with pytest.raises(ValueError, match="exact availability"):
        learner.start_round(2, [RegimeFeedback(1, 1)])
    assert learner.round == 1 and learner.observed == 0
    learner.start_round(2)
    learner.request()
    for rows in ([], [RegimeFeedback(1, 2)], [RegimeFeedback(1, 1)] * 2):
        with pytest.raises(ValueError):
            learner.start_round(3, rows)
    learner.start_round(3, [RegimeFeedback(1, 1)])
    with pytest.raises(ValueError, match="exhausted"):
        learner.request()
    learner.start_round(4, [RegimeFeedback(2, 0)])
    with pytest.raises(ValueError, match="outstanding"):
        learner.start_round(5, [RegimeFeedback(2, 0)])
    learner.start_round(5)


def test_after_horizon_pending_labels_are_charged_but_not_observed():
    learner = DelayedRegimeInformation(horizon=2, budget=2, delay=3, model=RegimeModel())
    for time in (1, 2):
        learner.start_round(time)
        learner.request()
    assert learner.pending_events == (1, 2)
    assert learner.observed == 0 and learner.e_value == 1
    with pytest.raises(ValueError, match="within the horizon"):
        learner.start_round(3)


@pytest.mark.parametrize("dependent_null", [False, True])
def test_exact_short_null_calculation_with_adaptive_querying(dependent_null):
    horizon, budget, delay = 8, 6, 2
    wealth = [F(0)] * horizon
    crossing = F(0)
    for labels in product((0, 1), repeat=horizon):
        weight = F(1)
        for i, y in enumerate(labels):
            p = F(1, 4) if dependent_null and i and labels[i - 1] == 0 else F(1, 2)
            weight *= p if y else 1 - p
        learner = DelayedRegimeInformation(
            horizon=horizon,
            budget=budget,
            delay=delay,
            model=RegimeModel(transition01=F(1, 20), transition10=F(1, 20)),
        )
        requests = set()
        crossed = False
        for time in range(1, horizon + 1):
            source = time - delay
            rows = [RegimeFeedback(source, labels[source - 1])] if source in requests else []
            learner.start_round(time, rows)
            wealth[time - 1] += weight * learner.e_value
            crossed = crossed or learner.e_value >= 2
            # A predictable adaptive rule uses only learner-visible quantities.
            if learner.requested < budget and (
                time % 2 or learner.current_positive_probability > F(1, 2)
            ):
                learner.request()
                requests.add(time)
        crossing += weight * crossed
        assert learner.requested <= budget
    assert all(w <= 1 for w in wealth)
    assert all(b <= a for a, b in zip([F(1), *wealth[:-1]], wealth, strict=True))
    assert crossing <= F(1, 2)


def test_large_historical_evidence_does_not_certify_current_benefit_after_reversal():
    model = RegimeModel()
    labels = [1] * 20 + [0] * 5
    learner = DelayedRegimeInformation(horizon=26, budget=25, delay=1, model=model)
    for time in range(1, 27):
        rows = [RegimeFeedback(time - 1, labels[time - 2])] if time > 1 else []
        learner.start_round(time, rows)
        if time <= 25:
            learner.request()
    assert learner.current_positive_probability < F(1, 2)
    assert learner.e_value > 10


def test_integer_transition_inputs_preserve_exact_arithmetic():
    model = RegimeModel(transition01=1, transition10=1, prior1=0)
    for time in range(6):
        probability = model.propagate(model.prior1, time)
        assert isinstance(probability, F)
        assert probability == time % 2


@pytest.mark.parametrize(
    "override",
    [
        {"transition01": F(-1, 10)},
        {"transition10": F(11, 10)},
        {"emission0": F(1, 2)},
        {"emission1": 1},
        {"prior1": 0.5},
    ],
)
def test_invalid_models_are_rejected(override):
    with pytest.raises(ValueError):
        RegimeModel(**override)
