import numpy as np
import pytest

from shiftlab.dive.budgeted_promotion import (
    BudgetedPromotionConfig,
    _context_prevalence_path,
    _inject_context_heterogeneity,
)
from shiftlab.dive.promotion_grid import _time_splits


@pytest.mark.parametrize("schedule", ["gradual_up", "gradual_down"])
def test_gradual_context_path_has_ordered_quartile_means(schedule):
    path = _context_prevalence_path(4000, schedule=schedule, low=0.1, high=0.9)
    means = np.array([chunk.mean() for chunk in np.split(path, 4)])
    if schedule == "gradual_down":
        means = means[::-1]
    assert np.all(np.diff(means) > 0)
    assert means == pytest.approx([0.2, 0.4, 0.6, 0.8], abs=0.001)


@pytest.mark.parametrize(
    ("schedule", "expected"),
    [
        ("recurring_low_first", [0.1, 0.9, 0.1, 0.9]),
        ("recurring_high_first", [0.9, 0.1, 0.9, 0.1]),
    ],
)
def test_recurring_context_path_revisits_each_prevalence(schedule, expected):
    path = _context_prevalence_path(4000, schedule=schedule, low=0.1, high=0.9)
    means = [chunk.mean() for chunk in np.split(path, 4)]
    assert means == pytest.approx(expected, abs=0.001)


def test_temporal_context_generator_preserves_eventwise_null_and_hides_latent_truth():
    n = 12_000
    x = np.zeros((n, 16), dtype=float)
    y = np.zeros(n, dtype=int)
    probability = np.full(n, 1 / 6)
    config = BudgetedPromotionConfig(
        n=n,
        d=x.shape[1],
        context_feature_index=2,
        context_target_prevalence=0.5,
        context_prevalence_schedule="gradual_up",
        context_proxy_error=0.0,
        context_signal_strength=0.0,
        device="cpu",
    ).validate()
    x_out, y_out, probability_out = _inject_context_heterogeneity(
        x=x,
        y=y,
        probability_true=probability,
        seed=817,
        config=config,
        device="cpu",
    )

    _, validation_end, _ = _time_splits(n)
    context = x_out[validation_end:, config.context_feature_index] == 1
    prevalence = [chunk.mean() for chunk in np.split(context, 4)]
    assert np.all(np.diff(prevalence) > 0)
    assert probability_out[validation_end:] == pytest.approx(1 / 6)
    assert set(np.unique(x_out[:, config.context_feature_index])) <= {-1.0, 1.0}
    assert set(np.unique(y_out)) <= {0, 1}


def test_temporal_context_schedule_cannot_be_combined_with_markov_persistence():
    with pytest.raises(ValueError, match="cannot be combined"):
        BudgetedPromotionConfig(
            context_prevalence_schedule="recurring_low_first",
            context_persistence=0.5,
        ).validate()


def test_temporal_context_schedule_rejects_unknown_mode():
    with pytest.raises(ValueError, match="context_prevalence_schedule"):
        BudgetedPromotionConfig(context_prevalence_schedule="random_walk").validate()
