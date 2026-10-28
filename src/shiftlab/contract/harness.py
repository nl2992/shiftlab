"""Evaluator-side harness that drives a contract ``Monitor`` over one stream.

Not available to external adapters. The harness owns the query coin, the label price, the reserve
and the paired costs. Oracle quantities are never passed to the monitor.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np

from .interface import Feedback, Monitor, PublicEvent, TaskSpec

# Same numerical slack as ``replay_gated``'s reserve test.
_RESERVE_SLACK = 1e-12


@dataclass
class HarnessResult:
    """Per-event records for the processed prefix of one stream.

    ``queried`` is True for any event (agreement or disagreement) whose label was bought.
    ``refused`` marks events whose coin said query but whose price exceeded the remaining
    reserve. ``spend`` is the price charged at each event (zero when nothing was bought).
    """

    log_e: np.ndarray
    propensities: np.ndarray
    queried: np.ndarray
    refused: np.ndarray
    spend: np.ndarray
    total_spend: float
    budget: float
    first_alarm: int | None
    processed: int
    stopped_early: bool


def run_monitor(
    monitor: Monitor,
    spec: TaskSpec,
    events: Sequence[PublicEvent],
    paired_costs: np.ndarray,
    uniforms: np.ndarray,
    prices: np.ndarray,
    *,
    stop_when_reserve_below_max_price: bool = True,
) -> HarnessResult:
    """Run ``monitor`` through the P4 harness obligations on one stream.

    ``events`` supplies ``x`` and the two actions. The harness assigns ``t``, ``disagreement``,
    ``price`` (from ``prices``) and ``remaining_budget``, overwriting any values supplied.
    ``paired_costs`` is read only for queried disagreements.

    Per event: build the public event, call ``propensity`` (validated in ``[0, 1]``) before
    using the harness coin ``uniforms[t]``, query iff ``coin < q`` (on any event), charge the
    price (a query that would overdraw the reserve is refused and recorded, and counts as
    unqueried), pass ``Feedback`` only after the coin for a bought label, then record
    ``log_e_value``. There is no free feedback: a queried agreement is charged like any other
    query and delivers ``Feedback(paired_cost=0.0)`` (its cost is not read from ``paired_costs``);
    an unqueried event delivers ``None``. A monitor that exploits ``event.disagreement`` can
    return ``q = 0`` on agreements and avoid paying for them.

    With ``stop_when_reserve_below_max_price`` (default), the stream stops before an event when the
    remaining reserve is below the largest possible price, matching ``replay_gated``'s predictable
    reserve stop ``budget - spent < 2.5``. The alarm is the first event with
    ``log_e >= log(1/alpha)``; the run continues past it so the full path is recorded.
    """
    costs = np.asarray(paired_costs, dtype=float)
    coins = np.asarray(uniforms, dtype=float)
    price_array = np.asarray(prices, dtype=float)
    n = len(events)
    if n > spec.horizon:
        raise ValueError("more events than the task horizon")
    if any(a.shape != (n,) for a in (costs, coins, price_array)):
        raise ValueError("paired_costs, uniforms and prices must match the events")
    low, high = spec.price_range
    if not np.isfinite(price_array).all() or np.any((price_array < low) | (price_array > high)):
        raise ValueError("prices must lie in the task price range")
    if not np.isfinite(coins).all() or np.any((coins < 0) | (coins >= 1)):
        raise ValueError("query uniforms must lie in [0,1)")
    threshold = -np.log(spec.alpha)

    monitor.reset(spec)
    budget = float(spec.label_budget)
    spent = 0.0
    log_e, props, queried, refused, spend = [], [], [], [], []
    first_alarm: int | None = None
    stopped_early = False
    for i, source in enumerate(events):
        remaining = budget - spent
        if stop_when_reserve_below_max_price and remaining + _RESERVE_SLACK < high:
            stopped_early = True
            break
        disagreement = source.deployed_action != source.reference_action
        event = replace(
            source,
            t=i,
            disagreement=bool(disagreement),
            price=float(price_array[i]),
            remaining_budget=float(remaining),
        )
        q = float(monitor.propensity(event))
        if not np.isfinite(q) or not 0.0 <= q <= 1.0:
            raise ValueError(f"propensity {q!r} at event {i} is outside [0, 1]")
        wants = bool(coins[i] < q)
        refuse = bool(wants and event.price > remaining + _RESERVE_SLACK)
        bought = wants and not refuse
        feedback: Feedback | None = None
        charge = 0.0
        if bought:
            cost = float(costs[i]) if disagreement else 0.0
            if not np.isfinite(cost) or abs(cost) > spec.cost_bound:
                raise ValueError("observed paired cost must lie in [-C, C]")
            feedback = Feedback(t=i, paired_cost=cost, propensity=q)
            charge = event.price
        monitor.observe(event, feedback)
        spent += charge
        value = float(monitor.log_e_value)
        log_e.append(value)
        props.append(q)
        queried.append(bought)
        refused.append(refuse)
        spend.append(charge)
        if first_alarm is None and value >= threshold:
            first_alarm = i
    return HarnessResult(
        log_e=np.asarray(log_e),
        propensities=np.asarray(props),
        queried=np.asarray(queried, dtype=bool),
        refused=np.asarray(refused, dtype=bool),
        spend=np.asarray(spend),
        total_spend=spent,
        budget=budget,
        first_alarm=first_alarm,
        processed=len(log_e),
        stopped_early=stopped_early,
    )
