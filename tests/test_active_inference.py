import itertools

import numpy as np
import pytest

from shiftlab.dive.active_inference import (
    active_inference_propensities,
    prediction_powered_mean,
)


def test_active_inference_propensities_match_expected_budget_and_mix():
    q = active_inference_propensities(
        np.asarray([0.1, 0.5, 1.0, 2.0]), expected_budget=2.0, uniform_mixture=0.5
    )
    assert q.sum() == pytest.approx(2.0)
    assert np.all(q > 0)
    assert np.all(np.diff(q) > 0)

    uniform = active_inference_propensities(
        np.asarray([0.1, 0.5, 1.0, 2.0]), expected_budget=2.0, uniform_mixture=1.0
    )
    np.testing.assert_allclose(uniform, 0.5)


def test_active_inference_all_zero_uncertainty_falls_back_to_uniform():
    q = active_inference_propensities(np.zeros(5), expected_budget=1.5)
    np.testing.assert_allclose(q, 0.3)


def test_prediction_powered_mean_is_unbiased_over_bernoulli_queries():
    predictions = np.asarray([0.2, 0.5, 0.8])
    outcomes = np.asarray([0.0, 1.0, 1.0])
    q = np.asarray([0.25, 0.5, 0.75])
    expected = outcomes.mean()
    mean_estimate = 0.0
    for queried_tuple in itertools.product((False, True), repeat=3):
        queried = np.asarray(queried_tuple)
        probability = np.prod(np.where(queried, q, 1 - q))
        observed = np.full(3, np.nan)
        observed[queried] = outcomes[queried]
        result = prediction_powered_mean(predictions, queried, observed, q)
        mean_estimate += probability * result["estimate"]
    assert mean_estimate == pytest.approx(expected)


def test_prediction_powered_mean_rejects_unqueried_label_leakage():
    with pytest.raises(ValueError, match="unqueried outcomes"):
        prediction_powered_mean(
            np.asarray([0.5, 0.5]),
            np.asarray([True, False]),
            np.asarray([1.0, 0.0]),
            np.asarray([0.5, 0.5]),
        )


def test_zero_uncertainty_with_small_mixture_keeps_positive_queries():
    q = active_inference_propensities(
        np.asarray([0.0, 0.0, 1.0, 2.0]), expected_budget=1.0, uniform_mixture=0.25
    )
    assert np.all(q > 0)
    assert q.sum() == pytest.approx(1.0)
