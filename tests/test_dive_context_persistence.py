import numpy as np
import pytest

from shiftlab.dive.budgeted_promotion import (
    BudgetedPromotionConfig,
    _inject_context_heterogeneity,
)
from shiftlab.dive.promotion_grid import _time_splits


def test_persistent_context_is_stationary_and_preserves_eventwise_null():
    prevalence = 0.30
    persistence = 0.85
    config = BudgetedPromotionConfig(
        n=12_000,
        d=4,
        context_feature_index=3,
        context_target_prevalence=prevalence,
        context_signal_strength=0.0,
        context_proxy_error=0.0,
        context_persistence=persistence,
        scenario_subset=("candidate_context_heterogeneity",),
        device="cpu",
    )
    config.validate()
    features = np.random.default_rng(91).normal(size=(config.n, config.d))
    labels = np.zeros(config.n, dtype=int)
    probability = np.full(config.n, 1 / 6)
    x, _, probability = _inject_context_heterogeneity(
        x=features,
        y=labels,
        probability_true=probability,
        seed=92,
        config=config,
        device="cpu",
    )

    _, validation_end, _ = _time_splits(config.n)
    context = x[validation_end:, config.context_feature_index] > 0
    empirical_prevalence = float(context.mean())
    lag_one_correlation = float(np.corrcoef(context[:-1], context[1:])[0, 1])
    assert empirical_prevalence == pytest.approx(prevalence, abs=0.04)
    assert lag_one_correlation == pytest.approx(persistence, abs=0.03)
    assert np.allclose(probability[validation_end:], 1 / 6)


def test_context_persistence_must_be_a_valid_markov_correlation():
    with pytest.raises(ValueError, match="context_persistence"):
        BudgetedPromotionConfig(context_persistence=1.0).validate()


def test_context_prevalence_can_shift_at_certification_without_decision_harm():
    start_prevalence, end_prevalence = 0.15, 0.85
    config = BudgetedPromotionConfig(
        n=12_000,
        d=4,
        context_feature_index=3,
        context_target_prevalence=start_prevalence,
        context_signal_strength=0.0,
        context_proxy_error=0.0,
        context_certification_prevalence=end_prevalence,
        device="cpu",
    )
    config.validate()
    features = np.random.default_rng(101).normal(size=(config.n, config.d))
    labels = np.zeros(config.n, dtype=int)
    probability = np.full(config.n, 1 / 6)
    x, _, probability = _inject_context_heterogeneity(
        x=features,
        y=labels,
        probability_true=probability,
        seed=102,
        config=config,
        device="cpu",
    )

    _, validation_end, monitor_end = _time_splits(config.n)
    certification_start = validation_end + (monitor_end - validation_end) // 2
    context = x[:, config.context_feature_index] > 0
    assert context[validation_end:certification_start].mean() == pytest.approx(
        start_prevalence, abs=0.04
    )
    assert context[certification_start:monitor_end].mean() == pytest.approx(
        end_prevalence, abs=0.04
    )
    assert np.allclose(probability[validation_end:], 1 / 6)


def test_context_prevalence_shift_rejects_invalid_or_persistent_configurations():
    with pytest.raises(ValueError, match="context_certification_prevalence"):
        BudgetedPromotionConfig(context_certification_prevalence=1.0).validate()
    with pytest.raises(ValueError, match="mutually exclusive"):
        BudgetedPromotionConfig(
            context_persistence=0.5,
            context_certification_prevalence=0.5,
        ).validate()


def test_scout_bound_mode_is_validated():
    with pytest.raises(ValueError, match="scout_bound_mode"):
        BudgetedPromotionConfig(scout_bound_mode="unpredictable").validate()
    with pytest.raises(ValueError, match="uniform query policy"):
        BudgetedPromotionConfig(
            scout_bound_mode="eventwise_propensity",
            query_policies=("uniform", "variance"),
        ).validate()
