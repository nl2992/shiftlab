"""Aggregate Q1 baseline results by the preregistered screening metric (docs/sota_synthetic_search/03_*)."""

import glob
import sys

import pandas as pd

files = sys.argv[1:] or sorted(glob.glob("outputs/sota_search/q1_baselines_summary_*.csv"))
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
df["cfg"] = df["detector"] + "|" + df["params"]
harm = df[df.role == "harm"].groupby("cfg").detect_prob.mean().rename("power_harm")
benign_fa = df[df.role == "benign"].groupby("cfg").false_alarm_prob.mean().rename("fa_benign")
null_fa = df[df.role == "null"].groupby("cfg").false_alarm_prob.mean().rename("fa_null")
delay = df[df.role == "harm"].groupby("cfg").mean_delay.mean().rename("delay")
hb = df[df.role == "harm"].groupby("cfg").mean_harm_before_alarm.mean().rename("harm_before")
lab = df[df.role == "harm"].groupby("cfg").mean_labels.mean().rename("labels")
t = pd.concat([harm, benign_fa, null_fa, delay, hb, lab], axis=1)
t["screen"] = t.power_harm - t.fa_benign
t["detector"] = [c.split("|")[0] for c in t.index]
t.to_csv("outputs/sota_search/q1_config_table.csv")
pd.set_option("display.width", 200)
best = (
    t.sort_values("screen", ascending=False)
    .groupby("detector")
    .head(1)
    .sort_values("screen", ascending=False)
)
print(
    "BEST CONFIG PER DETECTOR (screen = power on harm worlds - false alarm on benign-shift worlds)"
)
print(
    best[["power_harm", "fa_benign", "fa_null", "delay", "harm_before", "labels", "screen"]]
    .round(3)
    .to_string()
)
print()
print("configs:", len(t), "| detectors:", t.detector.nunique())
