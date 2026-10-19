"""Controlled adaptation costs and restricted evaluator references, not a learned controller."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ComputeBudget:
    """Explicit resource units, separate from decision-loss units; rejected charges are atomic."""

    total: float
    spent: float = 0.0

    def __post_init__(self):
        if not np.isfinite([self.total, self.spent]).all() or not 0 <= self.spent <= self.total:
            raise ValueError("Require finite total >= spent >= 0")

    @property
    def remaining(self):
        return self.total - self.spent

    def charge(self, amount):
        if not np.isfinite(amount) or amount < 0:
            raise ValueError("Resource charge must be finite and nonnegative")
        if amount > self.remaining:
            return False
        self.spent += amount
        return True


def oblivious_change_times(n, review_period, first_change=0):
    """Worst-phase schedule fixed before data/actions: changes one step after reviews.

    Assumes a learner checks at multiples of review_period. This delays the next
    scheduled review by period-1 observations, not every possible detection policy.
    No learner observations or actions are inspected; this is an oblivious adversary.
    """
    if any(
        isinstance(v, bool) or not isinstance(v, (int, np.integer))
        for v in [n, review_period, first_change]
    ):
        raise ValueError("Schedule parameters must be integers")
    if n < 1 or review_period < 2 or not 0 <= first_change < n:
        raise ValueError("Require n > first_change >= 0 and review_period >= 2")
    changes = np.arange(1, n, review_period, dtype=int)
    return changes[changes >= first_change]


def intervention_reference(
    stale_expected_loss,
    updated_expected_loss,
    *,
    horizon=100,
    update_cost=0.0,
    resource_cost=1.0,
    remaining_budget=1.0,
    deployment_delay=0,
    transient_penalties=(),
):
    """Full-future, single-update-versus-hold reference at each independent start time.

    Inputs are evaluator-known expected losses of TWO FIXED candidate predictors at
    future times; updated_expected_loss is not a clairvoyant predictor that changes
    after each future regime. Scalar or per-start costs are supported. Deployment
    keeps the stale predictor for deployment_delay steps, then uses the fixed updated
    predictor. transient_penalties adds expected loss to its first deployed steps.

    Costs are in cumulative loss units; compute resource costs are distinct units.
    Each start is an independent counterfactual with the supplied remaining budget.
    There is no multistep optimal control, finite-sample fitting or selection of a
    learned policy. Future reference values must never be passed to the learner.
    """
    stale, updated = (
        np.asarray(stale_expected_loss, float),
        np.asarray(updated_expected_loss, float),
    )
    if stale.ndim != 1 or updated.shape != stale.shape or not len(stale):
        raise ValueError("Require equal nonempty loss vectors")
    if (
        not np.isfinite(stale).all()
        or not np.isfinite(updated).all()
        or min(stale.min(), updated.min()) < 0
    ):
        raise ValueError("Expected losses must be finite and nonnegative")
    if isinstance(horizon, bool) or not isinstance(horizon, (int, np.integer)) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    if (
        isinstance(deployment_delay, bool)
        or not isinstance(deployment_delay, (int, np.integer))
        or deployment_delay < 0
    ):
        raise ValueError("deployment_delay must be a nonnegative integer")
    n = len(stale)
    arrays = []
    for name, value in [
        ("update_cost", update_cost),
        ("resource_cost", resource_cost),
        ("remaining_budget", remaining_budget),
    ]:
        array = np.broadcast_to(np.asarray(value, float), (n,))
        if not np.isfinite(array).all() or (array < 0).any():
            raise ValueError(f"{name} must be finite and nonnegative")
        arrays.append(array)
    cost, resource, budget = arrays
    penalties = np.asarray(transient_penalties, float)
    if penalties.ndim != 1 or not np.isfinite(penalties).all() or (penalties < 0).any():
        raise ValueError("Transient penalties must be a finite nonnegative vector")
    start = np.arange(n)
    end = np.minimum(start + horizon, n)
    deployed = np.minimum(start + deployment_delay, end)
    stale_sum = np.r_[0.0, np.cumsum(stale)]
    updated_sum = np.r_[0.0, np.cumsum(updated)]
    penalty_sum = np.r_[0.0, np.cumsum(penalties)]
    hold = stale_sum[end] - stale_sum[start]
    update = (
        stale_sum[deployed]
        - stale_sum[start]
        + updated_sum[end]
        - updated_sum[deployed]
        + penalty_sum[np.minimum(end - deployed, len(penalties))]
        + cost
    )
    feasible = resource <= budget
    beneficial = feasible & (update < hold)
    result = pd.DataFrame(
        {
            "start": start,
            "end_exclusive": end,
            "deployment_start": deployed,
            "hold_expected_loss": hold,
            "update_expected_loss": update,
            "net_update_benefit": hold - update,
            "resource_cost": resource,
            "remaining_budget": budget,
            "update_feasible": feasible,
            "oracle_action": np.where(beneficial, "update", "hold"),
        }
    )
    result.attrs["observability"] = "evaluator only; knows future expected losses"
    result.attrs["scope"] = (
        "single update of a fixed candidate versus hold; independent start times"
    )
    result.attrs["utility_origin"] = "synthetically imposed cumulative loss and resource costs"
    return result
