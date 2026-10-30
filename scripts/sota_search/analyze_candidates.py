"""Batch-1 analysis: X1 (tight vs loose), S01 (cost vs Brier), S02 (SR e-detector). See 03b_*."""

import json

import numpy as np
import pandas as pd

df = pd.read_csv(
    "outputs/sota_search/q1_baselines_summary_cand.csv", keep_default_na=False, na_values=[""]
)
df["p"] = df.params.map(json.loads)
for k in ("frac", "delay", "tol"):
    df[k] = df.p.map(lambda d, k=k: d[k])
print("roles:", df.groupby("role").world.nunique().to_dict())
key = ["frac", "delay", "tol", "world"]


def piv(name, col):
    return df[df.detector == name].set_index(key)[col]


print("\n== NULL false-alarm by detector (max over configs; theory threshold 0.05) ==")
nul = df[df.role == "null"].groupby("detector").false_alarm_prob.agg(["mean", "max"]).round(3)
print(nul.to_string())

print("\n== X1: tight vs loose, power on harm worlds, paired over (frac, delay, tol, world) ==")
harm = df[df.role == "harm"]
for loose, tight in (("pprm", "pprm_tight"), ("pp_cost", "pp_cost_tight")):
    a = harm[harm.detector == loose].set_index(key).detect_prob
    b = harm[harm.detector == tight].set_index(key).detect_prob
    d = (b - a).dropna()
    print(
        f"{loose:8s} -> {tight:14s} mean diff {d.mean():+.3f}  median {d.median():+.3f}  frac(tight>loose) {np.mean(d > 0):.2f}  frac(tight<loose) {np.mean(d < 0):.2f}  n={len(d)}"
    )
    for f in (0.05, 0.1, 0.2):
        dd = d[d.index.get_level_values("frac") == f]
        print(f"      frac={f}: mean diff {dd.mean():+.3f}")
    pl = harm[harm.detector == loose].detect_prob.mean()
    pt = harm[harm.detector == tight].detect_prob.mean()
    print(f"      overall power loose {pl:.3f} tight {pt:.3f}")

print(
    "\n== S01: decision-cost vs Brier (tight), power on harm worlds and false alarm on benign-shift worlds =="
)
for name in ("pprm_tight", "pp_cost_tight"):
    h = df[(df.detector == name) & (df.role == "harm")].detect_prob.mean()
    b = df[(df.detector == name) & (df.role == "benign")].false_alarm_prob.mean()
    dl = df[(df.detector == name) & (df.role == "harm")].mean_delay.mean()
    hb = df[(df.detector == name) & (df.role == "harm")].mean_harm_before_alarm.mean()
    print(f"{name:14s} power_harm {h:.3f}  fa_benign {b:.3f}  delay {dl:.0f}  harm_before {hb:.0f}")
print("  by benign-world kind (false alarm, tight versions):")
for name in ("pprm_tight", "pp_cost_tight"):
    sub = df[(df.detector == name) & (df.role == "benign")]
    print(
        "   ",
        name,
        sub.assign(kind=sub.world.str.split("|").str[1])
        .groupby("kind")
        .false_alarm_prob.mean()
        .round(3)
        .to_dict(),
    )

print(
    "\n== S02: SR e-detector (empirical threshold) vs single-start tight e-process, harm worlds =="
)
for name in ("pprm_tight", "pp_cost_tight", "sr_brier_tight", "sr_cost_tight"):
    s = df[(df.detector == name) & (df.role == "harm")]
    bn = df[(df.detector == name) & (df.role == "benign")].false_alarm_prob.mean()
    print(
        f"{name:15s} power {s.detect_prob.mean():.3f}  delay {s.mean_delay.mean():.0f}  harm_before {s.mean_harm_before_alarm.mean():.0f}  fa_benign {bn:.3f}"
    )
