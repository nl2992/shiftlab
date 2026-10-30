"""Checkpoints A and C: cost-null comparators and H2c ablations on fresh development seeds (exploratory for G4)."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

THR = float(np.log(20))
ARMS = {
    "C0_cost_parent": ("pp_cost_tight", {}),
    "C1_cost_disc.995": ("fix_cost", {"gamma": 0.995, "uniform_cap": True}),
    "C2_cost_ONS": ("pp_cost_guided", {"mode": "cost_ons"}),
    "C3_guided_ONS": ("pp_cost_guided", {"mode": "guided"}),
    "C4_H2c_.995": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
    "C5_cost_mixture8": ("pp_mixture", {"risk": "cost"}),
    "C6a_multi_cost": ("pp_cost_multi", {"guided": False}),
    "C6b_multi_guided": ("pp_cost_multi", {"guided": True}),
    "C7a_cost_SR": ("sr_cost_tight", {}),
    "C7b_PR_CS": ("pr_cs", {}),
    "A_guided_pooled": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 1.0}),
    "A_guided_.99": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.99}),
    "A_guided_.999": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.999}),
    "C8_HG_unifcap(Brier)": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "C8_ONS(Brier)": ("pp_ons", {}),
}
worlds = h.dev_pool()
dev = [(f"dev/{w.key()}", w, g.simulate(w, 200, 70000 + i)) for i, w in enumerate(worlds)]
g3 = g.simulate_g3(500, 72000)
g4 = g.simulate_g4(500, 71000)
null_g1 = g.simulate(g.World(kind="none"), 400, 9000)
null_g4 = g.simulate_g4(400, 73000, transition=np.eye(3))
rows = []


def thr_for(name, p, family):
    if name in det.THEORY_THRESHOLD:
        return det.THEORY_THRESHOLD[name]
    return h.calibrate(name, p, null_g4 if family == "G4" else null_g1)


def per_seed(al, T, fh, has_harm):
    return ((al < T) & (al >= fh) & has_harm), (al < fh)


for frac in (0.10, 0.20):
    for arm, (name, extra) in ARMS.items():
        p = {"frac": frac, "delay": 5, "tol": 0.0, **extra}
        for label, w, sim in dev:
            thr = thr_for(name, p, "G1")
            al = det.first_cross(
                np.nan_to_num(det.DETECTORS[name](sim, lseed=75000, **p), nan=-np.inf), thr
            )
            tr = g.truth(w)
            T = w.T
            fh = int(tr["harmful"].argmax()) if tr["harmful"].any() else T
            d, f = per_seed(al, T, fh, bool(tr["harmful"].any()))
            for s in range(len(al)):
                rows.append((frac, arm, label, h.role(w), s, bool(d[s]), bool(f[s])))
        for label, sim, family in (("G3dev", g3, "G1"), ("G4dev", g4, "G4")):
            thr = thr_for(name, p, family)
            al = det.first_cross(
                np.nan_to_num(det.DETECTORS[name](sim, lseed=76000, **p), nan=-np.inf), thr
            )
            T = sim["y"].shape[1]
            fh = np.where(sim["harmful"].any(1), sim["harmful"].argmax(1), T)
            d, f = per_seed(al, T, fh, fh < T)
            for s in range(len(al)):
                rows.append((frac, arm, label, "regime", s, bool(d[s]), bool(f[s])))
        print(frac, arm, flush=True)
df = pd.DataFrame(
    rows, columns=["frac", "arm", "source", "role", "seed", "detected", "false_alarm"]
)
df.to_parquet("outputs/h2c_next/dev_per_seed.parquet")
rows = []
for (frac, arm), d in df.groupby(["frac", "arm"], sort=False):
    harm = d[d.role == "harm"].groupby("source").detected.mean().mean()
    ben = d[d.role == "benign"].groupby("source").false_alarm.mean().mean()
    nul = d[d.role == "null"].false_alarm.mean()
    r = {"frac": frac, "arm": arm, "dev_harm_power": harm, "dev_benign_fa": ben, "dev_null_fa": nul}
    for s in ("G3dev", "G4dev"):
        x = d[d.source == s]
        has = (
            x.detected | ~x.false_alarm
        )  # seeds without harm are not separable here; power over all seeds is reported
        r[f"{s}_power_allseeds"] = x.detected.mean()
        r[f"{s}_fa"] = x.false_alarm.mean()
    rows.append(r)
out = pd.DataFrame(rows)
out.to_csv("outputs/h2c_next/dev_summary.csv", index=False)
pd.set_option("display.width", 250)
for f in (0.1, 0.2):
    print(out[out.frac == f].drop(columns="frac").round(3).to_string(index=False))
