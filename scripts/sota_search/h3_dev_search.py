"""H3 development: predictable-baseline ONS vs ONS/HG under AR(1) covariates (null) and on the dev worlds (power)."""

import json
import sys

import numpy as np

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

sys.path.insert(0, "scripts/sota_search")
THR = float(np.log(20))
ARMS = {
    "parent": ("pprm_tight", {}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "ONS": ("pp_ons", {}),
    "base_g999": ("pp_ons_baseline", {"gamma_b": 0.999}),
    "base_g995": ("pp_ons_baseline", {"gamma_b": 0.995}),
    "base_g99": ("pp_ons_baseline", {"gamma_b": 0.99}),
}


def ar_sim(rho, n=300, T=2000, seed=0):
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((n, T, g.D))
    x = np.empty_like(e)
    x[:, 0] = e[:, 0]
    for t in range(1, T):
        x[:, t] = rho * x[:, t - 1] + np.sqrt(1 - rho**2) * e[:, t]
    y = (rng.random((n, T)) < g.sigmoid(x @ g.W_SRC + g.B_SRC)).astype(np.int8)
    p = g.sigmoid(x @ g.W_SRC + g.B_SRC)
    act = (p >= g.TAU).astype(float)
    return {
        "x": x.astype(np.float32),
        "y": y,
        "p": p,
        "loss": g.decision_cost(act, y),
        "brier": (p - y) ** 2,
        "world": g.World(kind="none", T=T),
    }


out = {"null_fa": {}, "power": {}}
for rho in (0.0, 0.9, 0.98):
    sim = ar_sim(rho, seed=47000 + int(rho * 100))
    for frac in (0.10, 0.20):
        for arm, (name, extra) in ARMS.items():
            st = det.DETECTORS[name](sim, lseed=48000, frac=frac, delay=5, tol=0.0, **extra)
            out["null_fa"][f"rho{rho}/{frac}/{arm}"] = float(
                (det.first_cross(np.nan_to_num(st, nan=-np.inf), THR) < 2000).mean()
            )
worlds = h.dev_pool()
sims = [g.simulate(w, 200, 40000 + i) for i, w in enumerate(worlds)]
for frac in (0.10, 0.20):
    for arm, (name, extra) in ARMS.items():
        pw, ben = [], []
        for i, (w, sim) in enumerate(zip(worlds, sims, strict=True)):
            m, _ = h.evaluate(
                name, {"frac": frac, "delay": 5, "tol": 0.0, **extra}, w, sim, THR, lseed=45000 + i
            )
            r = h.role(w)
            if r == "harm":
                pw.append(m["detect_prob"])
            elif r == "benign":
                ben.append(m["false_alarm_prob"])
        out["power"][f"{frac}/{arm}"] = [float(np.mean(pw)), float(np.mean(ben))]
with open("outputs/hg_v2/h3_dev_search.json", "w") as fh:
    json.dump(out, fh, indent=2)
for rho in (0.0, 0.9, 0.98):
    for frac in (0.10, 0.20):
        print(
            "null FA rho",
            rho,
            frac,
            {a: round(out["null_fa"][f"rho{rho}/{frac}/{a}"], 3) for a in ARMS},
        )
for frac in (0.10, 0.20):
    print(
        "dev power/benign FA",
        frac,
        {a: [round(v, 3) for v in out["power"][f"{frac}/{a}"]] for a in ARMS},
    )
