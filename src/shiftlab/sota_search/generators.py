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


def nonlinear_term(x):
    """G2: interaction and curvature the linear deployed model cannot represent (zero mean under the source)."""
    return 0.8 * x[..., 0] * x[..., 1] - 0.5 * (x[..., 2] ** 2 - 1.0)


def _sample(rng, n: int, kind: str, delta: float, m: float, family: str = "G1"):
    dmu, dw, db, dsub = _delta_terms(kind, delta)
    x = rng.standard_normal((n, D)) + m * dmu
    logit = x @ (W_SRC + m * dw) + B_SRC + m * db + m * dsub * (x[:, 2] > 1.0)
    if family == "G2":
        logit = logit + nonlinear_term(x)
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
def population_effects(kind: str, delta: float, family: str = "G1", n: int = 40_000):
    """Evaluator-only effect curves over shift strength m in [0, 1]: (m_grid, disc, pred, harm)."""
    grid = np.linspace(0.0, 1.0, 11)
    rng = np.random.default_rng(12345)
    xs, ys = _sample(rng, n, "none", 0.0, 0.0, family)
    ps = sigmoid(xs @ W_SRC + B_SRC)
    cost_src = decision_cost((ps >= TAU).astype(float), ys).mean()
    brier_src = ((ps - ys) ** 2).mean()
    ref = np.c_[xs[:1500], ys[:1500]]
    disc, pred, harm = [], [], []
    for m in grid:
        x, y = _sample(np.random.default_rng(777), n, kind, delta, float(m), family)
        p = sigmoid(x @ W_SRC + B_SRC)
        harm.append(decision_cost((p >= TAU).astype(float), y).mean() - cost_src)
        pred.append(((p - y) ** 2).mean() - brier_src)
        cur = np.c_[x[:1500], y[:1500]]
        disc.append(max(_rbf_mmd2(ref, cur, 0.25), 0.0))
    return grid, np.array(disc), np.array(pred), np.array(harm)


def truth(world: World):
    """Per-step ground truth arrays (discrepancy, predictive deterioration, decision harm, harmful flag)."""
    m = schedule(world.shape, world.T, world.t0, world.ramp, world.length, world.period)
    grid, disc, pred, harm = population_effects(world.kind, world.delta, world.family)
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
    if world.family == "G2":
        logit = logit + nonlinear_term(x)
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


# G3: Markov-switching regimes. 0 = source, 1 = harmful concept shift (delta 2), 2 = benign covariate shift (delta 3).
G3_P = np.array([[0.997, 0.0015, 0.0015], [0.003, 0.995, 0.002], [0.003, 0.002, 0.995]])
G3_KINDS = (("none", 0.0), ("concept", 2.0), ("cov_benign", 3.0))


def simulate_g3(n_seeds: int, seed: int, T: int = 2000, transition=None):
    """Per-seed hidden regime paths with ground-truth regime labels; harm is a function of the regime."""
    rng = np.random.default_rng(seed)
    P = G3_P if transition is None else np.asarray(transition)
    reg = np.zeros((n_seeds, T), dtype=np.int8)
    u = rng.random((n_seeds, T))
    cum = P.cumsum(1)
    for t in range(1, T):
        reg[:, t] = (u[:, t, None] > cum[reg[:, t - 1]]).sum(1)
    terms = np.array([_delta_terms(k, d) for k, d in G3_KINDS], dtype=object)
    dmu = np.stack([np.asarray(t[0], dtype=float) * np.ones(D) for t in terms])
    dw = np.stack([np.asarray(t[1], dtype=float) * np.ones(D) for t in terms])
    db = np.array([float(t[2]) for t in terms])
    x = rng.standard_normal((n_seeds, T, D)) + dmu[reg]
    logit = (x * (W_SRC + dw[reg])).sum(-1) + B_SRC + db[reg]
    y = (rng.random((n_seeds, T)) < sigmoid(logit)).astype(np.int8)
    p = sigmoid(x @ W_SRC + B_SRC)
    act = (p >= TAU).astype(float)
    harm_by_regime = np.array(
        [0.0] + [max(population_effects(k, d)[3][-1], 0.0) for k, d in G3_KINDS[1:]]
    )
    return {
        "x": x.astype(np.float32),
        "y": y,
        "p": p,
        "loss": decision_cost(act, y),
        "brier": (p - y) ** 2,
        "world": World(kind="none", T=T),
        "regime": reg,
        "harm": harm_by_regime[reg],
        "harmful": reg == 1,
    }


# G4: financial-style decision regimes. Signal s_t is a weak AR(1) factor; the label is the sign of the next return
# (logistic noise: heavy-tailed, exactly calibrated for the source model p = sigmoid(s)).
G4_P = np.array(
    [
        [0.996, 0.002, 0.002],
        [0.004, 0.994, 0.002],
        [0.004, 0.002, 0.994],
    ]
)
G4_BETA = np.array([1.0, -0.7, 1.0])  # regime 1: signal reversal
G4_SIGMA = np.array(
    [1.0, 1.0, 1.6]
)  # regime 2: volatility increase (Brier +0.039, decision harm +0.079 < 0.10: benign)


def simulate_g4(n_seeds: int, seed: int, T: int = 2000, source_only: bool = False, transition=None):
    rng = np.random.default_rng(seed)
    P = G4_P if transition is None else np.asarray(transition)
    reg = np.zeros((n_seeds, T), dtype=np.int8)
    if not source_only:
        u = rng.random((n_seeds, T))
        cum = P.cumsum(1)
        for t in range(1, T):
            reg[:, t] = (u[:, t, None] > cum[reg[:, t - 1]]).sum(1)
    e = rng.standard_normal((n_seeds, T)) * 1.5
    sig = np.empty_like(e)
    sig[:, 0] = e[:, 0]
    for t in range(1, T):
        sig[:, t] = 0.6 * sig[:, t - 1] + np.sqrt(1 - 0.36) * e[:, t]
    logit = G4_BETA[reg] * sig / G4_SIGMA[reg]
    y = (rng.random((n_seeds, T)) < sigmoid(logit)).astype(np.int8)
    p = sigmoid(sig)
    act = (p >= TAU).astype(float)
    loss = decision_cost(act, y)
    out = {
        "x": sig[..., None].astype(np.float32),
        "y": y,
        "p": p,
        "loss": loss,
        "brier": (p - y) ** 2,
        "world": World(kind="none", T=T, family="G4"),
        "regime": reg,
    }
    if not source_only:
        src = simulate_g4(100, 998, T=2000, source_only=True)
        base = float(src["loss"].mean())
        by = np.zeros(3)
        for k in range(3):
            z = np.random.default_rng(997 + k)
            sg = z.standard_normal(400_000) * 1.5
            yy = (z.random(400_000) < sigmoid(G4_BETA[k] * sg / G4_SIGMA[k])).astype(np.int8)
            by[k] = decision_cost((sigmoid(sg) >= TAU).astype(float), yy).mean() - base
        out["harm_by_regime"] = by
        out["harm"] = np.maximum(by, 0.0)[reg]
        out["harmful"] = by[reg] >= HARM_THRESHOLD
    return out
