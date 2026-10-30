"""G6: cost-null e-processes with per-event label release times and hard query budgets (checkpoint B)."""

import numpy as np

from . import detectors as det
from . import generators as g


def delays_for(sim, kind, base=5, seed=0):
    S, T = sim["y"].shape
    rng = np.random.default_rng(seed)
    if kind == "fixed":
        return np.full((S, T), base)
    if kind == "random":  # independent of everything
        return base + rng.integers(0, 21, (S, T))
    if (
        kind == "late_if_good"
    ):  # zero-cost outcomes resolve late (selection toward high cost among released labels)
        return base + 30 * (sim["loss"] == 0)
    if kind == "late_if_bad":  # costly outcomes resolve late
        return base + 30 * (sim["loss"] > 0)
    raise ValueError(kind)


def _released(a, release, T):
    """Sum of ``a`` over events whose release time equals t, as an (S, T) array."""
    out = np.zeros((a.shape[0], T + 1))
    rows = np.repeat(np.arange(a.shape[0])[:, None], a.shape[1], 1)
    np.add.at(out, (rows, np.minimum(release, T)), a)
    return out[:, :T]


def cost_eprocess(
    sim, frac, lseed, delays, mode="pooled", gamma=0.995, budget=None, budget_rule="stop", cap=0.5
):
    """Cost-null PP e-process with arbitrary release times. mode: pooled | disc | h2c."""
    S, T = sim["y"].shape
    mask = det.label_mask(sim, frac, lseed)
    exhausted = np.full(S, T)
    if budget is not None:  # queries are charged when issued; later queries are not made
        cum = np.cumsum(mask, 1)
        mask = mask & (cum <= budget)
        hit = cum > budget
        exhausted = np.where(hit.any(1), hit.argmax(1), T)
    qm = mask.astype(float)
    xc, _q, _l, bc = det._pp_parts(sim, frac, lseed, "cost", None, qm, 0.0, uniform_cap=True)
    xb, _q2, _l2, bb = det._pp_parts(sim, frac, lseed, "brier", None, qm, 0.0, uniform_cap=True)
    release = np.arange(T)[None, :] + delays
    g_ = 1.0 if mode == "pooled" else gamma

    def moments(x):
        ones = np.ones_like(x)
        n = det.shift_time(det._ewm_cumsum(_released(ones, release, T), g_), 1)
        m1 = det.shift_time(det._ewm_cumsum(_released(x, release, T), g_), 1) / (n + 1)
        m2 = det.shift_time(det._ewm_cumsum(_released(x**2, release, T), g_), 1) / (n + 1)
        return m1, m2

    hic, hib = cap / bc, cap / bb
    if mode == "h2c":
        m1, m2 = moments(xb)
        lam = (
            np.minimum(np.where(m2 > 0, np.maximum(m1, 0) / np.maximum(m2, 1e-12), 0.0), hib)
            / hib
            * hic
        )
    else:
        m1, m2 = moments(xc)
        lam = np.minimum(np.where(m2 > 0, np.maximum(m1, 0) / np.maximum(m2, 1e-12), 0.0), hic)
    if budget is not None and budget_rule == "stop":
        lam = lam * (np.arange(T)[None, :] < exhausted[:, None])
    return np.cumsum(_released(np.log1p(lam * xc), release, T), 1)


def null_and_power(frac, kind, mode, n=400, seed=60000, budget=None, rule="stop", gamma=0.995):
    thr = float(np.log(20))
    out = {}
    for tag, w in (
        ("null", g.World(kind="none")),
        ("harm", g.World(kind="concept", delta=2.0, shape="abrupt", t0=700)),
    ):
        sim = g.simulate(w, n, seed + (0 if tag == "null" else 1))
        d = delays_for(sim, kind, seed=seed + 7)
        st = cost_eprocess(
            sim, frac, seed + 9, d, mode=mode, gamma=gamma, budget=budget, budget_rule=rule
        )
        al = det.first_cross(st, thr)
        T = w.T
        out[tag] = (
            float((al < T).mean()) if tag == "null" else float(((al < T) & (al >= 700)).mean())
        )
    return out
