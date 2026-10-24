from __future__ import annotations

import numpy as np

from scripts.analyze_pprm_block_mixture_confirmation import _holm, _paired_summary, _wilson
from scripts.calibrate_pprm_registered_null_scenarios import (
    _prediction_only_proxy,
    _vectorized_mixture_crossings,
)
from shiftlab.dive.eprocess import PPIBlockMixtureEProcess
from shiftlab.dive.proxy import DecisionLossProxy


def test_paired_summary_uses_matched_discordant_streams() -> None:
    result = _paired_summary(
        np.array([True, True, False, False]),
        np.array([True, False, True, False]),
    )
    assert result["streams"] == 4
    assert result["mixture_only"] == 1
    assert result["comparator_only"] == 1
    assert result["rate_difference_mixture_minus_comparator"] == 0
    assert result["difference_bootstrap_95_low"] <= 0 <= result["difference_bootstrap_95_high"]
    assert result["mcnemar_exact_p"] == 1


def test_holm_adjustment_is_monotone_and_never_below_raw_p() -> None:
    raw = [0.01, 0.04, 0.03]
    adjusted = _holm(raw)
    assert adjusted == [0.03, 0.06, 0.06]
    assert np.all(np.asarray(adjusted) >= raw)


def test_prediction_only_proxy_matches_full_proxy_ridge_predictions() -> None:
    rng = np.random.default_rng(24)
    x_train = rng.normal(size=(160, 8))
    z_train = rng.normal(size=160)
    x_validation = rng.normal(size=(60, 8))
    z_validation = rng.normal(size=60)
    full = DecisionLossProxy(seed=24, clip=5.1).fit(x_train, z_train, x_validation, z_validation)
    reduced = _prediction_only_proxy(seed=24, clip=5.1, x_train=x_train, z_train=z_train)
    np.testing.assert_allclose(reduced.predict(x_validation), full.predict(x_validation))


def test_zero_false_alarms_have_exact_zero_lower_wilson_bound() -> None:
    low, high = _wilson(0, 200)
    assert low == 0
    assert 0 < high < 0.03


def test_vectorized_registered_mixture_recursion_matches_scalar_production_process() -> None:
    rng = np.random.default_rng(73)
    estimates = rng.uniform(-0.1, 1.1, size=(4, 18))
    active = np.ones_like(estimates, dtype=bool)
    active[0, 11:] = False
    active[1, [2, 7, 14]] = False
    active[2, 4:] = False
    cm_crossed, mixture_crossed = _vectorized_mixture_crossings(estimates, active, device="cpu")
    expected_cm = []
    expected_mixture = []
    for row, row_active in zip(estimates, active, strict=True):
        monitor = PPIBlockMixtureEProcess(max_reliance=0.1, threshold=0.51, alpha=0.05)
        cm_alarm = mixture_alarm = False
        for value, is_active in zip(row, row_active, strict=True):
            if is_active:
                monitor.update(float(value))
                cm_alarm |= monitor.cm_eb.alarm
                mixture_alarm |= monitor.alarm_at_weight(0.1)
        expected_cm.append(cm_alarm)
        expected_mixture.append(mixture_alarm)
    np.testing.assert_array_equal(cm_crossed, expected_cm)
    np.testing.assert_array_equal(mixture_crossed, expected_mixture)
