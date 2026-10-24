"""Utilities for replaying bounded-mean mixture e-processes on saved traces."""

from __future__ import annotations

import math

import numpy as np
from scipy.special import logsumexp

DEFAULT_STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)


def replay_mixture_log_e(
    values: np.ndarray,
    bounds: np.ndarray | float,
    *,
    alpha: float,
    stakes: tuple[float, ...] = DEFAULT_STAKES,
) -> np.ndarray:
    """Replay a fixed-stake mixture using fixed or history-predictable bounds.

    This computes wealth only. Validity still requires each bound to be
    predictable under the filtration in the asserted conditional-mean null.
    """
    observed = np.asarray(values, dtype=float)
    scale = np.asarray(bounds, dtype=float)
    bets = np.asarray(stakes, dtype=float)
    if observed.ndim != 1 or not len(observed) or not np.isfinite(observed).all():
        raise ValueError("values must be a nonempty finite one-dimensional array")
    if scale.ndim == 0:
        scale = np.full_like(observed, float(scale))
    if scale.shape != observed.shape or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError("bounds must be positive finite scalars or match values")
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")
    if bets.ndim != 1 or not len(bets) or not np.isfinite(bets).all():
        raise ValueError("stakes must be a nonempty finite one-dimensional array")
    if np.any((bets <= 0) | (bets > 1)):
        raise ValueError("stakes must lie in (0, 1]")
    if np.any(np.abs(observed) > scale + 1e-10):
        raise ValueError("a value is outside its declared bound")

    factors = 1 + (observed / scale)[:, None] * bets[None, :]
    if np.any(factors < -1e-12):
        raise ValueError("a betting factor is negative")
    with np.errstate(divide="ignore"):
        component_log_wealth = np.cumsum(np.log(np.maximum(factors, 0.0)), axis=0)
    return logsumexp(component_log_wealth - math.log(len(bets)), axis=1)


def first_crossing(log_e_values: np.ndarray, *, alpha: float) -> int | None:
    """Return the zero-based first crossing of the 1/alpha threshold."""
    values = np.asarray(log_e_values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("log_e_values must be a finite one-dimensional array")
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")
    hits = np.flatnonzero(values >= -math.log(alpha))
    return int(hits[0]) if len(hits) else None
