"""Frozen G4 confirmation (docs/hg_v2/FROZEN_CONFIRMATION_PROTOCOL.md). Run once."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

THR = float(np.log(20))
ARMS = {
    "F1_H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
    "F2_gONS_hard200": ("pp_ons_gated", {"gate": "hard", "w": 200}),
    "F3_gONS_multi": ("pp_ons_gated", {"gate": "multi", "w_short": 30, "w_long": 200}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "ONS": ("pp_ons", {}),
    "parent": ("pprm_tight", {}),
    "cost_parent": ("pp_cost_tight", {}),
    "cost_DK": ("fix_cost", {"gamma": 0.995, "uniform_cap": True}),
    "disc_only": ("fix_brier", {"gamma": 0.99, "uniform_cap": True}),
}
sim = g.simulate_g4(1000, 50000)
null = g.simulate_g4(400, 50500, transition=np.eye(3))
T = sim["y"].shape[1]
fh = np.where(sim["harmful"].any(1), sim["harmful"].argmax(1), T)
hp = fh < T
cum = np.cumsum(sim["harm"], 1)
rng = np.random.default_rng(13)
res, det_by = [], {}
for frac in (0.10, 0.20):
    for arm, (name, extra) in ARMS.items():
        p = {"frac": frac, "delay": 5, "tol": 0.0, **extra}
        al = det.first_cross(
            np.nan_to_num(det.DETECTORS[name](sim, lseed=51000, **p), nan=-np.inf), THR
        )
        aln = det.first_cross(
            np.nan_to_num(det.DETECTORS[name](null, lseed=51000, **p), nan=-np.inf), THR
        )
        d = ((al < T) & (al >= fh) & hp)[hp].astype(float)
        det_by[(frac, arm)] = d
        res.append(
            {
                "frac": frac,
                "arm": arm,
                "power": d.mean(),
                "false_alarm": float((al < fh).mean()),
                "null_fa": float((aln < T).mean()),
                "harm_before": float(cum[np.arange(len(al)), np.minimum(al, T - 1)][hp].mean()),
            }
        )
out = pd.DataFrame(res)
out.to_csv("outputs/hg_v2/g4_confirmation.csv", index=False)
pd.set_option("display.width", 200)
print(out.round(3).to_string(index=False))


def ci(a, b, frac):
    diff = det_by[(frac, a)] - det_by[(frac, b)]
    bs = diff[rng.integers(0, len(diff), (4000, len(diff)))].mean(1)
    return float(diff.mean()), float(np.quantile(bs, 0.025)), float(np.quantile(bs, 0.975))


def row(frac, arm):
    return out[(out.frac == frac) & (out.arm == arm)].iloc[0]


verdict = {}
for frac in (0.10, 0.20):
    m, lo, hi = ci("F1_H2c", "cost_parent", frac)
    verdict[f"C1/{frac}"] = (m >= 0.10 and lo > 0, round(m, 3), round(lo, 3))
    for f_, tag in (("F2_gONS_hard200", "C2"), ("F3_gONS_multi", "C3")):
        pw_ok = row(frac, f_).power >= row(frac, "ONS").power - 0.03
        fa_ok = row(frac, f_).false_alarm <= row(frac, "ONS").false_alarm
        m2, lo2, _ = ci(f_, "HG_unifcap", frac)
        verdict[f"{tag}/{frac}"] = (
            bool(pw_ok and fa_ok),
            "vs ONS power",
            round(float(row(frac, f_).power - row(frac, "ONS").power), 3),
            "FA",
            round(float(row(frac, f_).false_alarm - row(frac, "ONS").false_alarm), 3),
        )
        verdict[f"{tag}b/{frac}"] = (m2 >= 0.03, round(m2, 3), round(lo2, 3))
    for a in ("F1_H2c", "F2_gONS_hard200", "F3_gONS_multi"):
        verdict[f"C4/{frac}/{a}"] = (
            bool(row(frac, a).null_fa <= 0.07),
            round(float(row(frac, a).null_fa), 3),
        )
for k, v in verdict.items():
    print(k, v)
print("harm seeds", int(hp.sum()))
