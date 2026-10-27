import math

import numpy as np
import pytest

from shiftlab.dive.horizon_edetectors import HorizonCalibratedEDetector


def _brute_force_statistics(factors: list[float]) -> tuple[float, float]:
    started_products = [float(np.prod(factors[start:])) for start in range(len(factors))]
    return sum(started_products), max(started_products)


@pytest.mark.parametrize("kind,index", [("sr", 0), ("cusum", 1)])
def test_recursion_matches_brute_force_started_products_with_skips(kind, index):
    bound = 2.0
    stakes = (0.25, 0.75)
    weights = (0.4, 0.6)
    events = [(1.0, False), (None, True), (-0.5, False), (2.0, False)]
    factors_by_stake = [[] for _ in stakes]
    detector = HorizonCalibratedEDetector(
        bound=bound,
        horizon=len(events),
        alpha=0.1,
        kind=kind,
        stakes=stakes,
        weights=weights,
    )

    for value, skip in events:
        detector.update(value, skip=skip)
        for factors, stake in zip(factors_by_stake, stakes, strict=True):
            factors.append(1.0 if skip else 1 + stake * value / bound)
        expected_components = [
            _brute_force_statistics(factors)[index] for factors in factors_by_stake
        ]
        expected_mixture = sum(
            weight * statistic
            for weight, statistic in zip(weights, expected_components, strict=True)
        )
        assert detector.log_statistic == pytest.approx(math.log(expected_mixture))
        assert detector.component_log_statistics == pytest.approx(
            tuple(math.log(statistic) for statistic in expected_components)
        )


def test_cusum_statistic_is_never_larger_than_sr_for_same_factors():
    sr = HorizonCalibratedEDetector(bound=1, horizon=5, stakes=(0.2, 0.8))
    cusum = HorizonCalibratedEDetector(bound=1, horizon=5, kind="cusum", stakes=(0.2, 0.8))
    for value, skip in ((0.5, False), (None, True), (0.25, False), (-0.1, False), (0, False)):
        log_sr = sr.update(value, skip=skip)
        log_cusum = cusum.update(value, skip=skip)
        assert log_cusum <= log_sr + 1e-12


def test_sr_zero_factor_drops_old_starts_and_recovers_on_next_event():
    detector = HorizonCalibratedEDetector(bound=1, horizon=3, stakes=(1.0,))
    assert detector.update(-1.0) == -np.inf
    assert detector.component_log_statistics == (-np.inf,)
    assert detector.update(1.0) == pytest.approx(math.log(2.0))
    assert detector.component_log_statistics == pytest.approx((math.log(2.0),))


def test_threshold_and_alarm_use_horizon_over_alpha():
    detector = HorizonCalibratedEDetector(bound=1, horizon=5, alpha=0.2, stakes=(1.0,), kind="sr")
    assert detector.threshold == pytest.approx(25.0)
    assert detector.log_threshold == pytest.approx(math.log(25.0))
    assert not detector.alarm
    for _ in range(4):
        detector.update(1.0)
    assert detector.alarm
    assert detector.alarm_time == 4


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bound": 0, "horizon": 5},
        {"bound": 1, "horizon": 0},
        {"bound": 1, "horizon": True},
        {"bound": 1, "horizon": 5, "alpha": 0},
        {"bound": 1, "horizon": 5, "kind": "other"},
        {"bound": 1, "horizon": 5, "stakes": ()},
        {"bound": 1, "horizon": 5, "stakes": (0, 0.2)},
        {"bound": 1, "horizon": 5, "weights": (0.2, 0.2)},
    ],
)
def test_constructor_rejects_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        HorizonCalibratedEDetector(**kwargs)


def test_update_rejects_invalid_values_and_horizon_overrun():
    detector = HorizonCalibratedEDetector(bound=1, horizon=1)
    for value in (None, float("nan"), float("inf"), 1.01):
        with pytest.raises(ValueError):
            detector.update(value)
    detector.update(0.1)
    with pytest.raises(RuntimeError, match="horizon"):
        detector.update(0.1)


def test_skip_ignores_value_but_requires_boolean_flag():
    detector = HorizonCalibratedEDetector(bound=1, horizon=2, stakes=(0.5,))
    assert detector.update(float("nan"), skip=True) == pytest.approx(0.0)
    with pytest.raises(TypeError, match="boolean"):
        detector.update(0.1, skip=1)
