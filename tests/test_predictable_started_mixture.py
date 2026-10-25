import numpy as np
import pytest
from scipy.special import logsumexp

from shiftlab.dive.eprocess import PredictableBoundMeanEProcess, PredictableStartedMixtureEProcess


def test_predictable_started_mixture_matches_fixed_convex_combination():
    starts = (0, 2, 5)
    weights = (0.2, 0.3, 0.5)
    mixture = PredictableStartedMixtureEProcess(
        alpha=0.05, starts=starts, weights=weights, stakes=(0.2, 0.6)
    )
    components = [PredictableBoundMeanEProcess(alpha=0.05, stakes=(0.2, 0.6)) for _ in starts]
    values = (0.2, -0.1, 0.35, -0.2, 0.1, 0.4, -0.15)
    bounds = (1.0, 0.8, 0.7, 1.2, 0.6, 0.9, 1.1)
    for time, (value, bound) in enumerate(zip(values, bounds, strict=True)):
        for start, component in zip(starts, components, strict=True):
            if time >= start:
                component.update(value, bound=bound)
        observed = mixture.update(value, bound=bound)
        expected = logsumexp(
            [
                (component.log_e_value if time >= start else 0.0) + np.log(weight)
                for start, component, weight in zip(starts, components, weights, strict=True)
            ]
        )
        assert observed == pytest.approx(expected)
    assert mixture.alarm == (mixture.log_e_value >= -np.log(mixture.alpha))


@pytest.mark.parametrize("starts", [(), (1, 1), (2, 1)])
def test_predictable_started_mixture_rejects_invalid_starts(starts):
    with pytest.raises(ValueError):
        PredictableStartedMixtureEProcess(starts=starts)


def test_predictable_started_mixture_rejects_invalid_weights():
    with pytest.raises(ValueError, match="weights"):
        PredictableStartedMixtureEProcess(starts=(0, 1), weights=(0.4, 0.4))


def test_predictable_started_mixture_enforces_eventwise_bound():
    mixture = PredictableStartedMixtureEProcess(starts=(0, 3))
    with pytest.raises(ValueError, match="outside"):
        mixture.update(1.1, bound=1.0)
