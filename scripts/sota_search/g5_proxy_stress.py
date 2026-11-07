"""Checkpoint B: corrected G5 proxy-defect benchmark (nominal risk from each condition's own source stream)."""

import sys

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

SEED0 = int(sys.argv[1]) if len(sys.argv) > 1 else 80000
OUT = sys.argv[2] if len(sys.argv) > 2 else "outputs/h2c_next/g5_dev.csv"
ARMS = {
    "C0_cost_parent": ("pp_cost_tight", {}),
    "C1_cost_disc": ("fix_cost", {"gamma": 0.995, "uniform_cap": True}),
    "C2_cost_ONS": ("pp_cost_guided", {"mode": "cost_ons"}),
    "C3_guided_ONS": ("pp_cost_guided", {"mode": "guided"}),
    "C4_H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
    "C7a_cost_SR": ("sr_cost_tight", {}),
    "C8_HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "C8_ONS_Brier": ("pp_ons", {}),
}
THR = float(np.log(20))
rows = []
i = 0
for cond in g.G5_CONDITIONS:
    nulls = g.simulate_g5(cond, "none", 400, SEED0 + 900 + len(rows))
    for shift in g.G5_SHIFTS:
        sim = g.simulate_g5(cond, shift, 400, SEED0 + i)
        i += 1
        T = sim["y"].shape[1]
        harmful = bool(sim["harmful"].any())
        role = "null" if shift == "none" else ("harm" if harmful else "benign")
        fh = 700 if harmful else T
        for frac in (0.10, 0.20):
            for arm, (name, extra) in ARMS.items():
                p = {"frac": frac, "delay": 5, "tol": 0.0, **extra}
                thr = det.THEORY_THRESHOLD.get(name)
                if thr is None:
                    thr = h.calibrate(name, p, nulls)
                al = det.first_cross(
                    np.nan_to_num(
                        det.DETECTORS[name](sim, lseed=SEED0 + 500 + i, **p), nan=-np.inf
                    ),
                    thr,
                )
                rows.append(
                    {
                        "cond": cond,
                        "shift": shift,
                        "role": role,
                        "harm": round(sim["harm_post"], 3),
                        "frac": frac,
                        "arm": arm,
                        "power": float(((al < T) & (al >= fh) & harmful).mean())
                        if harmful
                        else np.nan,
                        "alarm_rate_before_harm_or_any": float((al < fh).mean()),
                    }
                )
        print(cond, shift, role, flush=True)
df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
pd.set_option("display.width", 220)
for frac in (0.10, 0.20):
    d = df[df.frac == frac]
    s = d.groupby("arm", sort=False).apply(
        lambda x: pd.Series(
            {
                "harm_power": x[x.role == "harm"].power.mean(),
                "benign_fa": x[x.role == "benign"].alarm_rate_before_harm_or_any.mean(),
                "null_fa": x[x.role == "null"].alarm_rate_before_harm_or_any.mean(),
                "harm_fa_before": x[x.role == "harm"].alarm_rate_before_harm_or_any.mean(),
            }
        ),
        include_groups=False,
    )
    print(frac)
    print(s.round(3).to_string())
