import numpy as np
import pytest

from shiftlab.dive.pprm_risk_monitor import (
    PPRMBatchEstimate,
    PPRMRiskMonitor,
    PredictableReliance,
    prediction_powered_batch_risk,
    source_prediction_powered_values,
    source_risk_upper_bound_betting,
    source_risk_upper_bound_cm_eb,
)


def test_prediction_powered_estimator_matches_definition_and_support():
    true_loss = np.array([0.0, 1.0])
    proxy_labeled = np.array([0.0, 0.0])
    proxy_unlabeled = np.array([0.0, 1.0, 1.0, 1.0])

    result = prediction_powered_batch_risk(true_loss, proxy_labeled, proxy_unlabeled, reliance=0.5)

    assert result.estimate == pytest.approx(0.875)
    assert result.labeled_count == 2
    assert result.unlabeled_count == 4
    assert -0.5 <= result.estimate <= 1.5


def test_prediction_powered_estimator_rejects_invalid_inputs():
    with pytest.raises(ValueError, match="equal length"):
        prediction_powered_batch_risk(
            np.array([0.0]), np.array([0.0, 1.0]), np.array([0.0]), reliance=1
        )
    with pytest.raises(ValueError, match="nonempty"):
        prediction_powered_batch_risk(np.array([]), np.array([]), np.array([0.0]), reliance=1)
    with pytest.raises(ValueError, match="reliance"):
        prediction_powered_batch_risk(
            np.array([0.0]), np.array([0.0]), np.array([0.0]), reliance=-0.1
        )


def test_source_ppi_pairing_preserves_the_batch_estimator_mean():
    true_loss = np.array([0.0, 1.0])
    proxy_labeled = np.array([1.0, 0.0])
    proxy_unlabeled = np.array([0.0, 1.0, 0.0, 1.0])
    eta = 0.7

    per_sample = source_prediction_powered_values(
        true_loss, proxy_labeled, proxy_unlabeled, reliance=eta
    )
    batch = prediction_powered_batch_risk(true_loss, proxy_labeled, proxy_unlabeled, reliance=eta)

    assert per_sample.mean() == pytest.approx(batch.estimate)
    with pytest.raises(ValueError, match="divisible"):
        source_prediction_powered_values(
            true_loss, proxy_labeled, np.array([0.0, 1.0, 1.0]), reliance=eta
        )


def test_adaptive_reliance_is_history_predictable_and_capped():
    adaptive = PredictableReliance(window_rounds=2, max_reliance=0.8, initial_reliance=0.5)
    assert adaptive.choose(labeled_count=4, unlabeled_count=8) == 0.5
    labeled = np.array([0.0, 0.0, 1.0, 1.0])
    unlabeled_proxy = np.tile(labeled, 2)
    adaptive.update(labeled, labeled, unlabeled_proxy)

    chosen = adaptive.choose(labeled_count=4, unlabeled_count=8)

    assert chosen == pytest.approx(7 / 9)
    assert 0 <= chosen <= 0.8


def test_source_cm_eb_upper_bound_contains_empirical_mean():
    values = np.array([0.2, 0.4, 0.3, 0.5, 0.25, 0.35])

    upper = source_risk_upper_bound_cm_eb(
        values, max_reliance=0, alpha_source=0.05, lambda_count=64
    )

    assert values.mean() <= upper <= 1


def test_source_betting_upper_bound_contains_empirical_mean():
    values = np.array([0.2, 0.4, 0.3, 0.5, 0.25, 0.35])

    upper = source_risk_upper_bound_betting(
        values, max_reliance=0, alpha_source=0.05, grid_size=200
    )

    assert values.mean() <= upper <= 1


def test_source_betting_bound_matches_pinned_confseq_reference():
    # Reference values were generated with ConfSeq 5ffe733ca2447a2e28c2c91f3b00086173f2ab2c,
    # betting_cs(..., theta=0, running_intersection=False, breaks=1000).
    rng = np.random.default_rng(20261026)
    ordinary = rng.binomial(1, 0.31, size=80).astype(float)
    ppi = rng.uniform(-0.4, 1.4, size=80)
    all_low = np.zeros(80)

    assert source_risk_upper_bound_betting(
        ordinary, max_reliance=0, alpha_source=0.025, grid_size=1000
    ) == pytest.approx(0.503, abs=1e-12)
    assert source_risk_upper_bound_betting(
        ppi, max_reliance=0.4, alpha_source=0.025, grid_size=1000
    ) == pytest.approx(0.5774, abs=1e-12)
    assert source_risk_upper_bound_betting(
        all_low, max_reliance=0, alpha_source=0.025, grid_size=1000
    ) == pytest.approx(0.087, abs=1e-12)


def test_pprm_risk_monitor_uses_source_threshold_and_batch_sequence():
    monitor = PPRMRiskMonitor(
        source_upper_bound=0.1,
        tolerance=0.1,
        max_reliance=0,
        alpha_test=0.05,
        lambda_count=64,
    )
    batch = PPRMBatchEstimate(estimate=1.0, reliance=0.0, labeled_count=1, unlabeled_count=1)
    crossed = False
    for _ in range(300):
        crossed = monitor.update(batch)
        if crossed:
            break

    assert crossed
    assert monitor.lower_bound > monitor.threshold
    with pytest.raises(ValueError, match="maximum"):
        monitor.update(
            PPRMBatchEstimate(estimate=1.2, reliance=0.1, labeled_count=1, unlabeled_count=1)
        )
