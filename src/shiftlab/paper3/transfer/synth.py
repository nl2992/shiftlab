"""Synthetic paired-loss stream families (training augmentation + synthetic held-out folds).

Evaluator-side truth (the latent p_t path) is generated here and discarded; only (l0, l1, delay)
leave this module, so selectors cannot see it. On a disagreement event exactly one model is wrong;
p_t = P(challenger correct | disagreement). Families differ in how p_t evolves and in outcome
dependence, which is what moves the best (lambda, gamma, H).
"""

from __future__ import annotations

import numpy as np

FAMILIES = ("S1_static", "S2_markov_regime", "S3_ar_drift", "S4_ramp", "S5_sticky_outcomes")
DELAYS = (24, 50, 100, 144)


def _p_path(fam: str, T: int, rng) -> np.ndarray:
    if fam == "S1_static":
        return np.full(T, rng.choice([0.3, 0.4, 0.6, 0.7, 0.8]) + rng.normal(0, 0.03))
    if fam == "S2_markov_regime":
        dwell = rng.uniform(250, 900)
        lo, hi = rng.uniform(0.2, 0.4), rng.uniform(0.6, 0.85)
        s = rng.integers(2)
        p = np.empty(T)
        for t in range(T):
            if rng.random() < 1.0 / dwell:
                s = 1 - s
            p[t] = hi if s else lo
        return p
    if fam == "S3_ar_drift":
        rho, sd = rng.uniform(0.995, 0.9995), rng.uniform(0.04, 0.12)
        x = rng.normal(0, 1.0) * 0.5
        out = np.empty(T)
        for t in range(T):
            x = rho * x + sd * rng.normal()
            out[t] = x
        return 1.0 / (1.0 + np.exp(-(out * 3.0 + rng.normal(0, 0.5))))
    if fam == "S4_ramp":
        a, b = rng.uniform(0.2, 0.5), rng.uniform(0.55, 0.9)
        return np.linspace(a, b, T) if rng.random() < 0.5 else np.linspace(b, a, T)
    if fam == "S5_sticky_outcomes":
        return _p_path("S2_markov_regime", T, rng)
    raise KeyError(fam)


def make_stream(fam: str, seed: int, K: int = 40, T: int = 2000):
    """Returns (l0, l1, delay) for one synthetic stream of K episodes."""
    rng = np.random.default_rng(np.random.SeedSequence([777, seed, FAMILIES.index(fam)]))
    delay = int(rng.choice(DELAYS))
    r = rng.uniform(0.04, 0.45)
    base_err = rng.uniform(0.05, 0.3)
    stick = rng.uniform(0.3, 0.9) if fam == "S5_sticky_outcomes" else 0.0
    l0 = np.zeros((K, T), dtype=np.int8)
    l1 = np.zeros((K, T), dtype=np.int8)
    for e in range(K):
        p = np.clip(_p_path(fam, T, rng), 0.02, 0.98)
        dis = rng.random(T) < np.clip(r * rng.uniform(0.7, 1.3), 0.01, 0.9)
        both = rng.random(T) < base_err
        u = rng.random(T)
        chal = np.empty(T, dtype=bool)  # challenger correct on disagreement
        prev = rng.random() < 0.5
        for t in range(T):
            if stick > 0 and rng.random() < stick:
                chal[t] = prev
            else:
                chal[t] = u[t] < p[t]
            if dis[t]:
                prev = chal[t]
        a0 = np.where(
            dis, chal.astype(np.int8), both.astype(np.int8)
        )  # incumbent wrong iff chal correct
        a1 = np.where(dis, (~chal).astype(np.int8), both.astype(np.int8))
        l0[e], l1[e] = a0, a1
    return l0, l1, delay
