import numpy as np
import pytest

from shiftlab.monitoring import (
    HoeffdingExcessEProcess,
    conformal_upper_threshold,
    one_sided_cusum,
    rbf_gamma,
    rbf_mmd_squared,
)


def test_hoeffding_eprocess_matches_one_step_mixture_formula():
    process = HoeffdingExcessEProcess(
        epsilon=0.2,
        alpha=0.05,
        lower=-1.0,
        upper=1.0,
        lambdas=(0.1, 0.2),
    )
    log_evalue = process.update(0.7)
    increments = np.array([0.1, 0.2]) * (0.7 - 0.2) - np.array([0.1, 0.2]) ** 2 * 4 / 8
    expected = np.logaddexp.reduce(increments) - np.log(2)
    assert log_evalue == pytest.approx(expected)
    assert not process.alarm


def test_hoeffding_eprocess_rejects_unbounded_observed_costs():
    process = HoeffdingExcessEProcess(lower=-2, upper=2)
    with pytest.raises(ValueError, match="outside the declared bounded range"):
        process.update(2.01)


def test_bounded_eprocess_controls_null_crossing_in_independent_monte_carlo_check():
    rng = np.random.default_rng(20261022)
    false_alarms = 0
    n_streams = 1200
    for _ in range(n_streams):
        process = HoeffdingExcessEProcess(
            epsilon=0.5,
            alpha=0.05,
            lower=0.0,
            upper=1.0,
            lambdas=(0.1, 0.2, 0.4, 0.8),
        )
        for outcome in rng.binomial(1, 0.5, size=250):
            process.update(float(outcome))
        false_alarms += process.alarm
    # A Monte Carlo check of the theorem, not the theorem itself. The loose margin accounts for
    # finite simulation error; the implementation's guarantee comes from its stated assumptions.
    assert false_alarms / n_streams <= 0.07


def test_eprocess_has_power_on_strong_positive_excess_cost():
    process = HoeffdingExcessEProcess(
        epsilon=0.5,
        alpha=0.05,
        lower=0.0,
        upper=1.0,
        lambdas=(0.1, 0.2, 0.4, 0.8),
    )
    for outcome in [1.0] * 100:
        process.update(outcome)
    assert process.alarm


def test_mmd_and_cusum_validate_and_detect_large_changes():
    rng = np.random.default_rng(7)
    reference = rng.normal(size=(80, 3))
    current = rng.normal(loc=2.0, size=(80, 3))
    gamma = rbf_gamma(reference)
    shifted = rbf_mmd_squared(reference, current, gamma)
    stationary = rbf_mmd_squared(reference, reference.copy(), gamma)
    assert shifted > stationary
    path = one_sided_cusum([0.0, 0.0, 1.0, 1.0], baseline_mean=0.0, baseline_scale=0.5, slack=0.1)
    assert np.allclose(path, [0, 0, 1.9, 3.8])
    assert conformal_upper_threshold([1.0, 2.0, 3.0, 4.0], alpha=0.2) == 4.0
