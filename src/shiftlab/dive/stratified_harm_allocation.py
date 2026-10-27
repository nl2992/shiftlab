"""Deterministic minimax label allocations for stratified harm monitors."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np


def _vector(value: np.ndarray | float, *, name: str, size: int) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim == 0:
        array = np.full(size, float(array))
    if array.shape != (size,) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite scalar or matching one-dimensional vector")
    return array


def _inputs(
    w: np.ndarray,
    c: np.ndarray,
    budget: float,
    floors: np.ndarray | float,
    caps: np.ndarray | float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
    frequency = np.asarray(w, dtype=float)
    tariff = np.asarray(c, dtype=float)
    if (
        frequency.ndim != 1
        or not len(frequency)
        or tariff.shape != frequency.shape
        or not np.isfinite(frequency).all()
        or not np.isfinite(tariff).all()
        or np.any(frequency <= 0)
        or np.any(tariff <= 0)
        or float(frequency.sum()) > 1.0 + 1e-12
    ):
        raise ValueError("w and c must be matching finite positive vectors, with sum(w) <= 1")
    if not np.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be finite and positive")
    lower = _vector(floors, name="floors", size=len(frequency))
    upper = _vector(caps, name="caps", size=len(frequency))
    if np.any(lower < 0) or np.any(upper <= 0) or np.any(upper > 1):
        raise ValueError("floors must be nonnegative and caps must lie in (0, 1]")
    if np.any(lower > upper):
        raise ValueError("each floor must be no larger than its cap")
    budget_tolerance = 1e-12 * float(budget)
    return lower, upper, frequency * tariff, float(budget), budget_tolerance


def _minimax_bisection(
    *,
    required_q: Callable[[float], np.ndarray],
    minimum_time: float,
    floors: np.ndarray,
    caps: np.ndarray,
    weighted_cost: np.ndarray,
    budget: float,
    budget_tolerance: float,
) -> np.ndarray:
    floor_spend = float(np.dot(weighted_cost, floors))
    cap_spend = float(np.dot(weighted_cost, caps))
    if floor_spend > budget:
        raise ValueError("required floor allocation exceeds the label budget")
    if cap_spend <= budget:
        return caps.copy()
    if floor_spend == budget and np.any(floors == 0):
        raise ValueError("no finite minimax time is feasible at the floor-only budget")
    if floor_spend == budget:
        return floors.copy()

    def allocation(time: float) -> np.ndarray:
        return np.minimum(caps, np.maximum(floors, required_q(time)))

    def spend(time: float) -> float:
        return float(np.dot(weighted_cost, allocation(time)))

    low = float(minimum_time)
    minimum_allocation = allocation(low)
    if spend(low) <= budget:
        return minimum_allocation

    step = max(1.0, abs(low))
    high = low + step
    while spend(high) > budget:
        step *= 2
        high = low + step
        if not np.isfinite(high):
            raise ValueError("could not find a finite feasible minimax time")

    # Maintain an infeasible lower endpoint and a feasible upper endpoint.
    # A finite cap and midpoint guard prevent stalls when the budget is tiny
    # and the two floating-point endpoints become adjacent.
    for _ in range(256):
        middle = low + (high - low) / 2
        if middle <= low or middle >= high:
            break
        if spend(middle) <= budget:
            high = middle
        else:
            low = middle
        scale = max(1.0, abs(low), abs(high))
        if high - low <= 8 * np.finfo(float).eps * scale:
            break
    result = allocation(high)
    if float(np.dot(weighted_cost, result)) > budget + budget_tolerance:
        raise RuntimeError("allocation bisection exceeded the budget tolerance")
    return result


def minimax_support_allocation(
    C: np.ndarray,
    w: np.ndarray,
    c: np.ndarray,
    budget: float,
    power: int = 1,
    floors: np.ndarray | float = 0.0,
    caps: np.ndarray | float = 1.0,
) -> tuple[np.ndarray, float]:
    """Minimize ``max_k C_k / (w_k q_k**power)`` under a label-dollar budget.

    The constraints are ``sum_k w_k c_k q_k <= budget`` and elementwise
    ``floors <= q <= caps``. Stratum frequencies need only sum to at most one;
    omitted mass can represent a known agreement stratum. ``power=1`` models
    cap-dominated time, and ``power=2`` models a range-limited approximation.

    Returns the feasible propensity vector and its modeled maximum stratum time.
    This is a deterministic allocation solver; it does not select strata, K,
    constants, seeds, or empirical thresholds.
    """
    coefficients = np.asarray(C, dtype=float)
    frequency = np.asarray(w, dtype=float)
    tariff = np.asarray(c, dtype=float)
    if (
        coefficients.ndim != 1
        or not len(coefficients)
        or not np.isfinite(coefficients).all()
        or np.any(coefficients <= 0)
    ):
        raise ValueError("C must be a nonempty finite positive vector")
    if frequency.shape != coefficients.shape or tariff.shape != coefficients.shape:
        raise ValueError("C, w, and c must have matching one-dimensional shapes")
    if isinstance(power, bool) or not isinstance(power, int) or power not in (1, 2):
        raise ValueError("power must be 1 or 2")
    lower, upper, weighted_cost, budget_value, tolerance = _inputs(
        frequency, tariff, budget, floors, caps
    )
    minimum_time = float(np.max(coefficients / (frequency * upper**power)))
    propensities = _minimax_bisection(
        required_q=lambda time: (coefficients / (frequency * time)) ** (1.0 / power),
        minimum_time=minimum_time,
        floors=lower,
        caps=upper,
        weighted_cost=weighted_cost,
        budget=budget_value,
        budget_tolerance=tolerance,
    )
    if np.any(propensities <= 0):
        raise ValueError("no finite minimax time is feasible with the supplied budget")
    modeled_time = float(np.max(coefficients / (frequency * propensities**power)))
    return propensities, modeled_time


def minimax_uncapped_allocation(
    u: np.ndarray,
    v: np.ndarray,
    w: np.ndarray,
    c: np.ndarray,
    budget: float,
    floors: np.ndarray | float = 0.0,
    caps: np.ndarray | float = 1.0,
) -> tuple[np.ndarray, float]:
    """Minimize ``max_k (u_k + v_k / q_k)`` under a label-dollar budget.

    ``u`` may contain negative entries; ``v``, ``w``, and ``c`` must be finite
    and strictly positive. The same floor/cap and budget constraints as
    :func:`minimax_support_allocation` apply. The monotone requirement at a
    proposed maximum time is ``q_k(T) = v_k / (T - u_k)``. Returns the feasible
    propensity vector and its modeled maximum stratum time.
    """
    offset = np.asarray(u, dtype=float)
    inverse_query = np.asarray(v, dtype=float)
    frequency = np.asarray(w, dtype=float)
    tariff = np.asarray(c, dtype=float)
    if (
        offset.ndim != 1
        or not len(offset)
        or not np.isfinite(offset).all()
        or inverse_query.shape != offset.shape
        or not np.isfinite(inverse_query).all()
        or np.any(inverse_query <= 0)
        or frequency.shape != offset.shape
        or tariff.shape != offset.shape
    ):
        raise ValueError("u, v, w, and c must be matching finite vectors with v > 0")
    lower, upper, weighted_cost, budget_value, tolerance = _inputs(
        frequency, tariff, budget, floors, caps
    )
    minimum_time = float(np.max(offset + inverse_query / upper))
    propensities = _minimax_bisection(
        required_q=lambda time: inverse_query / (time - offset),
        minimum_time=minimum_time,
        floors=lower,
        caps=upper,
        weighted_cost=weighted_cost,
        budget=budget_value,
        budget_tolerance=tolerance,
    )
    if np.any(propensities <= 0):
        raise ValueError("no finite minimax time is feasible with the supplied budget")
    modeled_time = float(np.max(offset + inverse_query / propensities))
    return propensities, modeled_time
