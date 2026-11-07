"""Windowed active auditing with delayed labels, hard pathwise budget, and a swappable request-size policy."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import numpy as np


class LeakageError(RuntimeError): ...


class BudgetError(RuntimeError): ...


class LabelStore:
    """The only path from the (hidden) oracle to the controller.  A label requested at t for item i is
    released at max(i + delay, t + latency); get() before release raises LeakageError; requests beyond
    ``budget`` raise BudgetError (pathwise enforcement)."""

    def __init__(
        self, oracle: Callable[[int], int], delay: int = 50, latency: int = 0, budget: int = 3000
    ):
        self._oracle, self.delay, self.latency, self.budget = oracle, delay, latency, budget
        self.release: dict[int, int] = {}
        self.request_t: dict[int, int] = {}
        self.spent = 0
        self.log: list[tuple[int, int, int]] = []  # (t_request, i, t_release)

    @property
    def remaining(self):
        return self.budget - self.spent

    def request(self, i: int, t: int) -> bool:
        if i in self.release:
            return False  # cached, free
        if i > t:
            raise LeakageError("cannot label a future item")
        if self.spent >= self.budget:
            raise BudgetError("label budget exhausted")
        self.spent += 1
        self.release[i] = max(i + self.delay, t + self.latency)
        self.request_t[i] = t
        self.log.append((t, i, self.release[i]))
        return True

    def is_released(self, i, t):
        return i in self.release and self.release[i] <= t

    def get(self, i: int, t: int) -> int:
        if not self.is_released(i, t):
            raise LeakageError(f"label {i} used at t={t} before release {self.release.get(i)}")
        return int(self._oracle(i))

    def released(self, t: int, lo: int = 0, hi: int | None = None):
        return [
            i for i, r in self.release.items() if r <= t and i >= lo and (hi is None or i <= hi)
        ]

    def pending(self, t: int):
        return sum(1 for r in self.release.values() if r > t)


@dataclass
class QueryContext:
    t: int
    belief: np.ndarray
    prev_U: float
    prev_risk_hat: float
    prev_rad: float
    tau: float
    budget_remaining: int
    horizon: int | None = None
    pending: int = 0
    window_size: int = 0


class LabelRequestPolicy(Protocol):
    """Q2 hook.  Decides ONLY how many uniformly-sampled window items to label now (0 = skip).  Which
    indices are labelled stays uniform inside WindowedAuditor, so the certificate is unchanged."""

    def request_size(self, ctx: QueryContext) -> int: ...


class HeuristicQueryPolicy:
    """Reconstruction of QueryPolicy (paper gives only qualitative text + k_max=64,k_high=32,k_low=8,m_low=0.02;
    zeta=2.0 is listed but its role is unspecified and unused here)."""

    def __init__(self, k_max=64, k_high=32, k_low=8, m_low=0.02, audit_every=10):
        self.k_max, self.k_high, self.k_low, self.m_low, self.audit_every = (
            k_max,
            k_high,
            k_low,
            m_low,
            audit_every,
        )

    def request_size(self, ctx: QueryContext) -> int:
        if ctx.t % self.audit_every != 0:
            return 0
        drift_mass = 1.0 - float(ctx.belief[0])
        margin = (
            ctx.tau
            - (ctx.prev_risk_hat if np.isfinite(ctx.prev_risk_hat) else 0.0)
            - (ctx.prev_rad if np.isfinite(ctx.prev_rad) else 0.0)
        )
        if ctx.prev_U > ctx.tau and drift_mass > 0.5:
            k = self.k_max
        elif drift_mass > 0.5 or margin < self.m_low:
            k = self.k_high
        else:
            k = self.k_low
        return min(k, ctx.budget_remaining)


class WindowedAuditor:
    def __init__(self, store: LabelStore, N=1024, window_mode="delayed", pool="window"):
        assert window_mode in ("delayed", "current") and pool in ("window", "round")
        self.store, self.N, self.window_mode, self.pool = store, N, window_mode, pool
        self.last_Q: list[int] = []

    def window(self, t):
        hi = t - self.store.delay if self.window_mode == "delayed" else t
        lo = max(0, hi - self.N + 1)
        return lo, hi

    def sample(self, t, n, rng) -> tuple[list[int], list[int]]:
        """Uniform sample (random-permutation prefix) of size <= n from the window; truncated by the budget
        using only index-level facts (cache status), never label values => selection independent of labels."""
        lo, hi = self.window(t)
        if hi < lo or n <= 0:
            return [], []
        perm = rng.permutation(np.arange(lo, hi + 1))[:n]
        Q, J = [], []
        for i in perm:
            i = int(i)
            if i not in self.store.release:
                if self.store.remaining <= 0:
                    break
                self.store.request(i, t)
                J.append(i)
            Q.append(i)
        self.last_Q = Q if Q else self.last_Q
        return Q, J

    def audited_indices(self, t):
        if self.pool == "round":
            idx = self.last_Q
        else:
            lo, hi = self.window(t)
            idx = self.store.released(t, lo, hi)
        return [i for i in idx if self.store.is_released(i, t)]

    def losses(self, t, predict: Callable[[np.ndarray], np.ndarray]):
        idx = self.audited_indices(t)
        if not idx:
            return np.zeros(0), idx
        y = np.array([self.store.get(i, t) for i in idx])
        yhat = predict(np.array(idx))
        return (yhat != y).astype(float), idx
