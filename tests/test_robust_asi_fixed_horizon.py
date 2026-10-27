import numpy as np
import pytest

from scripts.reproduce_robust_asi_acs import _influence_scale
from shiftlab.dive.robust_asi_fixed_horizon import (
    budgeted_probabilities,
    choose_robust_geometric_path,
    geometric_budget_path,
    robust_variance_objective,
)


def test_budgeted_probabilities_are_positive_and_use_exact_expected_budget():
    q = budgeted_probabilities(np.asarray([0.0, 0.1, 0.5, 1.0]), budget=1.5)
    assert np.all(q > 0)
    assert np.all(q <= 1)
    assert q.sum() == pytest.approx(1.5)
    assert q[0] < q[-1]


def test_geometric_path_has_active_and_uniform_endpoints_with_equal_budget():
    budget = 2.0
    active = budgeted_probabilities(np.asarray([0.1, 0.2, 1.0, 2.0]), budget=budget)
    at_active = geometric_budget_path(active, budget=budget, rho=0.0)
    at_uniform = geometric_budget_path(active, budget=budget, rho=1.0)
    np.testing.assert_allclose(at_active, active, rtol=1e-8, atol=1e-9)
    np.testing.assert_allclose(at_uniform, np.full(4, 0.5), rtol=1e-9, atol=1e-9)
    assert geometric_budget_path(active, budget=budget, rho=0.4).sum() == pytest.approx(budget)


def test_robust_path_choice_minimizes_declared_grid_objective():
    error = np.asarray([0.1, 0.3, 0.8, 1.2])
    grid = (0.0, 0.5, 1.0)
    q, rho, objective = choose_robust_geometric_path(
        error, budget=1.5, l2_radius=2.0, path_grid=grid
    )
    expected = min(
        robust_variance_objective(
            error,
            geometric_budget_path(budgeted_probabilities(error, budget=1.5), budget=1.5, rho=r),
            l2_radius=2.0,
        )
        for r in grid
    )
    assert objective == pytest.approx(expected)
    assert rho in grid
    assert q.sum() == pytest.approx(1.5)


def test_invalid_budget_and_probability_inputs_fail_closed():
    with pytest.raises(ValueError, match="budget"):
        budgeted_probabilities(np.ones(3), budget=0.0)
    with pytest.raises(ValueError, match="active probabilities"):
        geometric_budget_path(np.asarray([0.1, 0.1]), budget=1.0, rho=0.5)


def test_acs_influence_scale_preserves_relative_values_above_one():
    design = np.asarray([[1.0], [2.0], [4.0]])
    h = np.asarray([1.0])
    residual_scale = np.asarray([2.0, 2.0, 2.0])
    np.testing.assert_allclose(_influence_scale(residual_scale, design, h), [2.0, 4.0, 8.0])
