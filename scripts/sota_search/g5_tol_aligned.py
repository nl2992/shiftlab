"""Tolerance-aligned cost null: H0 = cost increase <= eps (eps = 0.10 = the harm threshold). Fresh development seeds 140000+."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

EPS = 0.10
THR = float(np.log(20))
ARMS = {
    "C0_cost_parent": ("pp_cost_tight", {}),
    "C1_cost_disc": ("fix_cost", {"gamma": 0.995, "uniform_cap": True}),
    "C2_cost_ONS": ("pp_cost_guided", {"mode": "cost_ons"}),
    "C3_guided_ONS": ("pp_cost_guided", {"mode": "guided"}),
    "C4_H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
}
rows, k = [], 0
for cond in g.G5_CONDITIONS:
    for shift in g.G5_SHIFTS:
        if shift == "none":
            continue
        sim = g.simulate_g5(cond, shift, 400, 140000 + k)
        k += 1
        harm = g.g5_effects(cond, shift)[2]
        T = sim["y"].shape[1]
        for frac in (0.10, 0.20):
            for arm, (name, extra) in ARMS.items():
                al = det.first_cross(
                    det.DETECTORS[name](
                        sim, frac=frac, delay=5, lseed=145000 + k, tol=EPS, **extra
                    ),
                    THR,
                )
                post = (al < T) & (al >= 700)
                pre = al < 700
                rows.append(
                    {
                        "cond": cond,
                        "shift": shift,
                        "harm": harm,
                        "frac": frac,
                        "arm": arm,
                        "alarm_post": float(post.mean()),
                        "alarm_pre": float(pre.mean()),
                    }
                )
    print(cond, flush=True)
df = pd.DataFrame(rows)
df.to_csv("outputs/icml_sprint/g5_tol_aligned.csv", index=False)
df["cls"] = np.where(df.harm <= 0, "harm<=0", np.where(df.harm <= EPS, "0<harm<=eps", "harm>eps"))
pd.set_option("display.width", 200)
print(df.groupby(["frac", "cls", "arm"]).alarm_post.mean().unstack("arm").round(3).to_string())
print(
    df[df.cls == "harm>eps"]
    .groupby(["frac", "arm"])
    .alarm_post.mean()
    .unstack(0)
    .round(3)
    .to_string()
)
print(df[df.cls == "harm>eps"][["cond", "shift", "harm"]].drop_duplicates().to_string(index=False))
