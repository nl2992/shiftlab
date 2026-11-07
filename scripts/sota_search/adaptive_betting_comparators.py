"""Goal 4 (partial): adaptive-betting comparators on the exposed G1/G2 held-out pools (exploratory, configs fixed a priori)."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

ARMS = {
    "parent": ("pprm_tight", {}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "mixture8": ("pp_mixture", {}),
    "ons": ("pp_ons", {}),
    "pprm_unifcap": ("pprm_tight", {"uniform_cap": True}),
    "disc_only_unifcap": ("fix_brier", {"gamma": 0.99, "uniform_cap": True}),
}
THR = float(np.log(20))
rows = []
for fam, (worlds, sb, lb) in {
    "G1": (h.heldout_pool(), 5000, 5500),
    "G2": (h.heldout_g2_pool(), 7000, 7500),
}.items():
    for i, w in enumerate(worlds):
        sim = g.simulate(w, 400, sb + i)
        for frac in (0.10, 0.20):
            for arm, (name, extra) in ARMS.items():
                m, rt = h.evaluate(
                    name, {"frac": frac, "delay": 5, "tol": 0.0, **extra}, w, sim, THR, lseed=lb + i
                )
                rows.append(
                    {
                        "family": fam,
                        "frac": frac,
                        "arm": arm,
                        "world": w.key(),
                        "role": h.role(w),
                        "power": m["detect_prob"],
                        "fa": m["false_alarm_prob"],
                        "harm_before": m["mean_harm_before_alarm"],
                        "runtime_s": rt,
                    }
                )
df = pd.DataFrame(rows)
df.to_csv("outputs/hg_validation/04_ADAPTIVE_BETTING_COMPARATORS.csv", index=False)
t = (
    df.groupby(["family", "frac", "arm", "role"], sort=False)[["power", "fa"]]
    .mean()
    .unstack("role")
    .round(3)
)
print(t.to_string())
print(df.groupby("arm").runtime_s.mean().round(2).to_string())
