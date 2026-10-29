import pytest

from scripts.optimize_switching_onset_mixture import optimize_weights


def test_loss_aware_mixture_improves_registered_high_signal_bound():
    result = optimize_weights(
        horizon=120,
        budget=20,
        epsilon=0.49,
        alpha=0.05,
        delay=1,
    )

    assert sum(result.weights) == pytest.approx(1.0)
    assert all(weight > 0 for weight in result.weights)
    assert max(result.cell_bounds) == pytest.approx(57.224508, abs=1e-6)
    assert result.regret_horizon < result.uniform_bound < result.infinite_prior_bound


def test_registered_moderate_signal_cell_remains_vacuous():
    result = optimize_weights(
        horizon=120,
        budget=20,
        epsilon=0.1,
        alpha=0.05,
        delay=1,
    )

    assert result.regret_horizon == pytest.approx(120.0)
    assert result.uniform_bound == pytest.approx(120.0)
    assert result.infinite_prior_bound == pytest.approx(120.0)
