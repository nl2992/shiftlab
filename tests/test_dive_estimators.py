import numpy as np
import pytest

from shiftlab.dive.estimators import (
    AdaptiveReliance,
    prediction_powered_bound,
    prediction_powered_estimate,
)


def test_prediction_powered_estimate_is_unbiased_under_known_bernoulli_sampling():
    z, h, q = -0.4, 0.15, 0.2
    draws = np.random.default_rng(42).binomial(1, q, size=100_000)
    estimates = [
        prediction_powered_estimate(h, bool(indicator), z if indicator else None, q)
        for indicator in draws
    ]
    assert abs(np.mean(estimates) - z) < 0.015


@pytest.mark.parametrize("q", [0.05, 0.1, 0.5, 1.0])
def test_prediction_powered_bound_covers_all_endpoint_combinations(q):
    bound = prediction_powered_bound(2.0, q)
    for z in (-2.0, 2.0):
        for h in (-2.0, 2.0):
            assert abs(h + (z - h) / q) <= bound + 1e-12
            assert abs(h) <= bound


def test_estimator_rejects_unobserved_outcome_and_nonpositive_propensity():
    with pytest.raises(ValueError, match="unqueried"):
        prediction_powered_estimate(0.0, False, 1.0, 0.5)
    with pytest.raises(ValueError, match="propensity"):
        prediction_powered_estimate(0.0, False, None, 0.0)


def test_adaptive_reliance_uses_only_past_pairs_and_updates_after_feedback():
    proxy = np.linspace(-1.0, 1.0, 20)
    observed = 0.5 * proxy + 0.01 * np.sin(np.arange(20))
    reliance = AdaptiveReliance(query_fraction=0.1).fit(proxy, observed)
    initial = reliance.reliance
    assert 0 <= initial <= reliance.max_reliance
    reliance.observe(proxy_value=0.9, observed_value=0.45)
    assert len(reliance.observed_values) == 21
