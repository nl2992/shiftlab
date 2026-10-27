from __future__ import annotations

import itertools

import numpy as np
import pytest

from shiftlab.dive.certification_exponent_one_step import (
    ProjectedKellyOneStep,
    _projected_mle_bet,
    feasible_leaf_factors,
)


@pytest.mark.parametrize("target_action", [0, 1])
def test_bets_are_nonnegative_on_every_full_support_leaf(target_action: int) -> None:
    rng = np.random.default_rng(410 + target_action)
    for _ in range(300):
        # Sample the exact feasible polygon: lambda >= 0, |hedge| <= 1,
        # and |lambda + hedge| <= 1.
        hedge = rng.uniform(-1.0, 1.0)
        lambda_ = rng.uniform(0.0, 1.0 - hedge)
        factors = feasible_leaf_factors(lambda_, hedge, target_action=target_action)
        assert factors.shape == (4,)
        assert np.all(factors >= -1e-12)


def test_conditional_mean_factor_is_at_most_one_for_every_two_arm_null() -> None:
    # The null is theta_target <= theta_other. The fair action hedge has mean
    # zero under the fixed uniform logger, so every feasible predictable bet
    # has conditional mean 1 + lambda * (theta_target-theta_other)/2 <= 1.
    for target_action in (0, 1):
        for target_mean, other_mean, lambda_, hedge, shrinkage in itertools.product(
            np.linspace(0.0, 1.0, 11),
            np.linspace(0.0, 1.0, 11),
            (0.0, 0.2, 0.7, 1.0),
            (-0.5, 0.0, 0.5),
            (0.0, 0.5, 0.9),
        ):
            if target_mean > other_mean:
                continue
            if lambda_ < 0 or abs(hedge) > 1 or abs(lambda_ + hedge) > 1:
                continue
            expected_factor = 1.0 + shrinkage * lambda_ * (target_mean - other_mean) / 2.0
            assert expected_factor <= 1.0 + 1e-12


def test_projected_fit_matches_grid_optimum_on_interior_empirical_law() -> None:
    actions = np.array([1] * 40 + [0] * 40, dtype=np.int64)
    rewards = np.array([1] * 24 + [0] * 16 + [1] * 8 + [0] * 32, dtype=np.int64)
    lambda_, hedge = _projected_mle_bet(actions, rewards, target_action=1)

    def log_growth(lam: float, h: float) -> float:
        factors = feasible_leaf_factors(lam, h, target_action=1)
        counts = np.array([32, 8, 16, 24], dtype=np.float64)
        if np.any(factors <= 0.0):
            return float("-inf")
        return float(np.dot(counts, np.log(factors)))

    assert np.all(feasible_leaf_factors(lambda_, hedge, target_action=1) >= -1e-10)
    grid = [
        log_growth(lam, h)
        for lam in np.linspace(0, 2, 401)
        for h in np.linspace(-1, 1, 401)
        if abs(lam + h) <= 1.0 + 1e-12
    ]
    assert log_growth(lambda_, hedge) >= max(grid) - 2e-4


def test_stream_uses_predictable_refits_and_crosses_only_at_wealth_threshold() -> None:
    monitor = ProjectedKellyOneStep(target_action=1, alpha=0.05)
    updates = [
        monitor.update(action, reward)
        for action, reward in zip([0, 1, 0, 1, 1, 0], [0, 1, 0, 1, 1, 0], strict=True)
    ]
    assert [item.event for item in updates] == list(range(1, 7))
    assert updates[0].fitted_lambda == 0.0
    assert updates[1].fitted_lambda == 0.0
    assert updates[2].event == 3  # first refit is after two completed episodes
    assert all(item.factor >= 0.0 for item in updates)
    assert all(item.certified == (item.wealth >= 20.0) for item in updates)


@pytest.mark.parametrize("bad", [(-1, 0), (2, 0), (0, -1), (0, 2)])
def test_stream_rejects_nonbinary_events(bad: tuple[int, int]) -> None:
    with pytest.raises(ValueError, match="binary"):
        ProjectedKellyOneStep(target_action=1).update(*bad)
