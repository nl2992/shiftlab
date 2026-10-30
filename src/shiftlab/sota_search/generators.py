"""Synthetic streams with separately measurable discrepancy, predictive deterioration and decision harm.

A fixed logistic model (the source Bayes classifier) takes cost-sensitive decisions. Shifts act on
covariates (benign nuisance or informative directions), the label prior, the concept (conditional),
or a subgroup, on abrupt, gradual, transient or recurrent schedules. Ground truth per step is
evaluator-only and never passed to a detector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

D = 4
W_SRC = np.array([1.5, 1.0, 0.0, 0.0])
B_SRC = 0.0
FN_COST, FP_COST = 5.0, 1.0
TAU = FP_COST / (FP_COST + FN_COST)  # predict positive when P(y=1|x) >= TAU
HARM_THRESHOLD = 0.10  # expected decision-cost increase counted as harmful


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def decision_cost(act, y):
    return act * (1 - y) * FP_COST + (1 - act) * y * FN_COST


KINDS = ("none", "cov_benign", "cov_inform", "prior", "concept", "subgroup")


def _delta_terms(kind: str, delta: float):
    dmu, dw, db, dsub = np.zeros(D), np.zeros(D), 0.0, 0.0
    if kind == "cov_benign":
        dmu[2] = delta
    elif kind == "cov_inform":
        dmu[0] = delta
    elif kind == "prior":
        db = delta
    elif kind == "concept":
        dw[0], dw[1] = -delta, delta
    elif kind == "subgroup":
        dsub = -delta
    elif kind != "none":
        raise ValueError(kind)
    return dmu, dw, db, dsub


def schedule(
    shape: str, T: int, t0: int, ramp: int = 200, length: int = 400, period: int = 600
) -> np.ndarray:
    t = np.arange(T)
    if shape == "abrupt":
        return (t >= t0).astype(float)
    if shape == "gradual":
        return np.clip((t - t0) / max(ramp, 1), 0.0, 1.0)
    if shape == "transient":
        return ((t >= t0) & (t < t0 + length)).astype(float)
    if shape == "recurrent":
        return ((t >= t0) & (((t - t0) // (period // 2)) % 2 == 0)).astype(float)
    raise ValueError(shape)


@dataclass(frozen=True)
class World:
    kind: str = "none"
    delta: float = 0.0
    shape: str = "abrupt"
    T: int = 2000
    t0: int = 800
    ramp: int = 200
    length: int = 400
    period: int = 600
    family: str = "G1"
    extra: tuple = field(default=())

    def key(self) -> str:
        return f"{self.family}|{self.kind}|{self.delta:g}|{self.shape}|{self.t0}"


def _sample(rng, n: int, kind: str, delta: float, m: float):
    dmu, dw, db, dsub = _delta_terms(kind, delta)
    x = rng.standard_normal((n, D)) + m * dmu
    logit = x @ (W_SRC + m * dw) + B_SRC + m * db + m * dsub * (x[:, 2] > 1.0)
    return x, (rng.random(n) < sigmoid(logit)).astype(np.int8)


def _rbf_mmd2(a, b, gamma):
    def k(u, v):
        return np.exp(-gamma * ((u[:, None, :] - v[None, :, :]) ** 2).sum(-1))

    n, m = len(a), len(b)
    kaa, kbb, kab = k(a, a), k(b, b), k(a, b)
    return (
        (kaa.sum() - np.trace(kaa)) / (n * (n - 1))
        + (kbb.sum() - np.trace(kbb)) / (m * (m - 1))
        - 2 * kab.mean()
    )


@lru_cache(maxsize=256)
def population_effects(kind: str, delta: float, n: int = 40_000):
    """Evaluator-only effect curves over shift strength m in [0, 1]: (m_grid, disc, pred, harm)."""
    grid = np.linspace(0.0, 1.0, 11)
    rng = np.random.default_rng(12345)
    xs, ys = _sample(rng, n, "none", 0.0, 0.0)
    ps = sigmoid(xs @ W_SRC + B_SRC)
    cost_src = decision_cost((ps >= TAU).astype(float), ys).mean()
    brier_src = ((ps - ys) ** 2).mean()
    ref = np.c_[xs[:1500], ys[:1500]]
    disc, pred, harm = [], [], []
    for m in grid:
        x, y = _sample(np.random.default_rng(777), n, kind, delta, float(m))
        p = sigmoid(x @ W_SRC + B_SRC)
        harm.append(decision_cost((p >= TAU).astype(float), y).mean() - cost_src)
        pred.append(((p - y) ** 2).mean() - brier_src)
        cur = np.c_[x[:1500], y[:1500]]
        disc.append(max(_rbf_mmd2(ref, cur, 0.25), 0.0))
    return grid, np.array(disc), np.array(pred), np.array(harm)


def truth(world: World):
    """Per-step ground truth arrays (discrepancy, predictive deterioration, decision harm, harmful flag)."""
    m = schedule(world.shape, world.T, world.t0, world.ramp, world.length, world.period)
    grid, disc, pred, harm = population_effects(world.kind, world.delta)
    d_t, p_t, h_t = np.interp(m, grid, disc), np.interp(m, grid, pred), np.interp(m, grid, harm)
    return {
        "m": m,
        "discrepancy": d_t,
        "predictive": p_t,
        "harm": h_t,
        "harmful": h_t >= HARM_THRESHOLD,
    }


def simulate(world: World, n_seeds: int, seed: int):
    """Streams for ``n_seeds`` independent replicates. Detectors receive x, y, p only."""
    rng = np.random.default_rng(seed)
    m = schedule(world.shape, world.T, world.t0, world.ramp, world.length, world.period)
    dmu, dw, db, dsub = _delta_terms(world.kind, world.delta)
    T = world.T
    x = rng.standard_normal((n_seeds, T, D)) + m[None, :, None] * dmu
    w = W_SRC[None, None, :] + m[None, :, None] * dw
    logit = (x * w).sum(-1) + B_SRC + m * db + m * dsub * (x[:, :, 2] > 1.0)
    y = (rng.random((n_seeds, T)) < sigmoid(logit)).astype(np.int8)
    p = sigmoid(x @ W_SRC + B_SRC)
    act = (p >= TAU).astype(float)
    return {
        "x": x.astype(np.float32),
        "y": y,
        "p": p,
        "loss": decision_cost(act, y),
        "brier": (p - y) ** 2,
        "world": world,
    }
