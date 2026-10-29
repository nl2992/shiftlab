"""Evaluator-side v2 harness: delayed, pending and missing feedback plus an optional switching layer.

``harness.py`` (v1) is untouched. With every release round equal to its own round and no missing
labels, ``run_monitor_v2`` reproduces ``run_monitor`` field for field (tested).

Accounting conventions (all evaluator-side):

* A bought query's price is charged and reserved at request time. ``remaining_budget`` is
  ``budget - spent`` with ``spent`` including pending queries, and a query that would overdraw is
  refused. Pending queries are never refunded: labels released after the last processed round (or
  never) stay charged and are reported in ``pending_at_end``.
* ``release_round[t]`` is the round at whose start the label of event ``t`` is delivered; the
  effective release is ``max(release_round[t], t)``. Equal to ``t`` means same-round delivery
  inside ``observe`` (v1 behaviour). Release rounds need not be monotone (out-of-order arrival).
  Deliveries in one round are ordered by event index.
* A bought disagreement whose label is not observed delivers ``MissingFeedback`` (charged, no
  ``Z``) at its release time. A bought agreement always delivers ``Feedback(paired_cost=0.0)``
  (contract rule: ``Z = 0`` on agreement) unless ``missing_on_agreement=True``.
* Net utility ``= -(sum_t deployed loss) - c * (bought queries) - k * (policy switches)``; higher
  is better, ``net_cost = -net_utility``. Losses are the task's own normalised losses
  (``l(0)`` incumbent, ``l(1)`` candidate); ``A_0 = 0`` so a switch at round 0 counts. Rounds whose
  deployed loss is unavailable (NaN: unusable decision or missing evaluator data) add nothing and
  are counted in ``n_loss_missing``. The sum covers the processed prefix only.
* Switching layer: the monitor is a ``Switcher`` if it has ``choose``; otherwise ``A_t = 0``.
  ``PublicEvent.deployed_action``/``reference_action`` stay the incumbent/candidate actions of the
  task stream, so ``Z = l(incumbent) - l(candidate)`` and positive ``Z`` favours the candidate.
* False switches: ``false_promotions`` is reported only when the evaluator supplies a round-level
  indicator ``null_round`` (True where the evaluator-side truth satisfies the no-benefit null
  ``E[Z_t | H_t] <= 0``); it is the set of 0 -> 1 switch rounds inside the null. The problem note
  defines only a global-null event (any 0 -> 1 switch under the global null); the round-level
  version is an extension. Without ``null_round`` (all real tasks) only raw switch times are
  reported and ``false_promotions`` is ``None``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace

import numpy as np

from .harness import _RESERVE_SLACK, RESERVE_STOP_DEFAULT, HarnessResult
from .interface import Feedback, PublicEvent, TaskSpec
from .interface_v2 import (
    Delivery,
    MissingFeedback,
    MonitorV2,
    PendingQuery,
    QueryOutcome,
    SwitchContext,
)


@dataclass
class HarnessResultV2(HarnessResult):
    """``HarnessResult`` plus delay, pending, missing and switching records."""

    actions: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    switch_times: tuple[int, ...] = ()
    false_promotions: tuple[int, ...] | None = None
    deliveries: tuple[tuple[int, int, str], ...] = ()  # (delivery round, event index, kind)
    n_feedback_delivered: int = 0
    n_missing_delivered: int = 0
    pending_at_end: int = 0
    pending_spend_at_end: float = 0.0
    max_pending: int = 0
    query_cost: float = 0.0
    switch_cost: float = 0.0
    n_queries: int = 0
    n_switches: int = 0
    n_loss_missing: int = 0
    deployed_loss_sum: float | None = None
    loss_sum_always_incumbent: float | None = None
    loss_sum_always_candidate: float | None = None
    net_utility: float | None = None

    @property
    def net_cost(self) -> float | None:
        return None if self.net_utility is None else -self.net_utility


def run_monitor_v2(
    monitor: MonitorV2,
    spec: TaskSpec,
    events: Sequence[PublicEvent],
    paired_costs: np.ndarray,
    uniforms: np.ndarray,
    prices: np.ndarray,
    release_round: np.ndarray,
    *,
    observed: np.ndarray | None = None,
    loss_incumbent: np.ndarray | None = None,
    loss_candidate: np.ndarray | None = None,
    query_cost: float = 0.0,
    switch_cost: float = 0.0,
    null_round: np.ndarray | None = None,
    missing_on_agreement: bool = False,
    stop_when_reserve_below_max_price: bool = RESERVE_STOP_DEFAULT,
) -> HarnessResultV2:
    """Drive a ``MonitorV2`` (or ``Switcher``) over one stream; see the module docstring."""
    costs = np.asarray(paired_costs, dtype=float)
    coins = np.asarray(uniforms, dtype=float)
    price_array = np.asarray(prices, dtype=float)
    release = np.asarray(release_round)
    n = len(events)
    if n > spec.horizon:
        raise ValueError("more events than the task horizon")
    if any(a.shape != (n,) for a in (costs, coins, price_array, release)):
        raise ValueError("paired_costs, uniforms, prices and release_round must match the events")
    if not np.issubdtype(release.dtype, np.integer):
        raise ValueError("release_round must be integer")
    obs_flags = np.ones(n, dtype=bool) if observed is None else np.asarray(observed, dtype=bool)
    if obs_flags.shape != (n,):
        raise ValueError("observed must match the events")
    if (loss_incumbent is None) != (loss_candidate is None):
        raise ValueError("pass both loss_incumbent and loss_candidate or neither")
    if query_cost < 0 or switch_cost < 0:
        raise ValueError("query_cost and switch_cost must be non-negative")
    low, high = spec.price_range
    if not np.isfinite(price_array).all() or np.any((price_array < low) | (price_array > high)):
        raise ValueError("prices must lie in the task price range")
    if not np.isfinite(coins).all() or np.any((coins < 0) | (coins >= 1)):
        raise ValueError("query uniforms must lie in [0,1)")
    threshold = -np.log(spec.alpha)
    chooser = getattr(monitor, "choose", None)

    monitor.reset(spec)
    budget = float(spec.label_budget)
    spent = 0.0
    scheduled: dict[int, list[Delivery]] = {}
    pending_price: dict[int, float] = {}  # bought, not yet delivered (includes never-released)
    log_e, props, queried, refused, spend, actions = [], [], [], [], [], []
    deliveries: list[tuple[int, int, str]] = []
    counts = {"feedback": 0, "missing": 0}
    max_pending = 0
    current = 0  # A_0 = 0
    switch_times: list[int] = []
    first_alarm: int | None = None
    stopped_early = False

    def record(round_: int, item: Delivery) -> None:
        kind = "missing" if isinstance(item, MissingFeedback) else "feedback"
        deliveries.append((round_, item.t, kind))
        counts[kind] += 1

    for i, source in enumerate(events):
        remaining = budget - spent
        if stop_when_reserve_below_max_price and remaining + _RESERVE_SLACK < high:
            stopped_early = True
            break
        released = sorted(scheduled.pop(i, []), key=lambda d: d.t)
        for item in released:
            pending_price.pop(item.t)
            record(i, item)
        monitor.receive(i, tuple(released))
        disagreement = source.deployed_action != source.reference_action
        event = replace(
            source,
            t=i,
            disagreement=bool(disagreement),
            price=float(price_array[i]),
            remaining_budget=float(remaining),
        )
        choice = 0
        if chooser is not None:
            context = SwitchContext(
                t=i,
                current_policy=current,
                n_switches=len(switch_times),
                remaining_budget=float(remaining),
                pending_queries=len(pending_price),
                pending_spend=float(sum(pending_price.values())),
                query_cost=float(query_cost),
                switch_cost=float(switch_cost),
            )
            choice = int(chooser(event, context))
            if choice not in (0, 1):
                raise ValueError(f"switcher chose policy {choice!r} at event {i}; expected 0 or 1")
        if choice != current:
            switch_times.append(i)
            current = choice
        q = float(monitor.propensity(event))
        if not np.isfinite(q) or not 0.0 <= q <= 1.0:
            raise ValueError(f"propensity {q!r} at event {i} is outside [0, 1]")
        wants = bool(coins[i] < q)
        refuse = bool(wants and event.price > remaining + _RESERVE_SLACK)
        bought = wants and not refuse
        outcome: QueryOutcome = None
        charge = 0.0
        if bought:
            charge = event.price
            payload: Delivery
            if disagreement and obs_flags[i]:
                cost = float(costs[i])
                if not np.isfinite(cost) or abs(cost) > spec.cost_bound:
                    raise ValueError("observed paired cost must lie in [-C, C]")
                payload = Feedback(t=i, paired_cost=cost, propensity=q)
            elif disagreement or (missing_on_agreement and not obs_flags[i]):
                payload = MissingFeedback(t=i, propensity=q)
            else:
                payload = Feedback(t=i, paired_cost=0.0, propensity=q)
            due = max(int(release[i]), i)
            if due == i:
                outcome = payload
                record(i, payload)
            else:
                outcome = PendingQuery(t=i, propensity=q)
                scheduled.setdefault(due, []).append(payload)
                pending_price[i] = charge
        spent += charge  # charged (reserved) at request time, including pending queries
        max_pending = max(max_pending, len(pending_price))
        monitor.observe(event, outcome)
        value = float(monitor.log_e_value)
        if not np.isfinite(value):
            raise ValueError(f"log_e_value {value!r} at event {i} is not finite")
        log_e.append(value)
        props.append(q)
        queried.append(bought)
        refused.append(refuse)
        spend.append(charge)
        actions.append(current)
        if first_alarm is None and value >= threshold:
            first_alarm = i

    processed = len(log_e)
    queried_arr = np.asarray(queried, dtype=bool)
    action_arr = np.asarray(actions, dtype=np.int64)
    n_queries = int(queried_arr.sum())
    prev = np.concatenate([[0], action_arr[:-1]]).astype(np.int64) if processed else action_arr
    promotions = np.flatnonzero((prev == 0) & (action_arr == 1))
    false_promotions: tuple[int, ...] | None = None
    if null_round is not None:
        null_arr = np.asarray(null_round, dtype=bool)
        if null_arr.shape != (n,):
            raise ValueError("null_round must match the events")
        false_promotions = tuple(int(t) for t in promotions if null_arr[t])
    n_loss_missing = 0
    deployed = always_inc = always_cand = net = None
    if loss_incumbent is not None and loss_candidate is not None:
        full0 = np.asarray(loss_incumbent, dtype=float)
        full1 = np.asarray(loss_candidate, dtype=float)
        if full0.shape != (n,) or full1.shape != (n,):
            raise ValueError("loss arrays must match the events")
        l0, l1 = full0[:processed], full1[:processed]
        chosen = np.where(action_arr == 0, l0, l1)
        valid = np.isfinite(chosen)
        n_loss_missing = int((~valid).sum())
        deployed = float(chosen[valid].sum())
        both = np.isfinite(l0) & np.isfinite(l1)
        always_inc = float(l0[both].sum())
        always_cand = float(l1[both].sum())
        net = -deployed - query_cost * n_queries - switch_cost * len(switch_times)
    return HarnessResultV2(
        log_e=np.asarray(log_e),
        propensities=np.asarray(props),
        queried=queried_arr,
        refused=np.asarray(refused, dtype=bool),
        spend=np.asarray(spend),
        total_spend=spent,
        budget=budget,
        first_alarm=first_alarm,
        processed=processed,
        stopped_early=stopped_early,
        reserve_stop_rule=stop_when_reserve_below_max_price,
        actions=action_arr,
        switch_times=tuple(switch_times),
        false_promotions=false_promotions,
        deliveries=tuple(deliveries),
        n_feedback_delivered=counts["feedback"],
        n_missing_delivered=counts["missing"],
        pending_at_end=len(pending_price),
        pending_spend_at_end=float(sum(pending_price.values())),
        max_pending=max_pending,
        query_cost=float(query_cost),
        switch_cost=float(switch_cost),
        n_queries=n_queries,
        n_switches=len(switch_times),
        n_loss_missing=n_loss_missing,
        deployed_loss_sum=deployed,
        loss_sum_always_incumbent=always_inc,
        loss_sum_always_candidate=always_cand,
        net_utility=net,
    )
