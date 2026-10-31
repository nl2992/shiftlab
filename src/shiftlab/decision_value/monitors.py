"""Vectorised monitors (state arrays shape (n,), one entry per episode).

Interface: ``update(x, valid)`` consumes one released observation per episode (masked by ``valid``),
``statistic`` is an (n,) array, ``reset(mask)`` restarts the selected episodes, alarm = statistic >
``threshold`` (threshold set by calibration or nominally). Observations are bounded in [-1, 1].

Targets: 'paired' x = l0 - l1 (null E[x] <= 0); 'incumbent' x = l0 - r0 with r0 the mean of released
labels from the first ``cal`` events (never the evaluator's truth).

This module must not import synthetic/truth objects (information-flow test greps the source).

Fidelity: see FIDELITY below and docs/decision_value/05_EXPERIMENTAL_CONTRACT.md.
  cusum   -> repo shiftlab.monitoring.one_sided_cusum (baseline_mean=0, scale=1, slack=k): equivalence tested.
  kelly   -> repo shiftlab.dive.eprocess.MultiTimescaleStartedKellyEProcess (starts=(0,), bound=1): equivalence tested.
  page_hinkley, batch, sr_betting -> textbook reimplementations (no repo counterpart found).
"""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp

FIDELITY = {
    "cusum": "TEXTBOOK; numerically checked vs shiftlab.monitoring.one_sided_cusum",
    "page_hinkley": "TEXTBOOK (Page 1954; standard running-mean form with delta); no repo counterpart",
    "batch": "TEXTBOOK fixed-sample one-sided z on non-overlapping window means; no repo counterpart",
    "sr_betting": "TEXTBOOK Shin-Ramdas-Rinaldo e-detector, uniform mixture over a lambda grid; no repo counterpart",
    "kelly_h2c_inspired": "H2c-inspired (SOURCE_INSPIRED): discounted predictable Kelly mixture; numerically checked "
    "vs shiftlab.dive.eprocess.MultiTimescaleStartedKellyEProcess (starts=(0,))",
}


class Monitor:
    name = "monitor"
    log_scale = False  # statistic is a log e-value

    def __init__(self, n: int, target: str = "paired", cal: int = 300, **hp):
        self.n, self.target, self.cal, self.hp = n, target, cal, hp
        self.threshold = np.inf
        self._init()

    def _init(self): ...

    def update(self, x, valid): ...

    @property
    def statistic(self) -> np.ndarray: ...

    _state: tuple = ()

    def reset(self, mask):
        keep = ~np.asarray(mask, bool)
        old = {k: getattr(self, k).copy() for k in self._state}
        self._init()
        for k, v in old.items():  # restore episodes that are not reset
            getattr(self, k)[keep] = v[keep]

    def alarm(self) -> np.ndarray:
        return self.statistic > self.threshold

    def spec(self) -> dict:
        return {
            "name": self.name,
            "target": self.target,
            "fidelity": FIDELITY[self.name],
            "hyperparameters": dict(self.hp),
        }


class CUSUM(Monitor):
    name = "cusum"
    _state = ("s",)

    def _init(self):
        self.k = self.hp.setdefault("k", 0.02)
        self.s = np.zeros(self.n)

    def update(self, x, valid):
        self.s = np.where(valid, np.maximum(0.0, self.s + x - self.k), self.s)

    statistic = property(lambda self: self.s)


class PageHinkley(Monitor):
    name = "page_hinkley"
    _state = ("cnt", "mean", "m", "M")

    def _init(self):
        self.delta = self.hp.setdefault("delta", 0.005)
        self.cnt = np.zeros(self.n)
        self.mean = np.zeros(self.n)
        self.m = np.zeros(self.n)
        self.M = np.zeros(self.n)

    def update(self, x, valid):
        c = self.cnt + valid
        mean = np.where(valid, self.mean + (x - self.mean) / np.maximum(c, 1), self.mean)
        m = np.where(valid, self.m + x - mean - self.delta, self.m)
        self.cnt, self.mean, self.m = c, mean, m
        self.M = np.minimum(self.M, m)

    statistic = property(lambda self: self.m - self.M)


class BatchTest(Monitor):
    """Non-overlapping windows of n_b released labels; statistic = last completed window's one-sided
    z = mean / (sd / sqrt(n_b)) (sd floored at 0.05 to avoid 0/0 on constant windows)."""

    name = "batch"
    _state = ("cnt", "sum", "sumsq", "z")

    def _init(self):
        self.nb = self.hp.setdefault("n_b", 50)
        self.sd_floor = self.hp.setdefault("sd_floor", 0.05)
        self.cnt = np.zeros(self.n)
        self.sum = np.zeros(self.n)
        self.sumsq = np.zeros(self.n)
        self.z = np.full(self.n, -np.inf)

    def update(self, x, valid):
        self.cnt = self.cnt + valid
        self.sum = self.sum + np.where(valid, x, 0.0)
        self.sumsq = self.sumsq + np.where(valid, x * x, 0.0)
        done = self.cnt >= self.nb
        if done.any():
            mean = self.sum / self.nb
            sd = np.sqrt(np.maximum(self.sumsq / self.nb - mean**2, 0.0) * self.nb / (self.nb - 1))
            z = mean / (np.maximum(sd, self.sd_floor) / np.sqrt(self.nb))
            self.z = np.where(done, z, self.z)
            self.cnt = np.where(done, 0.0, self.cnt)
            self.sum = np.where(done, 0.0, self.sum)
            self.sumsq = np.where(done, 0.0, self.sumsq)

    statistic = property(lambda self: self.z)


class SRBetting(Monitor):
    """R_t^lam = (1 + R_{t-1}^lam)(1 + lam x_t), R_0 = 0; statistic = log of the uniform mixture over
    the lambda grid. Valid lambda in [0, 1) for x in [-1, 1]. Log domain to avoid overflow."""

    name = "sr_betting"
    _state = ("logR",)
    log_scale = True

    def _init(self):
        self.lams = np.asarray(self.hp.setdefault("lambdas", (0.05, 0.1, 0.2, 0.4, 0.8)), float)
        if np.any(self.lams < 0) or np.any(self.lams >= 1):
            raise ValueError("lambda must lie in [0, 1) for x in [-1, 1]")
        self.logR = np.full((self.n, len(self.lams)), -np.inf)

    def update(self, x, valid):
        new = np.logaddexp(0.0, self.logR) + np.log1p(self.lams[None, :] * x[:, None])
        self.logR = np.where(valid[:, None], new, self.logR)

    statistic = property(lambda self: logsumexp(self.logR, axis=1) - np.log(len(self.lams)))


class KellyH2c(Monitor):
    """H2c-inspired (SOURCE_INSPIRED) discounted predictable-Kelly betting e-process, single start at
    0: lambda_t = clip(max(mhat, 0) / vhat, 0, max_stake) from discounted past released x, mixture over
    half-lives. A valid e-process under E[x_t | F_{t-1}] <= 0, |x| <= 1 (predictable bet in [0, 1))."""

    name = "kelly_h2c_inspired"
    _state = ("logw", "m1", "m2")
    log_scale = True

    def _init(self):
        self.hl = np.asarray(self.hp.setdefault("half_lives", (16.0, 64.0, 256.0)), float)
        self.max_stake = self.hp.setdefault("max_stake", 0.5)
        self.v0 = self.hp.setdefault("prior_second_moment", 0.25)
        self.decay = np.exp2(-1.0 / self.hl)
        shape = (self.n, len(self.hl))
        self.logw = np.zeros(shape)
        self.m1 = np.zeros(shape)
        self.m2 = np.full(shape, self.v0)

    def stakes(self):
        return np.clip(
            np.maximum(self.m1, 0.0) / np.maximum(self.m2, np.finfo(float).tiny),
            0.0,
            self.max_stake,
        )

    def update(self, x, valid):
        v = valid[:, None]
        xx = x[:, None]
        self.logw = self.logw + np.where(v, np.log1p(self.stakes() * xx), 0.0)
        d = self.decay[None, :]
        self.m1 = np.where(v, d * self.m1 + (1 - d) * xx, self.m1)
        self.m2 = np.where(v, d * self.m2 + (1 - d) * xx**2, self.m2)

    statistic = property(lambda self: logsumexp(self.logw, axis=1) - np.log(len(self.hl)))


MONITORS = {c.name: c for c in (CUSUM, PageHinkley, BatchTest, SRBetting, KellyH2c)}


def monitor_factory(name: str, target: str = "paired", cal: int = 300, **hp):
    """Return ``build(n) -> Monitor`` (threshold must be set by calibration or nominal rule)."""
    cls = MONITORS[name]
    return lambda n: cls(n, target=target, cal=cal, **hp)


def nominal_log_threshold(alpha: float = 0.05) -> float:
    """Nominal 1/alpha rule on the log e-value scale (e-detectors only; reported separately)."""
    return float(np.log(1.0 / alpha))


class Target:
    """Maps released labels to the monitor's input series (stateful: incumbent reference risk)."""

    def __init__(self, kind: str, n: int, cal: int = 300):
        if kind not in ("paired", "incumbent"):
            raise ValueError(kind)
        self.kind, self.cal = kind, cal
        self.sum0, self.cnt = np.zeros(n), np.zeros(n)

    def transform(self, rel):
        if self.kind == "paired":
            return rel.l0 - rel.l1, rel.valid
        if rel.event < self.cal:
            self.sum0 = self.sum0 + np.where(rel.valid, rel.l0, 0.0)
            self.cnt = self.cnt + rel.valid
            return np.zeros_like(rel.l0), np.zeros_like(rel.valid)
        r0 = self.sum0 / np.maximum(self.cnt, 1)
        return rel.l0 - r0, rel.valid & (self.cnt > 0)
