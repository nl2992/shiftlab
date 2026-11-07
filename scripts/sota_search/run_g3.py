"""Frozen G3 confirmation (docs/hg_validation/05_G3_FROZEN_PROTOCOL.md). Run once."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

THR = float(np.log(20))
ARMS = {
    "parent": ("pprm_tight", {}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "ONS": ("pp_ons", {}),
    "mixture8": ("pp_mixture", {}),
    "disc_only": ("fix_brier", {"gamma": 0.99, "uniform_cap": True}),
}


def score(sim, alarm):
    T = alarm.shape[0] and sim["y"].shape[1]
    fh = np.where(sim["harmful"].any(1), sim["harmful"].argmax(1), T)
    cum = np.cumsum(sim["harm"], 1)
    idx = np.minimum(alarm, T - 1)
    return {
        "detected": (alarm < T) & (alarm >= fh) & (fh < T),
        "false_alarm": alarm < fh,
        "harm_before": cum[np.arange(len(alarm)), idx],
        "has_harm": fh < T,
    }


sim = g.simulate_g3(1000, 20000)
null = g.simulate_g3(400, 20500, transition=np.eye(3))
rows = []
for frac in (0.10, 0.20):
    for arm, (name, extra) in ARMS.items():
        p = {"frac": frac, "delay": 5, "tol": 0.0, **extra}
        al = det.first_cross(
            np.nan_to_num(det.DETECTORS[name](sim, lseed=21000, **p), nan=-np.inf), THR
        )
        sc = score(sim, al)
        aln = det.first_cross(
            np.nan_to_num(det.DETECTORS[name](null, lseed=21000, **p), nan=-np.inf), THR
        )
        for s in range(len(al)):
            rows.append(
                {
                    "frac": frac,
                    "arm": arm,
                    "seed": s,
                    "detected": bool(sc["detected"][s]),
                    "false_alarm": bool(sc["false_alarm"][s]),
                    "harm_before": float(sc["harm_before"][s]),
                    "has_harm": bool(sc["has_harm"][s]),
                    "null_alarm": bool(aln[s % len(aln)] < null["y"].shape[1])
                    if s < len(aln)
                    else None,
                }
            )
df = pd.DataFrame(rows)
df.to_parquet("outputs/hg_validation/05_G3_PER_SEED.parquet")
rng = np.random.default_rng(11)
res = []
for frac in (0.10, 0.20):
    d = df[df.frac == frac]
    hp = d[d.has_harm]
    pw = {a: hp[hp.arm == a].sort_values("seed").detected.astype(float).values for a in ARMS}
    fa = {a: d[d.arm == a].sort_values("seed").false_alarm.astype(float).values for a in ARMS}
    nul = {
        a: float(d[(d.arm == a) & d.null_alarm.notna()].null_alarm.astype(float).mean())
        for a in ARMS
    }
    for a in ARMS:
        res.append(
            {
                "frac": frac,
                "arm": a,
                "power_harm_seeds": pw[a].mean(),
                "false_alarm_all": fa[a].mean(),
                "null_fa": nul[a],
                "harm_before": hp[hp.arm == a].harm_before.mean(),
            }
        )
    base = pw["parent"]
    for a in ("HG_unifcap", "ONS", "disc_only", "mixture8"):
        diff = pw[a] - base
        idx = rng.integers(0, len(diff), (4000, len(diff)))
        b = diff[idx].mean(1)
        res.append(
            {
                "frac": frac,
                "arm": a + "_minus_parent",
                "power_harm_seeds": diff.mean(),
                "ci_lo": float(np.quantile(b, 0.025)),
                "ci_hi": float(np.quantile(b, 0.975)),
            }
        )
out = pd.DataFrame(res)
out.to_csv("outputs/hg_validation/05_G3_RESULTS.csv", index=False)
pd.set_option("display.width", 200)
print(out.round(3).to_string(index=False))
print("harm seeds:", int(df[(df.frac == 0.1) & (df.arm == "parent")].has_harm.sum()))
