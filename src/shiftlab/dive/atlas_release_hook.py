"""Informative label release for Failure Atlas family 4 (Amendment 6, item 3).

``switching_explore.run`` releases every label at ``t + cfg.d``. :func:`run_informative` is a
parallel harness (``switching_explore`` is untouched) in which the release delay depends on the
outcome: a label queried at round ``t`` is released at ``t + delay_fn(D_t)``.

What is kept from ``run``: event order, budget charged at request time (``BudgetExceeded`` on
overuse), methods see only ``(t, released)``, and scoring through ``score_actions``.

What changes: labels are delivered in *release* order, so a later query with a short delay can be
released before an earlier one with a long delay (out-of-order release), and several labels can be
released in the same round (ties are listed in event order, as ``run`` would list them).

Declared misspecification: methods were written for a fixed delay and keep using ``cfg.d`` (the
base ``d``) internally, e.g. ``Method.can_query`` (``t + d <= T``), the uniform calendar on
``[1, T - d]``, and pending-cap logic. With a delay larger than ``d`` a query that passes
``can_query`` can be released after ``T``; such a query is charged but never delivered and is
counted in ``wasted_queries`` (the base ``score_actions`` count is replaced by this one).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable

import numpy as np

from shiftlab.dive.switching_explore import (
    BudgetExceeded,
    Config,
    Method,
    Released,
    RunResult,
    Stream,
    score_actions,
)

DelayFn = Callable[[float], int]


def outcome_delay(d_f: int, d_u: int) -> DelayFn:
    """Delay map: favourable labels (``D < 0``) after ``d_f``, the others after ``d_u``."""
    if d_f < 1 or d_u < 1:
        raise ValueError("delays must be >= 1")

    def fn(D: float) -> int:
        return d_f if D < 0 else d_u

    return fn


def run_informative(stream: Stream, method: Method, cfg: Config, delay_fn: DelayFn) -> RunResult:
    """Play one stream with outcome-dependent release; same contract as ``run`` otherwise."""
    if stream.T != cfg.T:
        raise ValueError("stream length must equal cfg.T")
    D = stream.D
    pending: dict[int, list[tuple[int, float]]] = {}
    actions = np.zeros(cfg.T, dtype=int)
    qmask = np.zeros(cfg.T, dtype=float)
    released_log: list[Released] = []
    used = wasted = 0
    method.start(cfg)
    for t in range(1, cfg.T + 1):
        due: Released = tuple(sorted(pending.pop(t, ()), key=lambda x: x[0]))
        released_log.append(due)
        action, query = method.step(t, due)
        if action not in (0, 1):
            raise ValueError("action must be 0 or 1")
        if query:
            if used >= cfg.B:
                raise BudgetExceeded(f"query {used + 1} requested with B={cfg.B} at round {t}")
            used += 1
            qmask[t - 1] = 1.0
            x = float(D[t - 1])
            delay = int(delay_fn(x))
            if delay < 1:
                raise ValueError("release delay must be >= 1")
            if t + delay <= cfg.T:
                pending.setdefault(t + delay, []).append((t, x))
            else:
                wasted += 1  # charged at request time, released after the horizon
        actions[t - 1] = action
    res = score_actions(stream, cfg, actions, qmask, released_log)
    return dataclasses.replace(res, wasted_queries=wasted)


ORDERED_LABEL_METHODS = frozenset({"c1_hmm_cs"})  # HMMBank raises on out-of-order events


class ReorderBuffer:
    """Head-of-line-blocking adapter for a method that requires labels in event order.

    ``HMMBank.update`` accepts labels only in strictly increasing event order, so under out-of-order
    release ``c1_hmm_cs`` would raise. The adapter holds a released label until every earlier query
    has been released, then passes the ready labels in event order. It uses only information the
    method owns (its own queries and the released labels); it adds no outcome information and is the
    identity when release is in order (so it is exact when ``d_f = d_u``).
    """

    def __init__(self, inner: Method):
        self.inner = inner
        self.name = getattr(inner, "name", "wrapped")

    def start(self, cfg: Config) -> None:
        self.buf: list[tuple[int, float]] = []
        self.outstanding: set[int] = set()
        self.inner.start(cfg)

    def step(self, t: int, released: Released) -> tuple[int, bool]:
        for ev, x in released:
            self.outstanding.discard(ev)
            self.buf.append((ev, x))
        horizon = min(self.outstanding) if self.outstanding else None
        ready = sorted(b for b in self.buf if horizon is None or b[0] < horizon)
        self.buf = [b for b in self.buf if horizon is not None and b[0] >= horizon]
        action, query = self.inner.step(t, tuple(ready))
        if query:
            self.outstanding.add(t)
        return action, query
