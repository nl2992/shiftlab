"""Exhaustively check the UPF paper's retraining-count bound on a minimal case.

The audit uses the finite-horizon objective and assumptions stated in Regol et
al. (ICML 2025), Proposition 3.1. It is a counterexample checker, not an UPF
implementation or a reproduction of the paper's experiments.
"""

from __future__ import annotations

import itertools
import json
import math
from typing import Any


def optimal_schedule(performance: list[list[float]], retrain_cost: float) -> dict[str, Any]:
    """Enumerate all retraining schedules for a bounded triangular PE matrix.

    ``performance[i][t - 1]`` is the loss of the model trained at index ``i``
    evaluated at test timestep ``t``. Rows have ``T + 1`` entries and columns
    have ``T`` entries; only ``i <= t`` is used. The initial model is index 0.
    """
    horizon = len(performance[0]) if performance else 0
    if horizon < 1 or len(performance) != horizon + 1:
        raise ValueError("performance must have shape (T + 1, T) for T >= 1")
    if not math.isfinite(retrain_cost) or retrain_cost < 0:
        raise ValueError("retrain_cost must be finite and nonnegative")
    for test_time in range(1, horizon + 1):
        for model_index in range(test_time + 1):
            value = performance[model_index][test_time - 1]
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("all used performance losses must lie in [0, 1]")

    best: tuple[float, int, tuple[bool, ...]] | None = None
    for schedule in itertools.product((False, True), repeat=horizon):
        model_index = 0
        total = 0.0
        count = 0
        for test_time, retrain in enumerate(schedule, start=1):
            if retrain:
                model_index = test_time
                count += 1
                total += retrain_cost
            total += performance[model_index][test_time - 1]
        candidate = (total, count, schedule)
        if best is None or candidate < best:
            best = candidate
    assert best is not None

    adjacent_model_bound = max(
        abs(performance[model_index][test_time - 1] - performance[model_index + 1][test_time - 1])
        for test_time in range(1, horizon + 1)
        for model_index in range(test_time)
    )
    claimed_upper_bound = (
        float("inf")
        if adjacent_model_bound == 0 and retrain_cost > 0
        else horizon - math.sqrt(retrain_cost / adjacent_model_bound)
        if adjacent_model_bound > 0
        else float(horizon)
    )
    return {
        "horizon": horizon,
        "retrain_cost_alpha": retrain_cost,
        "performance_matrix": performance,
        "adjacent_model_difference_bound_L": adjacent_model_bound,
        "optimal_cost": best[0],
        "optimal_retrains": best[1],
        "optimal_schedule": list(best[2]),
        "proposition_3_1_claimed_upper_bound": claimed_upper_bound,
        "violates_claimed_bound": best[1] > claimed_upper_bound,
    }


def main() -> None:
    # One-step case: keeping incurs loss 1; retraining incurs alpha=0.25 and
    # zero loss. L=1 satisfies the paper's adjacent-model Lipschitz condition.
    result = optimal_schedule([[1.0], [0.0]], retrain_cost=0.25)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
