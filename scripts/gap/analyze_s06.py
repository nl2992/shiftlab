import pandas as pd

pd.set_option("display.width", 220)
df = pd.read_parquet("outputs/gap_closure/e5_s06_all_perseed.parquet")
df["hardB"] = (df.frac_cfg * df["T"]).round()
big = df[df["T"] == 2000]
harm = big[big.group != "null"]
print("rows", len(df), "pathwise compliance: max labels - B (should be <=0 for hard-budget arms):")
hb = df[~df.config.isin(["bernoulli"])]
print((hb.labels - hb.hardB).groupby(hb.config).max().to_dict())
pw = (
    harm.assign(has=harm.first_harm < harm["T"])
    .groupby(["frac_cfg", "delay_cfg", "config"])
    .apply(lambda d: d.detected.sum() / max(d.has.sum(), 1), include_groups=False)
    .rename("power")
    .reset_index()
)
t = pw.pivot_table(index=["frac_cfg", "delay_cfg"], columns="config", values="power")
print("\npower (all onset x regime), T=2000")
print(t.round(3).to_string())
m = pw.groupby(["frac_cfg", "config"]).power.mean().unstack()
print("\nmean over delays:\n", m.round(3).to_string())
fa = big[big.group == "null"].groupby(["frac_cfg", "config"]).false_alarm.mean().unstack()
print("\nnull FA\n", fa.round(3).to_string())
# onset x regime for frac .1 delay 5
sub = harm[(harm.frac_cfg == 0.10) & (harm.delay_cfg == 5)].assign(
    onset=lambda d: d.world.str.extract(r"on([0-9.]+)", expand=False),
    regime=lambda d: d.world.str.split("|").str[2],
)
print(
    "\nonset x regime (f=.1,d=5) power:\n",
    sub.groupby(["onset", "config"])
    .apply(lambda d: d.detected.sum() / max((d.first_harm < d["T"]).sum(), 1), include_groups=False)
    .unstack()
    .round(3)
    .to_string(),
)
q = (
    big[(big.frac_cfg == 0.10)]
    .groupby(["delay_cfg", "config"])
    .agg(
        mean_pending=("mean_pending", "mean"),
        max_pending=("max_pending", "max"),
        exhausted=("exhaust_t", lambda s: (s < 2000).mean()),
        labels=("labels", "mean"),
    )
    .round(2)
)
print("\npending/exhaustion (f=.1)\n", q.unstack(0).to_string())
spend = (
    big[(big.frac_cfg == 0.10) & (big.delay_cfg == 5) & (big.group != "null")]
    .groupby("config")
    .apply(
        lambda d: pd.Series(
            {
                "mean_exhaust_t": d.exhaust_t[d.exhaust_t < 2000].mean(),
                "frac_exhausted": (d.exhaust_t < 2000).mean(),
            }
        ),
        include_groups=False,
    )
)
print("\nspend timing\n", spend.round(1).to_string())
sm = (
    df[df["T"] < 2000]
    .assign(has=lambda d: d.first_harm < d["T"])
    .groupby(["T", "frac_cfg", "config"])
    .apply(lambda d: d.detected.sum() / max(d.has.sum(), 1), include_groups=False)
    .unstack()
)
print("\nshort horizons\n", sm.round(3).to_string())
