import numpy as np
import torch

from shiftlab.dive.upf_retraining import (
    PerformanceObservation,
    build_upf_features,
    fit_available_performance_forecaster,
    fit_beta_performance_forecaster,
    upf_retraining_schedule,
)


def test_beta_forecaster_returns_valid_bounded_parameters():
    features = np.array(
        [[0, 1, 1, 0.0], [0, 2, 2, 0.1], [1, 2, 1, 0.1], [0, 3, 3, 0.2]],
        dtype=np.float64,
    )
    losses = np.array([0.8, 0.65, 0.55, 0.45], dtype=np.float64)
    forecaster = fit_beta_performance_forecaster(features, losses, seed=3)

    alpha, beta = forecaster.predict_beta_parameters(
        np.array([[0, 4, 4, 0.2], [3, 4, 1, 0.2]], dtype=np.float64)
    )

    assert forecaster.n_observations == 4
    assert alpha.shape == beta.shape == (2,)
    assert np.isfinite(alpha).all() and np.isfinite(beta).all()
    assert np.all(alpha > 0) and np.all(beta > 0)


def test_upf_features_use_paper_indices_and_shift_summary():
    features = build_upf_features(np.array([0, 2]), np.array([3, 3]), np.array([0.25, 0.5]))

    assert features.tolist() == [[0.0, 3.0, 3.0, 0.25], [2.0, 3.0, 1.0, 0.5]]


def test_forecaster_excludes_unmatured_performance_entries():
    observations = [
        PerformanceObservation(i, j, 0.1 * j, loss, j)
        for j, losses in enumerate(([0.8], [0.6, 0.7], [0.4, 0.5, 0.6]), start=1)
        for i, loss in enumerate(losses)
    ]
    observations.append(PerformanceObservation(0, 3, 0.3, 0.1, 5))

    forecaster = fit_available_performance_forecaster(observations, max_available_period=3, seed=4)

    assert forecaster.n_observations == 6


def test_quantile_recursion_retrains_only_when_total_cost_quantile_improves():
    alpha = np.array([[99.0], [1.0]])
    beta = np.array([[1.0], [99.0]])
    device = "cuda" if torch.cuda.is_available() else "cpu"

    schedule, margin = upf_retraining_schedule(
        alpha,
        beta,
        retraining_cost=0.1,
        monte_carlo_draws=2_000,
        seed=19,
        device=device,
    )

    assert schedule[1, 0]
    assert margin[1, 0] > 0


def test_quantile_recursion_respects_explicit_retraining_cost():
    alpha = np.array([[99.0], [1.0]])
    beta = np.array([[1.0], [99.0]])

    schedule, margin = upf_retraining_schedule(
        alpha,
        beta,
        retraining_cost=1.5,
        monte_carlo_draws=2_000,
        seed=19,
    )

    assert not schedule[1, 0]
    assert margin[1, 0] < 0
