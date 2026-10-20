import numpy as np
from sklearn.linear_model import Ridge

from .metrics import decision_cost


def fit_ridge(X, y, alpha=1.0):
    return Ridge(alpha=alpha).fit(X, y)


def weighted_conformal_quantile(scores, alpha=0.1):
    """Ordinary split-conformal quantile. NO shift validity is claimed."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    s = np.sort(np.asarray(scores))
    if s.ndim != 1 or np.any(~np.isfinite(s)) or np.any(s < 0):
        raise ValueError("scores must be finite nonnegative scalars")
    rank = int(np.ceil((len(s) + 1) * (1 - alpha)))
    return float(s[rank - 1]) if 0 < rank <= len(s) else np.inf


def exponentially_weighted_conformal_quantile(scores, ages, alpha=0.1, half_life=100.0):
    """Recency-weighted empirical radius with one unit of test-point mass.

    This is an adaptive heuristic under drift, not a distribution-free online guarantee.
    Ages are measured in the same units as ``half_life`` and must be nonnegative.
    """
    s, age = np.asarray(scores, dtype=float), np.asarray(ages, dtype=float)
    if (
        not 0 < alpha < 1
        or not np.isfinite(half_life)
        or half_life <= 0
        or s.ndim != 1
        or age.shape != s.shape
        or not np.isfinite(s).all()
        or not np.isfinite(age).all()
        or (s < 0).any()
        or (age < 0).any()
    ):
        raise ValueError(
            "Require valid alpha, positive half_life, finite scores and nonnegative ages"
        )
    if not len(s):
        return float("inf")
    weights = np.exp2(-age / half_life)
    order = np.argsort(s, kind="stable")
    cumulative = np.cumsum(weights[order])
    required_mass = (1 - alpha) * (weights.sum() + 1.0)
    index = int(np.searchsorted(cumulative, required_mass, side="left"))
    return float(s[order[index]]) if index < len(s) else float("inf")


def rolling_quantile(scores, width=250, alpha=0.1):
    q = np.empty(len(scores))
    for t in range(len(scores)):
        if t == 0:
            q[t] = np.inf
        else:
            q[t] = weighted_conformal_quantile(scores[max(0, t - width) : t], alpha)
    return q


def best_cost_threshold(y, pred, fn_cost=5.0, fp_cost=1.0):
    """Illustrative supervised decision threshold; fit only on training/calibration data."""
    grid = np.quantile(pred, np.linspace(0, 1, 101))
    scores = [decision_cost(y, pred - thr, fn_cost=fn_cost, fp_cost=fp_cost) for thr in grid]
    return float(grid[int(np.argmin(scores))])
