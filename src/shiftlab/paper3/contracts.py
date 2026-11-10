"""Paper 3 event-clock contract types (docs: 2026_programme/02_SCIENTIFIC_CONTRACT.md).

Clock for round t = 1..T, in this order:
  1. every label with ``available_time <= t`` is released (never earlier);
  2. the policy sees ``PolicyView`` (released labels, event features, own budget state);
  3. it picks ``Paper3Decision`` (action, query, compute, retrain);
  4. the loss ell_t(action) is incurred; a query is paid and reserved at request time and its
     (paired) label is released at the start of round ``t + d_t`` with integer ``d_t >= 1``.
``a_0 = 0``. Nothing evaluator-side (potential outcomes, regimes, change points) is in a view.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Costs:
    c_q: float = 0.05  # per label, booked at request time
    k: float = 3.0  # per change of deployed action (a_0 = 0)
    c_compute: float = 0.0  # per unit of optional compute u_t
    c_retrain: float = 0.0  # per retrain event (cost accounting only in the core simulator)

    def __post_init__(self):
        if min(self.c_q, self.k, self.c_compute, self.c_retrain) < 0:
            raise ValueError("costs must be nonnegative")


@dataclass(frozen=True)
class ProblemSpec:
    """Public problem declaration handed to a policy at reset (no evaluator truth)."""

    T: int
    B: int
    costs: Costs
    compute_budget: int | None = None
    delay_known: int | None = None  # a constant delay if the contract declares one, else None
    delay_kind: str = "fixed"  # "fixed" | "random" | "informative" (declared, not the realisation)


@dataclass(frozen=True)
class ReleasedLabel:
    """A queried common outcome: both losses identified; visible from ``t_release`` on."""

    t_request: int
    t_release: int
    ell0: float
    ell1: float

    @property
    def z(self) -> float:
        return self.ell0 - self.ell1  # > 0 favours the challenger (action 1)


@dataclass(frozen=True)
class Paper3Event:
    t: int
    disagree: bool  # prediction-only disagreement flag, available before the label
    x: tuple[float, ...] = ()


@dataclass(frozen=True)
class Paper3Decision:
    action: int
    query: int = 0
    compute: int = 0
    retrain: int = 0


@dataclass(frozen=True)
class PolicyView:
    t: int
    event: Paper3Event
    released: tuple[ReleasedLabel, ...]  # exactly the labels released at the start of t
    prev_action: int
    labels_remaining: int  # B - requests so far (pending labels are already reserved)
    labels_pending: int
    compute_remaining: int | None


class PolicyAdapter(ABC):
    """Every policy (baseline or new) implements reset/act and nothing else."""

    name: str = "policy"

    @abstractmethod
    def reset(self, spec: ProblemSpec, rng: np.random.Generator) -> None: ...

    @abstractmethod
    def act(self, view: PolicyView) -> Paper3Decision: ...


@dataclass
class RunRecord:
    """Executed trajectory plus ledger totals; consumed by the evaluator only."""

    a: np.ndarray
    q: np.ndarray
    u: np.ndarray
    retrain: np.ndarray
    release_t: np.ndarray  # release time of the label requested at t (0 if no query / never)
    ledger: dict = field(default_factory=dict)

    @property
    def J(self) -> float:
        return float(self.ledger["J"])
