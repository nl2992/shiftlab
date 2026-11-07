"""H1 matched-benign-FA frontier on the v2 development worlds (thresholds swept; empirical operating points)."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

ARMS = {
    "parent": ("pprm_tight", {}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "disc_only": ("fix_brier", {"gamma": 0.99, "uniform_cap": True}),
    "ONS": ("pp_ons", {}),
    "gONS_hard200": ("pp_ons_gated", {"gate": "hard", "w": 200}),
    "gONS_unc2": ("pp_ons_gated", {"gate": "unc", "k": 2.0, "w": 100}),
    "gONS_soft2": ("pp_ons_gated", {"gate": "soft", "a": 2.0, "b": 0.0, "w": 100}),
    "gONS_soft1b-1": ("pp_ons_gated", {"gate": "soft", "a": 1.0, "b": -1.0, "w": 100}),
    "gONS_multi": ("pp_ons_gated", {"gate": "multi", "w_short": 30, "w_long": 200}),
}
THRS = np.log(np.array([2, 3, 5, 8, 12, 20, 35, 60, 100, 200, 500.0]))
worlds = h.dev_pool()
sims = [g.simulate(w, 200, 40000 + i) for i, w in enumerate(worlds)]
rows = []
for frac in (0.10, 0.20):
    for arm, (name, extra) in ARMS.items():
        for i, (w, sim) in enumerate(zip(worlds, sims, strict=True)):
            st = det.DETECTORS[name](sim, lseed=45000 + i, frac=frac, delay=5, tol=0.0, **extra)
            st = np.where(np.isfinite(st), st, -np.inf)
            for thr in THRS:
                m = h.score(det.first_cross(st, thr), w, frac)
                rows.append(
                    {
                        "frac": frac,
                        "arm": arm,
                        "thr": float(np.exp(thr)),
                        "role": h.role(w),
                        "power": m["detect_prob"],
                        "fa": m["false_alarm_prob"],
                    }
                )
df = pd.DataFrame(rows)
f = df.groupby(["frac", "arm", "thr", "role"])[["power", "fa"]].mean().unstack("role")
f.columns = ["pow_ben", "pow_harm", "pow_null", "fa_ben", "fa_harm", "fa_null"]
f = f.reset_index()[["frac", "arm", "thr", "pow_harm", "fa_ben", "fa_null"]]
f.to_csv("outputs/hg_v2/h1_frontier_dev.csv", index=False)
for frac in (0.10, 0.20):
    for cap in (0.02, 0.05, 0.08):
        best = {}
        for arm, grp in f[f.frac == frac].groupby("arm"):
            ok = grp[(grp.fa_ben <= cap) & (grp.fa_null <= 0.07)]
            best[arm] = round(float(ok.pow_harm.max()), 3) if len(ok) else None
        print(frac, cap, best)
