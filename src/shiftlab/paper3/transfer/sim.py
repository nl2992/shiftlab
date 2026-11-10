"""Vectorised Wald/LCB economic switcher + paced acquisition + late-label cutoff.

Port (see 03D_TRANSFER_DESIGN.md Sec. 8) of research/paper1-eqsdp-foundation-2026-11-08@5bda4e73
scripts/qsg_methods_search/{eqs_d,hurdles}.py, scripts/paper1_eqsdp/stage1_policies.py
(Stage1WaldStop) and scripts/promising_directions/sota/{simulator,competitors/controls}.py.
Runs E episodes x C configurations at once with common random numbers across configurations.
The policy sees: disagreement indicator, released paired outcomes of its own purchases, remaining
budget, delay, costs, horizon. Nothing else.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm

LAMS = (0.85, 0.90, 0.95, 0.97, 0.98, 0.99)
GAMS = (0.10, 0.20, 0.30, 0.45)
HS = (0, 500, 900, 1100, 1300, 1500)
GRID = np.array(list(itertools.product(LAMS, GAMS, HS)), dtype=float)  # (144, 3)
NCFG = len(GRID)
REF_CFG = int(np.where((GRID == (0.97, 0.20, 0)).all(1))[0][0])  # Paper 1 wald_l0.97_g0.2 reference
P_MIN, PRIOR_RATE, PRIOR_W = 0.05, 0.25, 20.0


@dataclass(frozen=True)
class Costs:
    T: int = 2000
    B: int = 200
    cq: float = 0.05
    cs: float = 5.0


PRIMARY = Costs()
SHIFTED = Costs(cq=0.15, cs=15.0)
SCENARIOS = {"primary": PRIMARY, "shifted": SHIFTED}


def simulate(
    l0, l1, delay, costs: Costs = PRIMARY, grid=GRID, seed: int = 0, log_cfg: int | None = None
):
    """Return dict of (E, C) arrays: J, loss, labels, switches. If ``log_cfg`` is given also
    ``rel`` (E, T) int8 in {-1,0,1}: released paired outcome D = l0 - l1 of the log_cfg policy at
    its release time (0 = nothing released), and ``req`` (E, T) bool purchase indicator."""
    l0 = np.asarray(l0, dtype=np.int8)
    l1 = np.asarray(l1, dtype=np.int8)
    E, T = l0.shape
    assert T == costs.T and delay >= 1
    C = len(grid)
    lam = grid[:, 0][None, :]
    gam = grid[:, 1]
    H = grid[:, 2][None, :]
    zlo = norm.ppf(gam)[None, :]  # quantile at gamma
    zhi = norm.ppf(1.0 - gam)[None, :]
    rng = np.random.default_rng(np.random.SeedSequence([20261109, seed, E, T]))
    U = rng.random((E, T))
    dis = l0 != l1
    D = l0.astype(np.int8) - l1.astype(np.int8)
    n = np.zeros((E, C))
    k = np.zeros((E, C))
    dep = np.zeros((E, C), dtype=np.int8)
    rem = np.full((E, C), costs.B, dtype=np.int64)
    loss = np.zeros((E, C))
    sw = np.zeros((E, C))
    lab = np.zeros((E, C))
    nd = np.zeros(E)
    reqmat = np.zeros((T, E, C), dtype=bool)
    rel = np.zeros((E, T), dtype=np.int8) if log_cfg is not None else None
    cut_ok_t = (np.arange(T)[:, None] + delay) <= (T - H)  # (T, C) purchase allowed
    cs = costs.cs
    for t in range(T):
        s = t - delay
        if s >= 0:
            r = reqmat[s]  # (E, C) labels released now
            if r.any():
                d = D[:, s][:, None]
                pos = (d > 0).astype(float)
                n = np.where(r, lam * n + 1.0, n)
                k = np.where(r, lam * k + pos, k)
                p = (k + 0.5) / (n + 1.0)
                se = np.sqrt(p * (1.0 - p) / (n + 1.0))
                rate = ((nd + PRIOR_RATE * PRIOR_W) / (t + PRIOR_W))[:, None]
                q = np.where(dep == 0, p + zlo * se, p + zhi * se)
                q = np.clip(q, 0.0, 1.0)
                adv = np.where(dep == 0, 2.0 * q - 1.0, 1.0 - 2.0 * q)
                flip = r & (adv * rate * (T - t) > cs)
                dep = np.where(flip, 1 - dep, dep)
                if rel is not None:
                    rel[:, t] = np.where(r[:, log_cfg], D[:, s], 0)
        # deploy: switch counted when deployment changed during release
        if t == 0:
            prev = np.zeros((E, C), dtype=np.int8)
        sw += dep != prev
        prev = dep
        loss += np.where(dep == 0, l0[:, t][:, None], l1[:, t][:, None])
        # acquire
        dt = dis[:, t]
        if dt.any():
            rate_a = (nd + PRIOR_RATE * PRIOR_W) / (t + PRIOR_W)
            exp_left = np.maximum(rate_a * (T - t), 1e-9)[:, None]
            qa = np.clip(rem / exp_left, P_MIN, 1.0)
            take = dt[:, None] & (rem > 0) & (U[:, t][:, None] < qa) & cut_ok_t[t][None, :]
            rem = rem - take
            lab += take
            reqmat[t] = take
        nd += dt
    out = {
        "J": loss + costs.cq * lab + cs * sw,
        "loss": loss,
        "labels": lab,
        "switches": sw,
    }
    if log_cfg is not None:
        out["rel"] = rel
        out["req"] = reqmat[:, :, log_cfg].T.copy()
    return out


def never_switch_J(l0):
    return np.asarray(l0, dtype=float).sum(1)
