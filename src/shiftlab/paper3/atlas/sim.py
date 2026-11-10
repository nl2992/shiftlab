"""Streaming deployment simulator for the Paper 3 atlas (workstream C).

Event/QueryRequest/ReleasedFeedback types and the budgeted-query accounting follow
8af33afe934c3c5dba03caa55257125941f6df4f:scripts/promising_directions/sota/simulator.py (origin/main).
ATLAS CHANGES: (i) per-event release delays (``delays[t]``), so delay may depend on the evaluator-side
outcome (informative delay) -- the policy never sees the delay rule; (ii) array-based traces;
(iii) the cost identity J = loss + c_q*queries + k*switches is returned in parts.
Evaluator-side truth (regimes, gains) is never passed to a policy.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Event:
    event_id: int
    t: int
    horizon: int
    model_predictions: np.ndarray
    context: Any = None


@dataclass(frozen=True)
class QueryRequest:
    requested: bool
    probability: float = 0.0
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ReleasedFeedback:
    event_id: int
    t_requested: int
    t_released: int
    label: int
    model_losses: np.ndarray
    query_probability: float
    extra: dict = field(default_factory=dict)


def policy_rng(seed_base: int, episode: int, policy_name: str) -> np.random.Generator:
    h = hashlib.sha256(policy_name.encode()).digest()[:8]
    return np.random.default_rng(
        np.random.SeedSequence([seed_base, episode, int.from_bytes(h, "big") % (2**31)])
    )


def preds_from_losses(losses: np.ndarray, rng: np.random.Generator):
    """Balanced labels with predictions = label XOR loss (reproduces the loss stream exactly)."""
    labels = rng.integers(0, 2, losses.shape[0])
    preds = labels[:, None].astype(int) ^ losses.astype(int)
    return preds, labels


@dataclass
class EpisodeOut:
    dep: np.ndarray  # (T,) deployed model at each event
    req: np.ndarray  # (T,) 1 if a query was granted at t
    loss: float
    n_queries: int
    n_switches: int
    n_refused: int
    max_pending: int
    cost: float


def run_episode(policy, preds, labels, delays, *, budget, price, switch_cost) -> EpisodeOut:
    """One episode. ``delays[t] >= 1`` is the release delay of a label requested at t."""
    T = preds.shape[0]
    deployed, remaining = 0, int(budget)
    dep = np.zeros(T, np.int8)
    req = np.zeros(T, np.int8)
    pending: dict[int, list] = {}
    n_pend = 0
    max_pend = 0
    n_sw = n_ref = 0
    total = 0.0
    for t in range(T):
        ev = Event(t, t, T, preds[t])
        due = pending.pop(t, None)
        if due:
            n_pend -= len(due)
            policy.observe(due)
        prev = deployed
        deployed = int(policy.predict(ev))
        if deployed not in (0, 1):
            raise ValueError("invalid model index")
        n_sw += int(deployed != prev)
        total += float(preds[t, deployed] != labels[t])
        dep[t] = deployed
        r = policy.request_labels(ev, remaining)
        if r.requested and remaining <= 0:
            n_ref += 1
        elif r.requested:
            remaining -= 1
            req[t] = 1
            rt = t + int(delays[t])
            if rt < T:
                pending.setdefault(rt, []).append(
                    ReleasedFeedback(
                        t,
                        t,
                        rt,
                        int(labels[t]),
                        (preds[t] != labels[t]).astype(np.int8),
                        float(r.probability),
                        dict(r.extra),
                    )
                )
                n_pend += 1
                max_pend = max(max_pend, n_pend)
    nq = int(req.sum())
    return EpisodeOut(
        dep, req, total, nq, n_sw, n_ref, max_pend, total + price * nq + switch_cost * n_sw
    )
