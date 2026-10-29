"""Optimize onset-mixture weights for the finite-horizon safe-switching bound."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class MixtureResult:
    regret_horizon: float
    weights: tuple[float, ...]
    cell_bounds: tuple[float, ...]
    uniform_bound: float
    infinite_prior_bound: float


def _log_growth(epsilon: float) -> tuple[float, float]:
    if not 0 < epsilon < 0.5:
        raise ValueError("epsilon must lie in (0, 0.5)")
    kappa = (0.5 + epsilon) * math.log1p(2 * epsilon) + (0.5 - epsilon) * math.log1p(-2 * epsilon)
    return kappa, math.log1p(2 * epsilon)


def optimize_weights(
    *,
    horizon: int,
    budget: int,
    epsilon: float,
    alpha: float,
    delay: int,
    inactive_mass: float = 1e-12,
) -> MixtureResult:
    """Minimize the worst-cell regret bound over start-mixture weights.

    ``inactive_mass`` is reserved across cells whose trivial remaining-horizon bound
    already meets the optimum. It keeps every start weight positive without materially
    changing the optimum. Set it to zero to omit those start components entirely.
    """
    if not (1 <= budget <= horizon):
        raise ValueError("budget must satisfy 1 <= budget <= horizon")
    if not (0 < alpha < 1):
        raise ValueError("alpha must lie in (0, 1)")
    if delay < 1:
        raise ValueError("delay must be at least one")
    if not (0 <= inactive_mass < 1):
        raise ValueError("inactive_mass must lie in [0, 1)")

    query_times = tuple(math.ceil(j * horizon / budget) for j in range(1, budget + 1))
    max_gap = math.ceil(horizon / budget)
    previous_times = (0, *query_times[:-1])
    remaining = tuple(horizon - t for t in previous_times)
    kappa, overshoot = _log_growth(epsilon)

    def active_and_min_weight(regret_horizon: float) -> tuple[list[int], float]:
        active = [j for j, h in enumerate(remaining) if h > regret_horizon]
        log_weight = overshoot - kappa * (regret_horizon - delay + 1) / max_gap
        min_weight = math.exp(log_weight) / alpha
        return active, min_weight

    low, high = 0.0, float(max(remaining))
    for _ in range(100):
        mid = (low + high) / 2
        active, min_weight = active_and_min_weight(mid)
        if len(active) * min_weight <= 1 - inactive_mass:
            high = mid
        else:
            low = mid
    optimum = high
    active, min_weight = active_and_min_weight(optimum)
    inactive = [j for j in range(budget) if j not in active]

    if not active:
        weights = [1 / budget] * budget
    else:
        weights = [0.0] * budget
        for j in active:
            weights[j] = min_weight
        if inactive:
            for j in inactive:
                weights[j] = inactive_mass / len(inactive)
        weights[active[0]] += 1 - sum(weights)

    def cell_bound(j: int, weight: float) -> float:
        if weight <= 0:
            return float(remaining[j])
        test_delay = delay - 1 + max_gap * (math.log(1 / (alpha * weight)) + overshoot) / kappa
        return min(float(remaining[j]), test_delay)

    cell_bounds = tuple(cell_bound(j, w) for j, w in enumerate(weights))
    uniform_bounds = tuple(cell_bound(j, 1 / budget) for j in range(budget))
    old_bounds = tuple(
        min(
            float(remaining[j]),
            delay - 1 + max_gap * (math.log((j + 1) * (j + 2) / alpha) + overshoot) / kappa,
        )
        for j in range(budget)
    )
    return MixtureResult(
        regret_horizon=optimum,
        weights=tuple(weights),
        cell_bounds=cell_bounds,
        uniform_bound=max(uniform_bounds),
        infinite_prior_bound=max(old_bounds),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--horizon", type=int, default=120)
    parser.add_argument("--budget", type=int, default=20)
    parser.add_argument("--epsilon", type=float, default=0.49)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--delay", type=int, default=1)
    args = parser.parse_args()
    result = optimize_weights(
        horizon=args.horizon,
        budget=args.budget,
        epsilon=args.epsilon,
        alpha=args.alpha,
        delay=args.delay,
    )
    print(f"optimized worst-onset regret horizon: {result.regret_horizon:.6f}")
    print(f"uniform-weight bound: {result.uniform_bound:.6f}")
    print(f"infinite-prior bound: {result.infinite_prior_bound:.6f}")
    print("weights:", ", ".join(f"{w:.8g}" for w in result.weights))
    print("cell bounds:", ", ".join(f"{x:.6f}" for x in result.cell_bounds))


if __name__ == "__main__":
    main()
