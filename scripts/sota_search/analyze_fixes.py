"""Apply the frozen decision rules of docs/sota_synthetic_search/09_NOVELTY_FIX_DESIGNS.md."""

import json
import sys

import pandas as pd

split = sys.argv[1] if len(sys.argv) > 1 else "fix"
fix_csv = f"outputs/sota_search/q1_baselines_summary_{split}.csv"
par_csv = sys.argv[2] if len(sys.argv) > 2 else "outputs/sota_search/q1_baselines_summary_cand.csv"
read = dict(keep_default_na=False, na_values=[""])
fx, par = pd.read_csv(fix_csv, **read), pd.read_csv(par_csv, **read)
for d in (fx, par):
    d["p"] = d.params.map(json.loads)
    d["frac"] = d.p.map(lambda x: x["frac"])
par = par[par.p.map(lambda x: x["delay"] == 5 and x["tol"] == 0.0)]
PARENT = {"fix_brier": "pprm_tight", "fix_cost": "pp_cost_tight"}


def label(p):
    parts = [f"g={p.get('gamma', 1.0)}"]
    if "gate_w" in p:
        parts.append(f"gate={p['gate_w']}")
    if "alloc" in p:
        parts.append(f"bd={tuple(p['alloc'])}")
    return " ".join(parts)


rows = []
for (det, params), grp in fx.groupby(["detector", "params"]):
    p = json.loads(params)
    pr = par[(par.detector == PARENT[det]) & (par.frac == p["frac"])]
    m = grp.merge(pr, on="world", suffixes=("", "_p"))
    harm, ben, nul = (m[m.role == r] for r in ("harm", "benign", "null"))
    dpow = harm.detect_prob - harm.detect_prob_p
    rows.append(
        {
            "detector": det,
            "frac": p["frac"],
            "variant": label(p),
            "power": harm.detect_prob.mean(),
            "parent_power": harm.detect_prob_p.mean(),
            "dpow": dpow.mean(),
            "improved": int((dpow > 0.0).sum()),
            "worse5": int((dpow < -0.05).sum()),
            "fa_ben": ben.false_alarm_prob.mean(),
            "dfa_ben": (ben.false_alarm_prob - ben.false_alarm_prob_p).mean(),
            "fa_null": float(nul.false_alarm_prob.iloc[0]) if len(nul) else float("nan"),
            "label_ratio": harm.mean_labels.mean() / max(harm.mean_labels_p.mean(), 1e-9),
            "harm_before": harm.mean_harm_before_alarm.mean(),
            "parent_hb": harm.mean_harm_before_alarm_p.mean(),
        }
    )
t = pd.DataFrame(rows)
import numpy as np

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

null_sim = g.simulate(g.World(kind="none", T=1500), 40, 5)


def rate_ratio(variant, frac):
    """BD label matching is about the realized query RATE (labels-to-alarm shrinks when alarms come earlier)."""
    if "bd=" not in variant:
        return 1.0
    h, fl = eval(variant.split("bd=")[1].split(")")[0] + ")")
    return float(det._boundary_q(null_sim, frac, h, fl).mean() / frac)


t["rate_ratio"] = [rate_ratio(v, f) for v, f in zip(t.variant, t.frac, strict=True)]
ctrl = t[~t.variant.str.contains("bd=|gate=")].set_index(["detector", "frac", "variant"]).dpow
t["dpow_marg"] = [
    dp - ctrl.get((d, f, "g=" + v.split("g=")[1].split(" ")[0]), np.nan) if "bd=" in v else dp
    for d, f, v, dp in zip(t.detector, t.frac, t.variant, t.dpow, strict=True)
]
t["ok"] = (
    (t.dpow >= 0.05)
    & (t.improved >= 7)
    & (t.worse5 == 0)
    & (t.fa_null <= 0.07)
    & (t.dfa_ben <= 0.02)
    & t.rate_ratio.between(0.9, 1.1)
)
t["ok_marginal_bd"] = t.ok & ((~t.variant.str.contains("bd=")) | (t.dpow_marg >= 0.05))
pd.set_option("display.width", 230)
cols = [
    "detector",
    "frac",
    "variant",
    "power",
    "parent_power",
    "dpow",
    "dpow_marg",
    "improved",
    "worse5",
    "fa_ben",
    "dfa_ben",
    "fa_null",
    "rate_ratio",
    "harm_before",
    "parent_hb",
    "ok",
    "ok_marginal_bd",
]
print(t.sort_values("dpow", ascending=False)[cols].round(3).to_string(index=False))
isbd = t.variant.str.contains("bd=")
print(
    "\nmeeting the frozen rule vs parent:",
    int(t.ok.sum()),
    "of",
    len(t),
    "| BD rows also meeting it marginally over the same-gamma control:",
    int(t[isbd].ok_marginal_bd.sum()),
    "of",
    int(isbd.sum()),
)
print("\nrule met at BOTH label rates (0.1 and 0.2), marginal rule for BD:")
g2 = t.groupby(["detector", "variant"]).agg(
    n=("ok_marginal_bd", "sum"),
    dpow=("dpow", "mean"),
    marg=("dpow_marg", "mean"),
    dfa=("dfa_ben", "mean"),
)
print(g2[g2.n == 2].sort_values("dpow", ascending=False).round(3).to_string())
t.to_csv(f"outputs/sota_search/fix_decision_table_{split}.csv", index=False)
