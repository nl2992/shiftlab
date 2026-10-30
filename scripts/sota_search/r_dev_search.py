"""Development search (docs/h2c_restart/RESEARCH_CHARTER.md): restart mixtures over H2c / cost-ONS / guided-ONS factors."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h
from shiftlab.sota_search import restart as rs

T, ALPHA, N = 2000, 0.05, 400
THR = float(np.log(1 / ALPHA))
SRC = {
    "H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
    "costONS": ("pp_cost_guided", {"mode": "cost_ons"}),
    "guidedONS": ("pp_cost_guided", {"mode": "guided"}),
}
KINDS = ("single", "uniform", "front", "geometric", "coarse8")
worlds = {}
for onset in (300, 1000, 1500):
    for shape, extra in (
        ("abrupt", {}),
        ("transient", {"length": 200}),
        ("recurrent", {"period": 400}),
    ):
        for delta in (1.5, 2.0):
            worlds[f"onset{onset}/{shape}/d{delta}"] = g.World(
                kind="concept", delta=delta, shape=shape, t0=onset, **extra
            )
worlds["null"] = g.World(kind="none")
null_cal = g.simulate(g.World(kind="none"), 400, 9000)
rows = []
for wi, (label, w) in enumerate(worlds.items()):
    sim = g.simulate(w, N, 100000 + wi)
    tr = g.truth(w)
    harmful = bool(tr["harmful"].any())
    fh = int(tr["harmful"].argmax()) if harmful else T
    cum_harm = np.cumsum(np.maximum(tr["harm"], 0.0))
    for frac in (0.05, 0.10, 0.20):
        p = {"frac": frac, "delay": 5, "tol": 0.0}
        stats = {}
        for sname, (name, extra) in SRC.items():
            lf = rs.log_factors(det.DETECTORS[name](sim, lseed=105000 + wi, **p, **extra))
            for kind in KINDS:
                stats[f"{sname}|{kind}"] = (
                    rs.restart_mixture(lf, rs.start_weights(kind, T)),
                    1 / ALPHA,
                )
            if sname != "guidedONS":
                R = rs.sr_statistic(lf)
                stats[f"{sname}|SR_ARL(1/a)"] = (R, 1 / ALPHA)
                stats[f"{sname}|SR_FWER(T/a)"] = (R, T / ALPHA)
        st0 = det.DETECTORS["sr_cost_tight"](sim, lseed=105000 + wi, **p)
        stats["SR0_existing_empirical"] = (st0, h.calibrate("sr_cost_tight", p, null_cal))
        for m, (arr, thr) in stats.items():
            hit = arr >= thr
            al = np.where(hit.any(1), hit.argmax(1), T)
            det_ = (al < T) & (al >= fh) & harmful
            rows.append(
                {
                    "world": label,
                    "role": "harm" if harmful else "null",
                    "frac": frac,
                    "method": m,
                    "power": float(det_.mean()) if harmful else np.nan,
                    "false_alarm": float((al < fh).mean()),
                    "delay": float((al[det_] - fh).mean()) if det_.any() else np.nan,
                    "harm_before": float(cum_harm[np.minimum(al, T - 1)].mean()),
                }
            )
    print(label, flush=True)
df = pd.DataFrame(rows)
df.to_csv("outputs/h2c_restart/dev_search.csv", index=False)
harm = df[df.role == "harm"].copy()
harm["kind"] = harm.world.str.split("/").str[1]
harm["onset"] = harm.world.str.split("/").str[0]
nul = df[df.role == "null"].groupby(["frac", "method"]).false_alarm.mean()
pd.set_option("display.width", 220)
s = harm.groupby(["frac", "method"]).power.mean().unstack(0).round(3)
s["nullFA@.05/.10/.20"] = [
    " / ".join(f"{nul[(f, m)]:.3f}" for f in (0.05, 0.10, 0.20)) for m in s.index
]
print(s.to_string())
late = harm[(harm.onset != "onset300") | (harm.kind != "abrupt")]
print(late.groupby(["frac", "method"]).power.mean().unstack(0).round(3).to_string())
