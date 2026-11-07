"""Does an SR threshold calibrated on the G1 null keep its false-alarm rate on other nulls? (Mode C validity transfer)"""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import restart as rs

T = 2000
SRC = ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995})


def stats_for(sim, lseed, p):
    lf = rs.log_factors(det.DETECTORS[SRC[0]](sim, lseed=lseed, **p, **SRC[1]))
    return {
        "H2c|SR": rs.sr_statistic(lf),
        "H2c|single": np.exp(lf.cumsum(1)),
        "SR0_existing": det.DETECTORS["sr_cost_tight"](sim, lseed=lseed, **p),
    }


def ar_sim(rho, n=400, seed=0):
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((n, T, g.D))
    x = np.empty_like(e)
    x[:, 0] = e[:, 0]
    for t in range(1, T):
        x[:, t] = rho * x[:, t - 1] + np.sqrt(1 - rho**2) * e[:, t]
    y = (rng.random((n, T)) < g.sigmoid(x @ g.W_SRC + g.B_SRC)).astype(np.int8)
    p = g.sigmoid(x @ g.W_SRC + g.B_SRC)
    act = (p >= g.TAU).astype(float)
    return {
        "x": x.astype(np.float32),
        "y": y,
        "p": p,
        "loss": g.decision_cost(act, y),
        "brier": (p - y) ** 2,
        "world": g.World(kind="none", T=T),
    }


targets = {
    "G1_other_seed": g.simulate(g.World(kind="none"), 400, 9200),
    "G2_null": g.simulate(g.World(kind="none", family="G2"), 400, 9201),
    "AR0.9": ar_sim(0.9, seed=9202),
    "AR0.98": ar_sim(0.98, seed=9203),
}
for i, c in enumerate(g.G5_CONDITIONS):
    targets[f"G5:{c}"] = g.simulate_g5(c, "none", 400, 9300 + i)
cal = g.simulate(g.World(kind="none"), 1000, 9100)
rows = []
for frac in (0.10, 0.20):
    p = {"frac": frac, "delay": 5, "tol": 0.0}
    thr = {
        m: float(np.quantile(np.nan_to_num(a, nan=-np.inf).max(1), 0.95))
        for m, a in stats_for(cal, 109000, p).items()
    }
    for tname, sim in targets.items():
        for m, arr in stats_for(sim, 110000, p).items():
            t_ = thr[m]
            rows.append(
                {
                    "frac": frac,
                    "target": tname,
                    "method": m,
                    "null_fa_at_G1_calibrated_threshold": float(
                        (np.nan_to_num(arr, nan=-np.inf).max(1) >= t_).mean()
                    ),
                }
            )
    print(frac, flush=True)
df = pd.DataFrame(rows)
df.to_csv("outputs/h2c_restart/calibration_transfer.csv", index=False)
pd.set_option("display.width", 200)
print(
    df.pivot_table(
        index=["frac", "target"], columns="method", values="null_fa_at_G1_calibrated_threshold"
    )
    .round(3)
    .to_string()
)
