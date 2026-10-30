"""Null false alarm under temporally dependent covariates (AR(1), stationary N(0,1) marginal; no shift)."""

import json

import numpy as np

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

THR = float(np.log(20))
ARMS = {
    "parent": ("pprm_tight", {}),
    "HG_ctxcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "ONS": ("pp_ons", {}),
}


def ar_sim(rho, n=400, T=2000, seed=0, family="G1"):
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((n, T, g.D))
    x = np.empty_like(e)
    x[:, 0] = e[:, 0]
    for t in range(1, T):
        x[:, t] = rho * x[:, t - 1] + np.sqrt(1 - rho**2) * e[:, t]
    logit = x @ g.W_SRC + g.B_SRC
    if family == "G2":
        logit = logit + g.nonlinear_term(x)
    y = (rng.random((n, T)) < g.sigmoid(logit)).astype(np.int8)
    p = g.sigmoid(x @ g.W_SRC + g.B_SRC)
    act = (p >= g.TAU).astype(float)
    return {
        "x": x.astype(np.float32),
        "y": y,
        "p": p,
        "loss": g.decision_cost(act, y),
        "brier": (p - y) ** 2,
        "world": g.World(kind="none", T=T, family=family),
    }


out = {}
for family in ("G1", "G2"):
    for rho in (0.0, 0.9, 0.98):
        sim = ar_sim(rho, seed=30000 + int(rho * 100), family=family)
        for frac in (0.10, 0.20):
            for arm, (name, extra) in ARMS.items():
                st = det.DETECTORS[name](sim, lseed=31000, frac=frac, delay=5, tol=0.0, **extra)
                fa = float(
                    (
                        det.first_cross(np.nan_to_num(st, nan=-np.inf), THR) < sim["y"].shape[1]
                    ).mean()
                )
                out[f"{family}/rho{rho}/{frac}/{arm}"] = fa
                print(family, rho, frac, arm, round(fa, 3), flush=True)
json.dump(out, open("outputs/hg_validation/06_DEPENDENCE_NULL.json", "w"), indent=2)
