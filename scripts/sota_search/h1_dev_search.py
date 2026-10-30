"""H1 development search: decision-gated ONS vs ONS / HG / discounting (dev seeds 40000+, G3 dev stream 41000)."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

THR = float(np.log(20))
BASE = {
    "parent": ("pprm_tight", {}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "disc_only": ("fix_brier", {"gamma": 0.99, "uniform_cap": True}),
    "ONS": ("pp_ons", {}),
}
H1 = {}
for w in (50, 100, 200):
    H1[f"hard_w{w}"] = ("pp_ons_gated", {"gate": "hard", "w": w})
for a in (0.5, 1.0, 2.0):
    for b in (0.0, -1.0):
        H1[f"soft_a{a}_b{b}"] = ("pp_ons_gated", {"gate": "soft", "a": a, "b": b, "w": 100})
for k in (1.0, 2.0, 4.0):
    H1[f"unc_k{k}"] = ("pp_ons_gated", {"gate": "unc", "k": k, "w": 100})
H1["multi_30_200"] = ("pp_ons_gated", {"gate": "multi", "w_short": 30, "w_long": 200})
ARMS = {**BASE, **H1}


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
        print(rows[-1], flush=True)
df = pd.DataFrame(rows)
df.to_csv("outputs/hg_v2/h1_dev_search.csv", index=False)
