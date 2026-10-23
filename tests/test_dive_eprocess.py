import numpy as np
import pytest

from shiftlab.dive.eprocess import BoundedMeanEProcess, StartedMixtureEProcess
from shiftlab.dive.estimators import prediction_powered_bound, prediction_powered_estimate


def test_bounded_mean_eprocess_stays_one_at_zero_and_rejects_bound_violation():
    process = BoundedMeanEProcess(bound=1.0, alpha=0.05)
    assert process.log_e_value == pytest.approx(0.0)
    with pytest.raises(ValueError, match="bounded"):
        process.update(1.01)


def test_bounded_mean_eprocess_accepts_a_fixed_weighted_stake_mixture():
    process = BoundedMeanEProcess(bound=1.0, stakes=(0.01, 0.5), weights=(0.8, 0.2))
    process.update(0.5)
    expected = 0.8 * (1 + 0.01 * 0.5) + 0.2 * (1 + 0.5 * 0.5)
    assert np.exp(process.log_e_value) == pytest.approx(expected)
    with pytest.raises(ValueError, match="weights"):
        BoundedMeanEProcess(bound=1.0, stakes=(0.1, 0.2), weights=(0.2, 0.2))


def test_prespecified_start_mixture_does_not_change_before_first_start():
    mixture = StartedMixtureEProcess(bound=1.0, alpha=0.05, starts=(3, 7))
    assert mixture.log_e_value == pytest.approx(0.0)
    mixture.update(0.9)
    mixture.update(0.9)
    assert mixture.log_e_value == pytest.approx(0.0)
    mixture.update(0.9)
    assert mixture.log_e_value == pytest.approx(0.0)
    mixture.update(0.9)
    assert mixture.log_e_value > 0


def test_bounded_eprocess_null_crossing_is_small_in_independent_simulation():
    rng = np.random.default_rng(7)
    crossings = 0
    for _ in range(400):
        process = BoundedMeanEProcess(bound=1.0, alpha=0.05)
        for value in rng.choice([-1.0, 1.0], size=500):
            if process.update(float(value)) >= -np.log(0.05):
                crossings += 1
                break
    # A finite Monte Carlo check of a proof-level guarantee, not its replacement.
    assert crossings / 400 < 0.07


def test_fixed_worst_case_bound_remains_safe_with_feature_adaptive_query_rates():
    rng = np.random.default_rng(17)
    crossings = 0
    for _ in range(250):
        process = BoundedMeanEProcess(bound=prediction_powered_bound(1.0, 0.1), alpha=0.05)
        for _ in range(300):
            proxy = float(rng.uniform(-0.7, 0.7))
            propensity = 0.1 + 0.7 * abs(proxy)
            outcome = float(rng.choice([-1.0, 1.0]))
            queried = bool(rng.random() < propensity)
            estimate = prediction_powered_estimate(
                proxy, queried, outcome if queried else None, propensity
            )
            if process.update(estimate) >= -np.log(0.05):
                crossings += 1
                break
    assert crossings / 250 < 0.08


def test_log_spaced_stake_mixture_null_crossing_is_small_in_independent_simulation():
    rng = np.random.default_rng(37)
    stakes = tuple(np.geomspace(1 / 1024, 0.99, 13))
    crossings = 0
    for _ in range(300):
        process = BoundedMeanEProcess(bound=1.0, alpha=0.05, stakes=stakes)
        for value in rng.choice([-1.0, 1.0], size=500):
            if process.update(float(value)) >= -np.log(0.05):
                crossings += 1
                break
    assert crossings / 300 < 0.08
