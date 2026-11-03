"""Common streaming-deployment simulator for the SOTA comparison.

The simulator owns the hidden labels. A policy sees a label only after it has requested it and
the declared delay has elapsed. The evaluator may read hidden labels to score predictions; the
policy may not, and the only channel from labels to a policy is ``observe``.

Design points that the comparison depends on:

* **Frozen propensities.** The query probability and any betting parameter are recorded at
  *issue* time and travel with the request. Nothing is recomputed at release. ``ReleasedFeedback``
  carries the issue-time values so a policy cannot accidentally use a later estimate.
* **Hard budget.** ``remaining_budget`` is enforced by the simulator, not by the policy. A policy
  that asks when the budget is exhausted simply does not get the label, and the attempt is
  recorded. Several published methods do not enforce a cap at all; forcing one on them is an
  adapter decision and is recorded per policy rather than hidden.
* **One documented event order** for every method, supplied by the caller.
* **Determinism.** Each policy is driven by its own ``numpy`` Generator seeded from
  ``(seed_base, episode, policy_name)``, so policies do not consume one another's randomness and a
  run is reproducible from its seed alone.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np

# Columns of the per-event record, in order.
EVENT_FIELDS = (
    "event_id",
    "deployed_model",
    "requested",
    "query_probability",
    "request_time",
    "release_time",
    "budget_remaining",
    "prediction_loss",
    "query_cost",
    "switch_cost",
    "decision_state",
)


@dataclass(frozen=True)
class Event:
    """What a policy may see before it acts. Never carries the label."""

    event_id: int
    t: int
    horizon: int
    model_predictions: np.ndarray  # (n_models,) predicted labels
    context: Any = None  # features, or None where a policy is context-free


@dataclass(frozen=True)
class QueryRequest:
    """A policy's acquisition decision. ``probability`` is frozen here and never recomputed."""

    requested: bool
    probability: float = 0.0
    extra: dict = field(default_factory=dict)  # e.g. a frozen betting fraction


@dataclass(frozen=True)
class ReleasedFeedback:
    """A label coming back, with the issue-time values that accompanied its request."""

    event_id: int
    t_requested: int
    t_released: int
    label: int
    model_losses: np.ndarray  # (n_models,) 0/1 loss of every frozen model on this event
    query_probability: float  # the issue-time propensity, not a recomputed one
    extra: dict = field(default_factory=dict)


class Policy(Protocol):
    """The interface every competitor and every one of our policies implements."""

    name: str

    def predict(self, event: Event) -> int:
        """Return the index of the model to deploy for this event."""

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        """Decide whether to buy this event's label. Called after ``predict``."""

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        """Receive labels whose delay has now elapsed. May be empty."""

    def state_dict(self) -> dict:
        """Serialisable state sufficient for deterministic restoration."""

    def load_state_dict(self, state: dict) -> None:
        """Restore from ``state_dict``."""


def policy_rng(seed_base: int, episode: int, policy_name: str) -> np.random.Generator:
    """A generator private to one (episode, policy), so policies cannot perturb each other."""
    h = hashlib.sha256(policy_name.encode()).digest()[:8]
    return np.random.default_rng(
        np.random.SeedSequence([seed_base, episode, int.from_bytes(h, "big") % (2**31)])
    )


@dataclass
class EpisodeResult:
    policy: str
    net_cost: float
    prediction_loss: float
    requested_labels: int
    deployment_switches: int
    records: list[dict]
    refused_requests: int  # asked with no budget left; evidence of a cap being binding

    def as_summary(self) -> dict:
        return {
            "policy": self.policy,
            "net_cost": self.net_cost,
            "prediction_loss": self.prediction_loss,
            "requested_labels": self.requested_labels,
            "deployment_switches": self.deployment_switches,
            "refused_requests": self.refused_requests,
        }


def run_episode(
    policy: Policy,
    *,
    model_predictions: np.ndarray,  # (T, n_models) predicted labels
    labels: np.ndarray,  # (T,) hidden ground truth, evaluator-only
    contexts: Any = None,  # (T, d) or None
    delay: int,
    budget: int,
    label_price: float,
    switch_cost: float,
    initial_model: int = 0,
    trace: bool = True,
) -> EpisodeResult:
    """Run one policy over one episode. Returns its net cost and per-event records.

    ``labels`` is read only to score predictions and to construct released feedback. It is never
    passed to the policy except through ``observe`` for events the policy paid for.
    """
    horizon = int(model_predictions.shape[0])
    n_models = int(model_predictions.shape[1])
    if labels.shape[0] != horizon:
        raise ValueError("labels and model_predictions disagree on horizon")

    deployed = int(initial_model)
    remaining = int(budget)
    n_requested = 0
    n_switches = 0
    n_refused = 0
    total_loss = 0.0
    records: list[dict] = []
    pending: dict[int, list[ReleasedFeedback]] = {}

    for t in range(horizon):
        event = Event(
            event_id=t,
            t=t,
            horizon=horizon,
            model_predictions=model_predictions[t],
            context=None if contexts is None else contexts[t],
        )

        # ---- release first: labels earned earlier become usable now, before this event's act
        due = pending.pop(t, [])
        if due:
            policy.observe(due)

        # ---- deploy
        prev = deployed
        deployed = int(policy.predict(event))
        if not 0 <= deployed < n_models:
            raise ValueError(f"{policy.name} deployed invalid model index {deployed}")
        switched = int(deployed != prev)
        n_switches += switched
        loss = float(model_predictions[t, deployed] != labels[t])
        total_loss += loss

        # ---- acquire
        req = policy.request_labels(event, remaining)
        granted = bool(req.requested) and remaining > 0
        if req.requested and remaining <= 0:
            n_refused += 1
        release_time = None
        if granted:
            remaining -= 1
            n_requested += 1
            release_time = t + delay
            if release_time < horizon:
                pending.setdefault(release_time, []).append(
                    ReleasedFeedback(
                        event_id=t,
                        t_requested=t,
                        t_released=release_time,
                        label=int(labels[t]),
                        model_losses=(model_predictions[t] != labels[t]).astype(np.int8),
                        query_probability=float(req.probability),  # frozen at issue
                        extra=dict(req.extra),
                    )
                )

        if trace:
            records.append(
                {
                    "event_id": t,
                    "deployed_model": deployed,
                    "requested": int(granted),
                    "query_probability": float(req.probability) if req.requested else 0.0,
                    "request_time": t if granted else None,
                    "release_time": release_time if granted else None,
                    "budget_remaining": remaining,
                    "prediction_loss": loss,
                    "query_cost": label_price if granted else 0.0,
                    "switch_cost": switch_cost * switched,
                    "decision_state": getattr(policy, "decision_state", lambda: "")(),
                }
            )

    net = total_loss + label_price * n_requested + switch_cost * n_switches
    return EpisodeResult(
        policy=policy.name,
        net_cost=float(net),
        prediction_loss=float(total_loss),
        requested_labels=int(n_requested),
        deployment_switches=int(n_switches),
        records=records,
        refused_requests=int(n_refused),
    )


def check_no_future_access(result: EpisodeResult, delay: int) -> list[str]:
    """Validation: no label may be released before its delay has elapsed."""
    problems = []
    for r in result.records:
        if r["release_time"] is not None and r["release_time"] - r["request_time"] != delay:
            problems.append(f"event {r['event_id']}: release-request != delay")
    return problems


def check_budget_feasible(result: EpisodeResult, budget: int) -> list[str]:
    """Validation: the hard cap holds pathwise, not merely on average."""
    problems = []
    if result.requested_labels > budget:
        problems.append(f"{result.policy}: {result.requested_labels} labels > budget {budget}")
    for r in result.records:
        if r["budget_remaining"] < 0:
            problems.append(f"{result.policy}: negative budget at event {r['event_id']}")
    return problems
