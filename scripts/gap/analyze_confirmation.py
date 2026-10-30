"""Statistics and documents for the frozen confirmation run (paired cluster bootstrap, Holm over the primary list)."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.gap.store import wilson

O = Path("outputs/gap_closure")
D = Path("docs/sota_gap_closure")
spec = json.load(open("configs/gap_closure/frozen_confirmation_v1.json"))
df = pd.read_parquet(O / "e15_confirm/perseed.parquet")
df["has_harm"] = df.first_harm < df["T"]
rng = np.random.default_rng(2026)


def md(d, ff="{:.3f}", index=True):
    if index:
        d = d.reset_index()
    out = [
        "| " + " | ".join(map(str, d.columns)) + " |",
        "|" + "|".join("---" for _ in d.columns) + "|",
    ]
    for _, r in d.iterrows():
        out.append(
            "| "
            + " | ".join(
                ff.format(v)
                if isinstance(v, float | np.floating) and not pd.isna(v)
                else ("" if pd.isna(v) else str(v))
                for v in r
            )
            + " |"
        )
    return "\n".join(out)


worlds = df.groupby("world").agg(has=("has_harm", "mean")).reset_index()
harm_w = list(worlds[worlds.has > 0.5].world)
null_w = list(worlds[worlds.has <= 0.5].world)
arms = list(df.config.unique())
n_w = df.groupby("world").seed.nunique()

# per-world table
pw = df[df.world.isin(harm_w) & df.has_harm].groupby(["world", "config"]).detected.mean().unstack()
hb = df[df.world.isin(harm_w)].groupby(["world", "config"]).harm_before.mean().unstack()
fa_h = df[df.world.isin(harm_w)].groupby(["world", "config"]).false_alarm.mean().unstack()
fa_n = df[df.world.isin(null_w)].groupby(["world", "config"]).false_alarm.mean().unstack()


def ci_tab(fa):
    out = fa.copy().astype(object)
    for wd in fa.index:
        n = int(n_w[wd])
        for a in fa.columns:
            lo, hi = wilson(fa.loc[wd, a] * n, n)
            out.loc[wd, a] = f"{fa.loc[wd, a]:.3f} [{lo:.3f}, {hi:.3f}]" + (
                " **>alpha**" if lo > 0.05 else ""
            )
    return out


def paired(a, b, metric):
    """Cluster bootstrap over worlds then seeds of the mean paired difference (worlds weighted equally)."""
    diffs = []
    for wd in harm_w if metric == "power" else harm_w + null_w:
        x = df[(df.world == wd) & (df.config == a)].set_index("seed")
        y = df[(df.world == wd) & (df.config == b)].set_index("seed")
        if metric == "power":
            m = x.has_harm
            d = (x.detected.astype(float) - y.detected.astype(float))[m].values
        elif metric == "fa":
            d = (x.false_alarm.astype(float) - y.false_alarm.astype(float)).values
        else:
            d = (x.harm_before - y.harm_before).values
        diffs.append(d)
    obs = np.mean([d.mean() for d in diffs])
    boots = np.empty(4000)
    for i in range(4000):
        ws = rng.integers(0, len(diffs), len(diffs))
        boots[i] = np.mean(
            [diffs[w][rng.integers(0, len(diffs[w]), len(diffs[w]))].mean() for w in ws]
        )
    p = 2 * min((boots <= 0).mean(), (boots >= 0).mean())
    return obs, np.quantile(boots, 0.025), np.quantile(boots, 0.975), max(p, 1 / 4000)


prim = [(f"{a}@{f}", f"{b}@{f}") for f in spec["fracs"] for a, b in spec["primary_comparisons"]]
rows = []
for a, b in prim:
    if a not in arms or b not in arms:
        continue
    for metric in ("power", "fa", "harm_before"):
        o, lo, hi, p = paired(a, b, metric)
        rows.append(
            {
                "A": a,
                "B": b,
                "metric": metric,
                "diff (A-B)": o,
                "ci_lo": lo,
                "ci_hi": hi,
                "p_raw": p,
            }
        )
st = pd.DataFrame(rows)
pm = st[st.metric == "power"].copy()
order = pm.p_raw.argsort().values
m = len(pm)
holm = np.empty(m)
run = 0.0
for rank, idx in enumerate(order):
    run = max(run, min(1.0, (m - rank) * pm.p_raw.values[idx]))
    holm[idx] = run
st.loc[pm.index, "p_holm(power family)"] = holm
st["effect>=threshold"] = np.where(
    st.metric == "power",
    st["diff (A-B)"].abs() >= 0.03,
    np.where(st.metric == "fa", st["diff (A-B)"].abs() >= 0.02, np.nan),
)
(
    D / "FINAL_STATISTICAL_COMPARISONS.md"
).write_text(f"""# Final statistical comparisons (frozen protocol; paired cluster bootstrap, 4,000 resamples; worlds weighted equally)
Primary power comparisons are Holm-adjusted together (family size {m}); false-alarm and harm-before-alarm rows are secondary. Harm worlds: {len(harm_w)}; null worlds: {len(null_w)}. A - B > 0 favours A for power, favours B for false alarm and harm-before-alarm.

{md(st, index=False)}

Practical thresholds: power 0.03, false alarm 0.02. Intervals reflect world and seed variability of the synthetic pools only; they say nothing about real data.
""")
mean_arm = pd.DataFrame(
    {
        "power (harm worlds, mean)": pw.mean(),
        "harm before alarm": hb.mean(),
        "FA before harm (harm worlds)": fa_h.mean(),
        "FA (null worlds, mean)": fa_n.mean(),
        "FA (null worlds, max)": fa_n.max(),
    }
)
(
    D / "FINAL_SYNTHETIC_CONFIRMATION_RESULTS.md"
).write_text(f"""# Final synthetic confirmation results (single run of `FINAL_SYNTHETIC_CONFIRMATION_PROTOCOL.md`; no tuning afterwards)
Pools: G3 (2 harm + null), G4 (2 + null), G5 (6 proxy modes + null), G6 (5 delay models + 3 nulls); seeds 900000+; label fraction {spec["frac"]}, delay 5 unless the world sets a delay model; {len(df):,} per-seed rows.

## Summary by arm
{md(mean_arm)}

## Power by world (seeds with a harmful step)
{md(pw)}

## Harm before alarm by world
{md(hb, "{:.1f}")}
""")
(
    D / "FINAL_VALIDITY_RESULTS.md"
).write_text(f"""# Final validity results (null worlds; false-alarm rate with Wilson 95% interval; **>alpha** = lower bound above 0.05)
{md(ci_tab(fa_n))}

False alarm before the first harmful step in harm worlds:

{md(ci_tab(fa_h))}

Empirical size is not a proof. Null classes where the guarantee does not apply (dependent outcomes: `C6|null|ar0.9_s1.3`, `C6|null|cluster120_s1.3`, G4 GARCH null) are expected to show inflation; the others should not.
""")
print(mean_arm.round(3).to_string())
print(st.round(4).to_string())
