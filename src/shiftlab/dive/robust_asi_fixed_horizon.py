"""Fixed-horizon robust active sampling for model-assisted inference.

Independent implementation of the geometric-path/l2-uncertainty-set
allocation in Li, Zrnic, and Candes (NeurIPS 2025). This module only selects
label propensities and does not provide a sequential-monitoring guarantee.
"""

from __future__ import annotations

import numpy as np


def _validated_scale(error_scale: np.ndarray) -> np.ndarray:
    scale = np.asarray(error_scale, dtype=np.float64).reshape(-1)
    if scale.size == 0 or not np.isfinite(scale).all() or np.any(scale < 0):
        raise ValueError("error_scale must be a nonempty finite nonnegative vector")
    return scale


def budgeted_probabilities(
    scores: np.ndarray,
    *,
    budget: float,
    min_probability: float = 1e-8,
) -> np.ndarray:
    """Normalize nonnegative scores to Bernoulli propensities with exact spend."""
    score = _validated_scale(scores)
    n = len(score)
    if not np.isfinite(budget) or not 0 < budget <= n:
        raise ValueError("budget must lie in (0, number of scores]")
    if not np.isfinite(min_probability) or not 0 < min_probability <= budget / n:
        raise ValueError("min_probability must lie in (0, budget / n]")
    if np.all(score == 0):
        return np.full(n, budget / n)

    positive = np.maximum(score, np.finfo(np.float64).tiny)
    low, high = 0.0, 1.0
    while np.clip(high * positive, min_probability, 1.0).sum() < budget:
        high *= 2.0
    for _ in range(80):
        middle = (low + high) / 2.0
        if np.clip(middle * positive, min_probability, 1.0).sum() < budget:
            low = middle
        else:
            high = middle
    probabilities = np.clip(((low + high) / 2.0) * positive, min_probability, 1.0)
    # The root is monotone and 80 bisection steps leave only floating-point error.
    if not np.isclose(probabilities.sum(), budget, rtol=1e-10, atol=1e-9):
        raise RuntimeError("could not normalize propensities to the requested budget")
    return probabilities


def geometric_budget_path(
    active_probabilities: np.ndarray,
    *,
    budget: float,
    rho: float,
    min_probability: float = 1e-8,
) -> np.ndarray:
    """Return a budget-preserving geometric interpolation to uniform sampling."""
    active = _validated_scale(active_probabilities)
    n = len(active)
    if not np.isfinite(rho) or not 0 <= rho <= 1:
        raise ValueError("rho must lie in [0, 1]")
    if not np.isfinite(budget) or not 0 < budget <= n:
        raise ValueError("budget must lie in (0, number of probabilities]")
    if np.any(active <= 0) or np.any(active > 1):
        raise ValueError("active probabilities must lie in (0, 1]")
    if not np.isclose(active.sum(), budget, rtol=1e-10, atol=1e-9):
        raise ValueError("active probabilities must use the requested expected budget")
    uniform = budget / n
    scores = np.exp((1.0 - rho) * np.log(active) + rho * np.log(uniform))
    return budgeted_probabilities(scores, budget=budget, min_probability=min_probability)


def robust_variance_objective(
    error_scale: np.ndarray,
    probabilities: np.ndarray,
    *,
    l2_radius: float,
) -> float:
    """Evaluate the paper's L2 worst-case residual-variance criterion.

    The criterion is ``mean(error_scale**2 / q) + radius * ||1/q||_2 / n``.
    It is an allocation objective, not a confidence bound.
    """
    error = _validated_scale(error_scale)
    q = np.asarray(probabilities, dtype=np.float64).reshape(-1)
    if len(q) != len(error) or not np.isfinite(q).all() or np.any(q <= 0) or np.any(q > 1):
        raise ValueError("probabilities must align with error_scale and lie in (0, 1]")
    if not np.isfinite(l2_radius) or l2_radius < 0:
        raise ValueError("l2_radius must be finite and nonnegative")
    n = len(q)
    return float(np.mean(np.square(error) / q) + l2_radius * np.linalg.norm(1.0 / q) / n)


def choose_robust_geometric_path(
    error_scale: np.ndarray,
    *,
    budget: float,
    l2_radius: float,
    path_grid: tuple[float, ...] = tuple(np.linspace(0.0, 1.0, 101)),
    min_probability: float = 1e-8,
) -> tuple[np.ndarray, float, float]:
    """Minimize the robust objective over a geometric active-to-uniform path."""
    error = _validated_scale(error_scale)
    if not np.isfinite(l2_radius) or l2_radius < 0:
        raise ValueError("l2_radius must be finite and nonnegative")
    if not path_grid or any(not np.isfinite(rho) or not 0 <= rho <= 1 for rho in path_grid):
        raise ValueError("path_grid must contain values in [0, 1]")
    active = budgeted_probabilities(error, budget=budget, min_probability=min_probability)
    rho_values = np.asarray(path_grid, dtype=np.float64)
    uniform = budget / len(error)
    raw = np.exp(
        (1.0 - rho_values[:, None]) * np.log(active)[None, :]
        + rho_values[:, None] * np.log(uniform)
    )
    low = np.zeros(len(rho_values), dtype=np.float64)
    high = np.ones(len(rho_values), dtype=np.float64)

    def normalize(scales: np.ndarray) -> np.ndarray:
        return np.clip(scales[:, None] * raw, min_probability, 1.0)

    while np.any(normalize(high).sum(axis=1) < budget):
        high *= 2.0
    for _ in range(80):
        middle = (low + high) / 2.0
        below_budget = normalize(middle).sum(axis=1) < budget
        low = np.where(below_budget, middle, low)
        high = np.where(below_budget, high, middle)
    probabilities_by_rho = normalize((low + high) / 2.0)
    estimates = np.square(error)[None, :] / probabilities_by_rho
    objectives = estimates.mean(axis=1) + (
        l2_radius * np.linalg.norm(1.0 / probabilities_by_rho, axis=1) / len(error)
    )
    best_index = int(np.argmin(objectives))
    probabilities = probabilities_by_rho[best_index]
    rho = float(rho_values[best_index])
    objective = float(objectives[best_index])
    if not np.isclose(probabilities.sum(), budget, rtol=1e-10, atol=1e-8):
        raise RuntimeError("selected geometric-path propensities do not meet the budget")
    return probabilities, rho, objective
