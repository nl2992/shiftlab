"""Payback certificates B0/B1/B2.  A certifier sees only released labels (request time s, value z in
[-1,1], arrival time) and the declared envelope; it never sees mu.  Each exposes

    start_batch(r, n)        -- a batch of n queries is committed at (predictable) time r
    observe(s, z, t)         -- label requested at s released at t
    lcb_sum(t, h)            -- lower confidence bound on sum_{j<h} mu_{t+j}  (-inf if no evidence)

and certifies a switch at t for hold-horizon h iff lcb_sum(t,h) > k.

Labels:  B0a/B0w: IN_HOUSE_HEURISTIC;  B0b: IN_HOUSE_HEURISTIC (Regol-style adapter, not
source-faithful: the paper was not retrieved);  B1: the internal age-corrected Hoeffding envelope
(docs/switching_mechanism_screen_v1.md, valid only at pre-committed completed batches);
B1n: B1 with naive optional continuation (INVALID, counterexample);  B2: time-uniform
normal-mixture confidence sequence per batch, alpha spent as alpha/(b(b+1)).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .envelope import Envelope
from .exact import mixture_boundary, mixture_rho

NEG = -math.inf


@dataclass
class _Batch:
    r: int
    n: int
    alpha_b: float
    rho: float
    reqs: list = field(default_factory=list)  # request times
    zs: list = field(default_factory=list)


def _window_term(env: Envelope, t: int, h: int, reqs) -> float:
    """(1/m) sum_i sum_{j<h} drop(t + j - s_i)."""
    tab = env.future_drop_table(h, t + 1)
    return float(tab[t - np.asarray(reqs)].mean())


class _BatchCert:
    def __init__(self, env: Envelope, alpha: float):
        self.env, self.alpha = env, alpha
        self.batches: list[_Batch] = []

    def alpha_b(self, b: int) -> float:  # b is 1-based
        return self.alpha / (b * (b + 1))

    def start_batch(self, r: int, n: int):
        b = len(self.batches) + 1
        ab = self.alpha_b(b)
        self.batches.append(_Batch(r, n, ab, mixture_rho(ab, max(n, 2))))

    def observe(self, s: int, z: float, t: int):
        for bt in reversed(self.batches):
            if bt.r <= s < bt.r + bt.n:
                bt.reqs.append(s)
                bt.zs.append(z)
                return
        raise ValueError("label outside any batch")

    def _radius(self, bt: _Batch, m: int) -> float:  # deviation of the SUM, S_m
        raise NotImplementedError

    def _eligible(self, bt: _Batch) -> bool:
        return len(bt.zs) > 0

    def lcb_sum(self, t: int, h: int) -> float:
        best = NEG
        for bt in self.batches:
            if not self._eligible(bt):
                continue
            m = len(bt.zs)
            mean_lcb = (sum(bt.zs) - self._radius(bt, m)) / m
            val = h * mean_lcb - _window_term(self.env, t, h, bt.reqs)
            best = max(best, val)
        return best


class B2Certificate(_BatchCert):
    """Time-uniform (within batch) normal-mixture CS; alpha spent over batches; valid under
    stopping at any label arrival and any adaptive choice of (t, h, batch)."""

    def _radius(self, bt, m):
        return mixture_boundary(bt.alpha_b, bt.rho)(m)


class B1Certificate(_BatchCert):
    """Fixed-n Hoeffding envelope (internal screen).  Evaluated only on batches that are complete."""

    def _eligible(self, bt):
        return len(bt.zs) == bt.n

    def _radius(self, bt, m):
        return math.sqrt(2 * math.log(1 / bt.alpha_b) * m)


class B1NaiveContinuation(_BatchCert):
    """Same formula evaluated after every arrival (optional continuation): NOT valid."""

    def _radius(self, bt, m):
        return math.sqrt(2 * math.log(1 / bt.alpha_b) * m)


class B0Window:
    """Recent-window LCB + horizon hurdle: last w released labels, Hoeffding at level alpha, no
    drift/age correction, no multiplicity correction."""

    def __init__(self, env: Envelope, alpha: float, w: int, gauss: bool = False):
        self.alpha, self.w, self.gauss = alpha, w, gauss
        self.log: list[tuple[int, float]] = []

    def start_batch(self, r, n):
        pass

    def observe(self, s, z, t):
        self.log.append((s, z))

    def lcb_sum(self, t, h):
        if len(self.log) < 2:
            return NEG
        zs = np.array([z for _, z in self.log[-self.w :]])
        m = len(zs)
        if self.gauss:
            from scipy.stats import norm

            rad = norm.ppf(1 - self.alpha) * max(zs.std(ddof=1), 1e-9) / math.sqrt(m)
        else:
            rad = math.sqrt(2 * math.log(1 / self.alpha) / m)
        return h * (zs.mean() - rad)


class B0Forecast:
    """Regol-style forecast-quantile payback (in-house adapter): OLS trend on the last w labels,
    Gaussian predictive distribution for the horizon sum (parameter + residual noise, independent
    future noise), certify when its alpha-quantile exceeds the hurdle."""

    def __init__(self, env: Envelope, alpha: float, w: int):
        self.alpha, self.w = alpha, w
        self.log: list[tuple[int, float]] = []

    def start_batch(self, r, n):
        pass

    def observe(self, s, z, t):
        self.log.append((s, z))

    def lcb_sum(self, t, h):
        from scipy.stats import norm

        pts = self.log[-self.w :]
        if len(pts) < 4:
            return NEG
        x = np.array([s for s, _ in pts], float)
        y = np.array([z for _, z in pts], float)
        X = np.stack([np.ones_like(x), x - x.mean()], 1)
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        res = y - X @ beta
        s2 = max(float(res @ res) / (len(y) - 2), 1e-6)
        xf = np.arange(t, t + h, dtype=float) - x.mean()
        Xf = np.stack([np.ones(h), xf], 1)
        mean = float((Xf @ beta).sum())
        cov = s2 * np.linalg.inv(X.T @ X)
        g = Xf.sum(0)
        var = float(g @ cov @ g) + h * s2
        return mean - norm.ppf(1 - self.alpha) * math.sqrt(var)


def plan_batch_size(env: Envelope, alpha_b: float, cap: int) -> int:
    """Integer n<=cap minimising  sqrt(2 ln(1/alpha_b)/n) + window bias(n)  (equal for all certifiers)."""
    best, arg = math.inf, 1
    la = math.log(1 / alpha_b)
    for n in range(1, max(cap, 1) + 1):
        val = math.sqrt(2 * la / n) + sum(env.drop(i) for i in range(n)) / n
        if val < best:
            best, arg = val, n
    return arg
