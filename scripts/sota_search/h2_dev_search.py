"""H2 development search: cost-null e-processes with Brier-guided bets (same dev seeds as H1)."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

THR = float(np.log(20))
ARMS = {
    "cost_tight(parent)": ("pp_cost_tight", {}),
    "cost_DK": ("fix_cost", {"gamma": 0.995, "uniform_cap": True}),
    "H2a_cost_ONS": ("pp_cost_guided", {"mode": "cost_ons"}),
    "H2b_guided_ONS": ("pp_cost_guided", {"mode": "guided"}),
    "H2c_guided_disc.99": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.99}),
    "H2c_guided_disc.995": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
    "HG_unifcap(ref,Brier)": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "ONS(ref,Brier)": ("pp_ons", {}),
}


def g3_score(sim, al):
    T = sim["y"].shape[1]
    fh = np.where(sim["harmful"].any(1), sim["harmful"].argmax(1), T)
    hp = fh < T
    return float(((al < T) & (al >= fh) & hp).sum() / hp.sum()), float((al < fh).mean())


worlds = h.dev_pool()
sims = [g.simulate(w, 200, 40000 + i) for i, w in enumerate(worlds)]
g3 = g.simulate_g3(500, 41000)
rows = []
for frac in (0.10, 0.20):
    for arm, (name, extra) in ARMS.items():
        p = {"frac": frac, "delay": 5, "tol": 0.0, **extra}
        per = {"harm": [], "benign": [], "null": []}
        for i, (w, sim) in enumerate(zip(worlds, sims, strict=True)):
            m, _ = h.evaluate(name, p, w, sim, THR, lseed=45000 + i)
            role = h.role(w)
            per[role].append(m["detect_prob"] if role == "harm" else m["false_alarm_prob"])
        al = det.first_cross(
            np.nan_to_num(det.DETECTORS[name](g3, lseed=46000, **p), nan=-np.inf), THR
        )
        gp, gfa = g3_score(g3, al)
        rows.append(
            {
                "frac": frac,
                "arm": arm,
                "dev_harm_power": np.mean(per["harm"]),
                "dev_benign_fa": np.mean(per["benign"]),
                "dev_null_fa": np.mean(per["null"]),
                "g3dev_power": gp,
                "g3dev_fa": gfa,
            }
        )
pd.DataFrame(rows).to_csv("outputs/hg_v2/h2_dev_search.csv", index=False)
pd.set_option("display.width", 200)
print(pd.DataFrame(rows).round(3).to_string(index=False))
