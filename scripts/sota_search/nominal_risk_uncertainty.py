"""H2c with an estimated nominal cost: Hoeffding upper bound from an independent calibration sample (docs/h2c_restart/NOMINAL_RISK_UNCERTAINTY.md)."""

import json

import numpy as np

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

ALPHA_CAL, ALPHA_TEST, B = 0.01, 0.04, 5.0  # total error budget .05; cost range [0, 5]
THR = float(np.log(1 / ALPHA_TEST))
worlds = {
    "null": g.World(kind="none"),
    "abrupt_d2": g.World(kind="concept", delta=2.0, shape="abrupt", t0=700),
    "abrupt_d1.5": g.World(kind="concept", delta=1.5, shape="abrupt", t0=700),
}
true_c0 = det.source_moments("G1")["loss"][0]
out = {"true_c0": true_c0}
for bound_kind, ncal in [("known", 0)] + [
    (b_, n_) for b_ in ("hoeffding", "empirical_bernstein") for n_ in (300, 1000, 5000, 50000)
]:
    for frac in (0.10, 0.20):
        res = {}
        for label, w in worlds.items():
            sim = g.simulate(w, 400, 120000)
            if ncal:
                cal = g.simulate(g.World(kind="none", T=ncal), 1, 130000 + ncal)["loss"].ravel()
                if bound_kind == "hoeffding":
                    u0 = float(cal.mean() + B * np.sqrt(np.log(1 / ALPHA_CAL) / (2 * ncal)))
                else:  # Maurer-Pontil empirical Bernstein, one-sided
                    lg = np.log(1 / ALPHA_CAL)
                    u0 = float(
                        cal.mean()
                        + np.sqrt(2 * cal.var(ddof=1) * lg / ncal)
                        + 7 * B * lg / (3 * (ncal - 1))
                    )
            else:
                u0 = true_c0  # known-nominal reference
            sim["r0_cost"] = u0
            st = det.pp_cost_guided(
                sim, frac=frac, delay=5, lseed=121000, mode="guided_disc", gamma=0.995
            )
            al = det.first_cross(st, THR)
            fh = 700 if w.kind != "none" else 2000
            res[label] = (
                float(((al < 2000) & (al >= fh)).mean())
                if w.kind != "none"
                else float((al < 2000).mean())
            )
        res["u0"] = u0
        out[f"{bound_kind}/ncal{ncal}/{frac}"] = res
        print(bound_kind, ncal, frac, {k: round(v, 3) for k, v in res.items()}, flush=True)
with open("outputs/h2c_restart/nominal_risk_uncertainty.json", "w") as fh_:
    json.dump(out, fh_, indent=2)
