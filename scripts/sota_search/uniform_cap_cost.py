"""Development-pool power cost of the context-free (uniform) bet cap; exploratory, not a confirmation."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

THR = float(np.log(20))
ARMS = {
    "pprm_tight": ("pprm_tight", {}),
    "pprm_tight_unifcap": ("pprm_tight", {"uniform_cap": True}),
    "HG": ("fix_brier", {"gamma": 0.99, "gate_w": 100}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
}
worlds = h.dev_pool()
sims = [g.simulate(w, 200, 1000 + i) for i, w in enumerate(worlds)]
rows = []
for frac in (0.10, 0.20):
    for arm, (name, extra) in ARMS.items():
        for i, (w, sim) in enumerate(zip(worlds, sims, strict=True)):
            m, _ = h.evaluate(
                name, {"frac": frac, "delay": 5, "tol": 0.0, **extra}, w, sim, THR, lseed=500 + i
            )
            rows.append(
                {
                    "frac": frac,
                    "arm": arm,
                    "world": w.key(),
                    "role": h.role(w),
                    "power": m["detect_prob"],
                    "fa": m["false_alarm_prob"],
                }
            )
df = pd.DataFrame(rows)
df.to_csv("outputs/hg_validation/uniform_cap_dev.csv", index=False)
t = df.groupby(["frac", "arm", "role"], sort=False)[["power", "fa"]].mean().unstack("role").round(3)
print(t.to_string())
