"""Public interface for sequential harm monitors (P4 section 1).

This module imports only the standard library and numpy. An external adapter needs nothing else
from the repository. Oracle quantities (expected costs, onset times, scenario labels) never cross
this interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class TaskSpec:
    """Task constants fixed before the stream starts; they carry no outcome information.

    Attributes:
        cost_bound: ``C`` with ``|Z_t| <= C`` for every paired cost (5.0 on the synthetic suite).
        epsilon: charter margin; the eventwise null is ``E[Z_t - epsilon | F_{t-1}] <= 0``.
        alpha: false-alarm level. The harness declares an alarm at ``log_e >= log(1/alpha)``.
        horizon: maximum number of events after monitor start.
        label_budget: total label reserve, in label-price units.
        price_range: ``(low, high)`` bounds on the per-event label price.
    """

    cost_bound: float
    epsilon: float
    alpha: float
    horizon: int
    label_budget: float
    price_range: tuple[float, float]


@dataclass(frozen=True)
class PublicEvent:
    """What a deployed monitor may see before the label decision at event ``t``.

    Attributes:
        t: event index after monitor start (0-based, assigned by the harness).
        x: covariate vector for this event.
        deployed_action: action of the deployed policy.
        reference_action: action of the frozen reference policy.
        disagreement: ``deployed_action != reference_action``. On agreements the paired cost is
            exactly zero, but a query on an agreement is still charged at ``price``; a monitor
            may use this flag to return propensity 0 there.
        price: label price for this event, inside ``TaskSpec.price_range``.
        remaining_budget: reserve left before this event's decision, in price units.
    """

    t: int
    x: np.ndarray
    deployed_action: int
    reference_action: int
    disagreement: bool
    price: float
    remaining_budget: float


@dataclass(frozen=True)
class Feedback:
    """Feedback delivered after the query decision.

    Attributes:
        t: event index this feedback belongs to.
        paired_cost: ``Z_t = c(deployed) - c(reference)`` with the common-label contract.
        propensity: the query probability ``q`` the harness actually used (the value returned by
            ``Monitor.propensity`` for this event), for Horvitz-Thompson weighting.
    """

    t: int
    paired_cost: float
    propensity: float


class Monitor(Protocol):
    """Sequential monitor protocol. Harness obligations are in the P4 protocol and README.

    Per event the harness calls ``propensity(event)`` first (the value must lie in ``[0, 1]``),
    then draws its own query coin (``coin < q`` queries, on any event), then calls ``observe``.
    ``Feedback`` is passed only for queried events (after the coin and a successful reserve
    charge); a queried agreement delivers ``paired_cost=0.0``. For an unqueried or refused
    event, ``feedback`` is ``None``. There is no free feedback. ``log_e_value`` is read after
    every ``observe``.
    """

    def reset(self, spec: TaskSpec) -> None: ...

    def propensity(self, event: PublicEvent) -> float: ...

    def observe(self, event: PublicEvent, feedback: Feedback | None) -> None: ...

    @property
    def log_e_value(self) -> float: ...
