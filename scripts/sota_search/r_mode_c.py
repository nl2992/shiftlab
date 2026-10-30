"""Mode C: empirical thresholds calibrated on a G1 null stream (horizon-max 95th percentile) for every method."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import restart as rs

T, N = 2000, 400
SRC = {
    "H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
    "costONS": ("pp_cost_guided", {"mode": "cost_ons"}),
    "guidedONS": ("pp_cost_guided", {"mode": "guided"}),
}


def stats_for(sim, lseed, p):
    out = {}
    for sname, (name, extra) in SRC.items():
        lf = rs.log_factors(det.DETECTORS[name](sim, lseed=lseed, **p, **extra))
        out[f"{sname}|single"] = np.exp(lf.cumsum(1))
        out[f"{sname}|geometric"] = rs.restart_mixture(lf, rs.start_weights("geometric", T))
        out[f"{sname}|SR"] = rs.sr_statistic(lf)
    out["SR0_existing"] = det.DETECTORS["sr_cost_tight"](sim, lseed=lseed, **p)
    return out


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
null = g.simulate(g.World(kind="none"), 1000, 9100)
rows = []
for frac in (0.05, 0.10, 0.20):
    p = {"frac": frac, "delay": 5, "tol": 0.0}
    ns = stats_for(null, 109000, p)
    thr = {m: float(np.quantile(np.nan_to_num(a, nan=-np.inf).max(1), 0.95)) for m, a in ns.items()}
    for wi, (label, w) in enumerate(worlds.items()):
        sim = g.simulate(w, N, 100000 + wi)
        tr = g.truth(w)
        fh = int(tr["harmful"].argmax())
        for m, arr in stats_for(sim, 105000 + wi, p).items():
            hit = np.nan_to_num(arr, nan=-np.inf) >= thr[m]
            al = np.where(hit.any(1), hit.argmax(1), T)
            rows.append(
                {
                    "world": label,
                    "frac": frac,
                    "method": m,
                    "power": float(((al < T) & (al >= fh)).mean()),
                    "fa": float((al < fh).mean()),
                    "thr": thr[m],
                }
            )
    print(frac, flush=True)
df = pd.DataFrame(rows)
df.to_csv("outputs/h2c_restart/mode_c.csv", index=False)
pd.set_option("display.width", 200)
print(df.groupby(["method", "frac"]).power.mean().unstack(1).round(3).to_string())
print(df.groupby(["method", "frac"]).thr.first().unstack(1).round(1).to_string())
