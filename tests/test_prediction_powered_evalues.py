from __future__ import annotations

import pytest

from shiftlab.dive.prediction_powered_evalues import (
    PredictionPoweredEProcess,
    minimum_query_probability,
    prediction_powered_factor,
)


def test_betting_factor_query_floor_matches_published_formula() -> None:
    stake = 0.2
    lower, upper = 1 - stake, 1 + stake
    assert minimum_query_probability(lower=lower, upper=upper) == pytest.approx(
        2 * stake / (1 + stake)
    )
    assert minimum_query_probability(lower=lower, upper=upper) < 0.4


def test_ppe_factor_is_proxy_when_not_queried_and_corrected_when_queried() -> None:
    lower, upper = 0.8, 1.2
    proxy = 0.9
    observed = 1.1
    q = 0.4
    assert (
        prediction_powered_factor(
            proxy_factor=proxy,
            queried=False,
            propensity=q,
            lower=lower,
            upper=upper,
        )
        == proxy
    )
    assert prediction_powered_factor(
        proxy_factor=proxy,
        queried=True,
        propensity=q,
        lower=lower,
        upper=upper,
        observed_factor=observed,
    ) == pytest.approx(proxy + (observed - proxy) / q)


def test_query_correction_preserves_conditional_mean_exactly() -> None:
    """Averaging over query/no-query reveals the base factor in expectation."""
    q = 0.4
    proxy = 0.93
    observed = 1.08
    lower, upper = 0.8, 1.2
    queried_factor = prediction_powered_factor(
        proxy_factor=proxy,
        queried=True,
        propensity=q,
        lower=lower,
        upper=upper,
        observed_factor=observed,
    )
    not_queried_factor = prediction_powered_factor(
        proxy_factor=proxy,
        queried=False,
        propensity=q,
        lower=lower,
        upper=upper,
    )
    assert q * queried_factor + (1 - q) * not_queried_factor == pytest.approx(observed)


def test_propensity_floor_guarantees_nonnegative_extreme_correction() -> None:
    lower, upper = 0.6, 1.4
    q_min = minimum_query_probability(lower=lower, upper=upper)
    corrected = prediction_powered_factor(
        proxy_factor=upper,
        queried=True,
        propensity=q_min,
        lower=lower,
        upper=upper,
        observed_factor=lower,
    )
    assert corrected == pytest.approx(0.0)
    with pytest.raises(ValueError, match="below the PPE"):
        prediction_powered_factor(
            proxy_factor=upper,
            queried=True,
            propensity=q_min - 0.01,
            lower=lower,
            upper=upper,
            observed_factor=lower,
        )


def test_unqueried_outcome_cannot_be_passed_into_learner_update() -> None:
    process = PredictionPoweredEProcess(lower=0.8, upper=1.2)
    with pytest.raises(ValueError, match="must not be supplied"):
        process.update(
            proxy_factor=1.0,
            queried=False,
            propensity=0.4,
            observed_factor=1.1,
        )
    assert process.wealth == 1.0
    assert process.updates == []


def test_process_multiplies_validated_factors() -> None:
    process = PredictionPoweredEProcess(lower=0.8, upper=1.2)
    process.update(proxy_factor=0.9, queried=False, propensity=0.4)
    wealth = process.update(
        proxy_factor=1.0,
        queried=True,
        propensity=0.4,
        observed_factor=1.1,
    )
    assert wealth == pytest.approx(0.9 * 1.25)
    assert process.log_wealth == pytest.approx(__import__("math").log(wealth))
