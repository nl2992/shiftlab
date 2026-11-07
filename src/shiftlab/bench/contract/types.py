"""Public (policy-visible) types of the common operational contract.

Everything here may be shown to a policy. Evaluator-side objects live in ``streams.py``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field

import numpy as np

# Action vocabulary. ``continue`` is the explicit no-op and is never charged.
ACTION_KINDS = ("query", "continue", "switch", "retrain", "alert", "rollback", "abstain", "route")
# route (canary traffic split) changes who serves, not the model in force; it is free (loss is
# charged per routed model) and therefore absent from COMPONENT.
FREE_KINDS = ("route",)
# Model ids: 0 incumbent (initially deployed), 1 candidate, 2 retrained model (exists after retrain).
INCUMBENT, CANDIDATE, RETRAINED = 0, 1, 2
# cost component for each chargeable action kind -> J term / ledger key
COMPONENT = {
    "query": "c_q",
    "switch": "c_s",
    "retrain": "c_r",
    "rollback": "c_b",
    "alert": "c_a",
    "abstain": "c_h",
}
COUNT_KEY = {
    "query": "N_q",
    "switch": "N_s",
    "retrain": "N_r",
    "rollback": "N_b",
    "alert": "N_a",
    "abstain": "N_h",
}


class BudgetExceeded(RuntimeError):
    """A pathwise budget (labels, retrains, switches, rollbacks, pending cap) would be exceeded."""


class ActionNotAllowed(RuntimeError):
    """The policy used an action outside its declared vocabulary subset."""


@dataclass(frozen=True)
class Action:
    kind: str
    target: int | None = None  # switch/route: model id
    propensity: float | None = (
        None  # query: declared randomisation probability (verified vs state.u)
    )
    round: int | None = None  # query: round whose label is requested (None = current round)
    fraction: float | None = None  # route: declared probability that a round is served by target
    u_index: int = 0  # query: which shared uniform (state.u[u_index]) realises the propensity

    def __post_init__(self) -> None:
        if self.kind not in ACTION_KINDS:
            raise ValueError(f"unknown action kind {self.kind!r}")


@dataclass(frozen=True)
class CostVector:
    """J(pi) = sum l_t + c_q N_q + c_s N_s + c_r N_r + c_b N_b + c_a N_a + c_h N_h."""

    name: str
    c_q: float = 0.0
    c_s: float = 0.0
    c_r: float = 0.0
    c_b: float = 0.0
    c_a: float = 0.0
    c_h: float = 0.0

    def price(self, kind: str) -> float:
        return float(getattr(self, COMPONENT[kind]))


@dataclass(frozen=True)
class BudgetSpec:
    """Pathwise caps. ``None`` = uncapped. Counts are performed actions only."""

    label_cap: int
    pending_cap: int | None = None  # max simultaneously outstanding label requests
    retrain_cap: int | None = None
    switch_cap: int | None = None
    rollback_cap: int | None = None
    retrain_cooldown: int = 0  # rounds after a retrain START before another may start
    switch_cooldown: int = 0  # rounds after a performed switch/rollback before another


@dataclass(frozen=True)
class ClockSpec:
    """Explicit clocks (all in rounds).

    request    : round t at which a label for round t is requested (query action).
    observation: the outcome of round t is realised at t (instant); the *system* only learns it at
                 release = t + delay_t (stream-level, evaluator-side; may be informative/missing).
    deployment : switch/rollback requested at t takes effect at t + deploy_lag / rollback_lag.
    retraining : retrain started at t completes at t + retrain_duration and (deploy_on_complete)
                 deploys the retrained model with NO extra switch charge.
    """

    deploy_lag: int = 0
    rollback_lag: int = 0
    retrain_duration: int = 20
    deploy_on_complete: bool = True
    fallback_loss: float = 0.5  # per-round loss while abstaining (handoff)
    max_lookback: int = 0  # query(round=s) allowed for s in [t - max_lookback, t]
    w_train: int = 100  # training window (rounds) of a retrain, RAR W_train


@dataclass(frozen=True)
class EnvSpec:
    """Everything fixed before the run that a policy may be told."""

    T: int
    costs: CostVector
    budget: BudgetSpec
    clocks: ClockSpec = field(default_factory=ClockSpec)
    obs_mode: str = "shadow"  # 'shadow': losses of all existing models on a queried round;
    #                          'deployed': only the model in force when the label was requested
    delay_info: str = "hidden"  # 'hidden' | 'exact' (pending views expose release round)
    allowed_actions: tuple[str, ...] = ACTION_KINDS
    hurdle: float = 0.1  # public decision hurdle h (benefit per round needed to justify a switch)


@dataclass(frozen=True)
class ReleasedLabel:
    """A label as delivered to the policy (the only form in which label content is visible)."""

    label_id: int
    request_t: int
    release_t: int
    obs: tuple[tuple[int, float], ...]  # (model id, loss on that round)
    model_at_request: int  # model that SERVED the label's round (routing-aware)
    propensity: float | None = None
    label_round: int = 0  # round whose outcome this label reveals (<= request_t)

    def loss(self, model: int) -> float | None:
        for m, v in self.obs:
            if m == model:
                return v
        return None

    def gain(self, base: int = INCUMBENT, other: int = CANDIDATE) -> float | None:
        a, b = self.loss(base), self.loss(other)
        return None if a is None or b is None else a - b


class PendingView:
    """Outstanding label request. Content is a honeypot: reading it before release is a leak."""

    __slots__ = ("expected_release_t", "label_id", "request_t")

    def __init__(self, label_id: int, request_t: int, expected_release_t: int | None) -> None:
        object.__setattr__(self, "label_id", label_id)
        object.__setattr__(self, "request_t", request_t)
        object.__setattr__(self, "expected_release_t", expected_release_t)

    def __setattr__(self, k, v):  # immutable
        raise AttributeError("PendingView is immutable")

    @property
    def value(self):
        from .guards import LabelNotReleased, record_leak

        record_leak("PendingView.value")
        raise LabelNotReleased(
            f"label {self.label_id} (requested t={self.request_t}) read before release"
        )


@dataclass(frozen=True)
class BudgetView:
    label_used: int
    label_cap: int
    pending: int
    retrain_used: int
    switch_used: int
    rollback_used: int
    retrain_busy_until: int | None  # completion round of the running retrain, if any
    retrain_cooldown_left: int
    switch_cooldown_left: int

    @property
    def label_remaining(self) -> int:
        return self.label_cap - self.label_used


@dataclass(frozen=True)
class ObservableState:
    """S_t = (m_t, b_t, Q_t, H_t, monitor signal, available labels). Frozen, evaluator-free."""

    t: int
    T: int
    m: int  # model in force at the start of round t
    prev_m: int | None  # model retained for rollback
    retrained_ready: bool  # a retrained model exists (completed)
    b: BudgetView
    Q: tuple[PendingView, ...]
    H: tuple[ReleasedLabel, ...]  # released labels in delivery order (may be out of request order)
    x: float  # monitor signal observed at round t (unlabelled)
    x_hist: np.ndarray  # monitor signals for rounds 1..t-1 (read-only view)
    u: tuple[float, ...] = ()  # shared i.i.d. Uniform(0,1) draws for this round (N_U of them)
    served_hist: np.ndarray | None = None  # model that served rounds 1..t-1 (read-only)
    route: tuple[int, float] | None = None  # standing canary route (target, fraction)
    routed_labels: tuple[tuple[int, int], ...] = ()  # (served model, released-label count)

    @property
    def available_labels(self) -> int:
        return len(self.H)


def cost_vector_fingerprint(vectors: Mapping[str, Mapping[str, float]]) -> str:
    blob = json.dumps(vectors, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def cost_to_dict(c: CostVector) -> dict:
    d = asdict(c)
    d.pop("name")
    return d
