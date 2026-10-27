import numpy as np
import pytest

from shiftlab.dive.eprocess import BoundedMeanEProcess
from shiftlab.dive.stratified_harm_eprocess import StratifiedEProcess


def test_fixed_mixture_matches_weighted_component_sum_and_untouched_stratum():
    process = StratifiedEProcess(
        bounds=(2.0, 4.0), weights=(0.25, 0.75), stakes=(0.5,), combination="mixture"
    )

    process.update(0, 1.0)
    first_log_e = np.log(1.0 + 0.5 * 1.0 / 2.0)
    np.testing.assert_allclose(process.component_log_e_values, (first_log_e, 0.0))
    expected_log_mixture = np.log(0.25 * np.exp(first_log_e) + 0.75)
    assert process.log_e_mixture == pytest.approx(expected_log_mixture)
    assert process.log_statistic == pytest.approx(expected_log_mixture)

    process.update(1, -2.0)
    second_log_e = np.log(1.0 + 0.5 * -2.0 / 4.0)
    assert process.component_log_e_values == pytest.approx((first_log_e, second_log_e))
    assert process.log_e_mixture == pytest.approx(
        np.log(0.25 * np.exp(first_log_e) + 0.75 * np.exp(second_log_e))
    )


def test_weighted_bonferroni_statistic_and_alarm_match_component_thresholds():
    process = StratifiedEProcess(
        bounds=(1.0, 2.0),
        alpha=0.2,
        weights=(0.25, 0.75),
        combination="bonferroni",
        stakes=(1.0,),
    )
    # The first component reaches e=2; its allocated threshold is 1/(.2*.25)=20.
    process.update(0, 1.0)
    assert process.adjusted_max_log_statistic == pytest.approx(np.log(max(0.25 * 2.0, 0.75)))
    assert not process.alarm
    # A second update makes the first component e=4, still below its threshold.
    process.update(0, 1.0)
    assert process.adjusted_max_log_statistic == pytest.approx(np.log(max(0.25 * 4.0, 0.75)))
    assert not process.alarm
    # At e=32 for component 0, equality with its allocated threshold is a crossing.
    process = StratifiedEProcess(
        bounds=(1.0,), alpha=1 / 32, combination="bonferroni", stakes=(1.0,)
    )
    for _ in range(5):
        process.update(0, 1.0)
    assert process.component_log_e_values[0] == pytest.approx(np.log(2.0**5))
    assert process.alarm


def test_single_stratum_mixture_is_the_existing_bounded_mean_process():
    kwargs = {"bound": 3.0, "alpha": 0.1, "stakes": (0.2, 0.7), "weights": (0.4, 0.6)}
    reference = BoundedMeanEProcess(**kwargs)
    stratified = StratifiedEProcess(
        bounds=(kwargs["bound"],),
        alpha=kwargs["alpha"],
        stakes=kwargs["stakes"],
        stake_weights=kwargs["weights"],
    )
    for value in (1.0, -0.5, 2.0):
        assert stratified.update(0, value) == pytest.approx(reference.update(value))
        assert stratified.log_e_mixture == pytest.approx(reference.log_e_value)
        assert stratified.alarm == reference.alarm


@pytest.mark.parametrize("bounds", [(), (0.0,), (-1.0,), (float("inf"),)])
def test_rejects_invalid_bounds(bounds):
    with pytest.raises(ValueError):
        StratifiedEProcess(bounds=bounds)


@pytest.mark.parametrize("weights", [(1.0, 0.0), (0.4, 0.5), (1.0,), (float("nan"), 0.5)])
def test_rejects_invalid_stratum_weights(weights):
    with pytest.raises(ValueError):
        StratifiedEProcess(bounds=(1.0, 2.0), weights=weights)


@pytest.mark.parametrize("stratum", [-1, 2, 0.5, True])
def test_rejects_invalid_stratum_index_without_advancing_component(stratum):
    process = StratifiedEProcess(bounds=(1.0, 2.0))
    with pytest.raises((TypeError, ValueError)):
        process.update(stratum, 0.0)
    assert process.component_log_e_values == (0.0, 0.0)


def test_component_bounds_are_fixed_and_out_of_range_values_rejected():
    process = StratifiedEProcess(bounds=(1.0, 2.0))
    assert process.bounds == (1.0, 2.0)
    with pytest.raises(AttributeError):
        process.bounds = (5.0, 5.0)
    with pytest.raises(ValueError):
        process.update(0, 1.01)
    assert process.component_log_e_values == (0.0, 0.0)
