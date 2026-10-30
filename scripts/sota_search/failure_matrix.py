"""Cross-method failure matrix on calibration-eligible configurations (null false alarm <= 0.07)."""

import glob
import json

import pandas as pd

files = sorted(glob.glob("outputs/sota_search/q1_baselines_summary_*.csv"))
df = pd.concat(
    [pd.read_csv(f, keep_default_na=False, na_values=[""]) for f in files], ignore_index=True
)
df["cfg"] = df.detector + "|" + df.params
df = df.drop_duplicates(["cfg", "world"])  # loose pprm/pp_cost appear in both batches with identical seeds
null_fa = df[df.role == "null"].set_index("cfg").false_alarm_prob
df["fa_null"] = df.cfg.map(null_fa)
elig = df[(df.fa_null <= 0.07) & (df.role != "null")].copy()
excluded = sorted(set(df.cfg[df.role == "null"]) - set(null_fa[null_fa <= 0.07].index))
print(
    f"eligible configs {elig.cfg.nunique()} of {df.cfg.nunique()}; excluded for null FA > 0.07: {len(excluded)}"
)
elig["fam"] = elig.detector.replace(
    {
        "pprm_tight": "pprm_t",
        "pp_cost_tight": "cost_t",
        "page_hinkley": "PH",
        "sr_cost_tight": "sr_cost",
        "sr_brier_tight": "sr_brier",
    }
)
elig["wk"] = (
    elig.world.str.split("|").str[1]
    + "/"
    + elig.world.str.split("|").str[3]
    + "/"
    + elig.world.str.split("|").str[2]
)
harm = elig[elig.role == "harm"]
best = harm.groupby(["wk", "fam"]).detect_prob.max().unstack().round(2)
print("\nBEST-CONFIG POWER on each harm world (rows) by detector family (cols):")
print(best.to_string())
print("\nfamilies that fail (best power < 0.30) on each harm world:")
for wk, row in best.iterrows():
    print(f"  {wk:28s} best={row.max():.2f}  failing={[c for c in best.columns if row[c] < 0.30]}")
ben = elig[elig.role == "benign"].groupby(["wk", "fam"]).false_alarm_prob.min().unstack().round(2)
print(
    "\nLOWEST achievable false alarm on each benign-shift world, by family (min over eligible configs):"
)
print(ben.to_string())
print(
    "\nMEDIAN (typical config) power on harm worlds by label rate and delay, pooled over label-using families:"
)
lab = harm[harm.mean_labels > 0].copy()
lab["frac"] = lab.params.map(lambda s: json.loads(s).get("frac"))
lab["delay"] = lab.params.map(lambda s: json.loads(s).get("delay"))
print(lab.groupby(["frac", "delay"]).detect_prob.median().unstack().round(3).to_string())
