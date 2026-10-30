"""Null false alarm when the deployed model is increasingly misspecified (no shift); partial G5."""

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
out = {}
for k in (1.0, 3.0, 6.0):
    rng = np.random.default_rng(40000 + int(k))
    n, T = 400, 2000
    x = rng.standard_normal((n, T, g.D))
    y = (rng.random((n, T)) < g.sigmoid(x @ g.W_SRC + k * g.nonlinear_term(x))).astype(np.int8)
    p = g.sigmoid(x @ g.W_SRC)
    act = (p >= g.TAU).astype(float)
    # nominal risks are the G1 values, so a misspecified model starts above them: the null is "no CHANGE", which is
    # then violated; we therefore report the false-alarm rate against the G1 nominal and flag it as a misspecification test
    sim = {
        "x": x.astype(np.float32),
        "y": y,
        "p": p,
        "loss": g.decision_cost(act, y),
        "brier": (p - y) ** 2,
        "world": g.World(kind="none", T=T),
    }
    for frac in (0.10, 0.20):
        for arm, (name, extra) in ARMS.items():
            st = det.DETECTORS[name](sim, lseed=41000, frac=frac, delay=5, tol=0.0, **extra)
            out[f"k{k}/{frac}/{arm}"] = float(
                (det.first_cross(np.nan_to_num(st, nan=-np.inf), THR) < T).mean()
            )
            print(
                k,
                frac,
                arm,
                round(out[f"k{k}/{frac}/{arm}"], 3),
                "brier",
                round(float(sim["brier"].mean()), 3),
                flush=True,
            )
with open("outputs/hg_validation/07_PROXY_MISSPEC.json", "w") as fh:
    json.dump(out, fh, indent=2)
