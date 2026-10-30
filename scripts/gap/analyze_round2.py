"""Round-2 confirmation: nominal-fraction paired tests (Holm) + label-matched gains against the uniform curve."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

O = Path("outputs/gap_closure")
D = Path("docs/sota_gap_closure")
spec = json.loads(Path("configs/gap_closure/frozen_confirmation_v2.json").read_text())
r2 = pd.read_parquet(O / "e15b_confirm_round2/perseed.parquet")
cv = pd.read_parquet(O / "e15c_curve/perseed.parquet")
df = pd.concat([r2, cv], ignore_index=True)
df["has"] = df.first_harm < df["T"]
wk = df.groupby("world").has.mean()
harm_w = list(wk[wk > 0.5].index)
null_w = [w for w in wk.index if w not in harm_w]
scope_null = [w for w in null_w if not any(k in w for k in ("ar0.9", "cluster120", "fin_null"))]
rng = np.random.default_rng(7)


def md(d, ff="{:.3f}"):
    d = d.reset_index()
    out = [
        "| " + " | ".join(map(str, d.columns)) + " |",
        "|" + "|".join("---" for _ in d.columns) + "|",
    ]
    for _, r in d.iterrows():
        out.append(
            "| "
            + " | ".join(
                ff.format(v) if isinstance(v, float | np.floating) and not pd.isna(v) else str(v)
                for v in r
            )
            + " |"
        )
    return "\n".join(out)


def stats(c):
    x = df[df.config == c]
    h = x[x.world.isin(harm_w)]
    p = h[h.has].groupby("world").detected.mean().mean()
    return {
        "power": p,
        "labels": h.labels.mean(),
        "harm_before": h.harm_before.mean(),
        "FA_in_scope_null_max": x[x.world.isin(scope_null)]
        .groupby("world")
        .false_alarm.mean()
        .max(),
        "FA_dependence_nulls_max": x[x.world.isin(null_w) & ~x.world.isin(scope_null)]
        .groupby("world")
        .false_alarm.mean()
        .max(),
    }


tab = pd.DataFrame(
    {c: stats(c) for c in sorted(df.config.unique()) if not c.startswith(("ph", "cusum"))}
).T
u = tab[tab.index.str.startswith(("HGu@", "HG@", "HG_hardcap@"))]
u = u.sort_values("labels")
tab["uniform_power_at_same_labels"] = np.interp(tab.labels, u.labels, u.power)
tab["label_matched_gain"] = tab.power - tab.uniform_power_at_same_labels


def paired(a, b):
    ds = []
    for wd in harm_w:
        x = df[(df.world == wd) & (df.config == a)].sort_values("seed")
        y = df[(df.world == wd) & (df.config == b)].sort_values("seed")
        m = x.has.values
        ds.append((x.detected.values.astype(float) - y.detected.values.astype(float))[m])
    obs = np.mean([d.mean() for d in ds])
    bs = np.array(
        [
            np.mean(
                [
                    ds[i][rng.integers(0, len(ds[i]), len(ds[i]))].mean()
                    for i in rng.integers(0, len(ds), len(ds))
                ]
            )
            for _ in range(3000)
        ]
    )
    return (
        obs,
        np.quantile(bs, 0.025),
        np.quantile(bs, 0.975),
        max(2 * min((bs <= 0).mean(), (bs >= 0).mean()), 1 / 3000),
    )


rows = []
for f in spec["fracs"]:
    for a, b in spec["primary_comparisons"]:
        o, lo, hi, p = paired(f"{a}@{f}", f"{b}@{f}")
        la = (
            df[(df.config == f"{a}@{f}") & df.world.isin(harm_w)].labels.mean()
            - df[(df.config == f"{b}@{f}") & df.world.isin(harm_w)].labels.mean()
        )
        rows.append(
            {
                "A": a,
                "B": b,
                "frac": f,
                "power A-B": o,
                "ci_lo": lo,
                "ci_hi": hi,
                "p_raw": p,
                "extra labels A-B": la,
            }
        )
st = pd.DataFrame(rows)
m = len(st)
order = st.p_raw.argsort().values
holm = np.empty(m)
run = 0.0
for rank, idx in enumerate(order):
    run = max(run, min(1.0, (m - rank) * st.p_raw.values[idx]))
    holm[idx] = run
st["p_holm"] = holm
cand = tab[tab.index.str.contains("floor|pace|robustmix")].index
txt = f"""# Final confirmation, round 2 (corrected-floor candidates; frozen in `frozen_confirmation_v2.json` before running; fresh seeds 1,100,000+)
Same confirmation pool parameters as round 1 ({len(harm_w)} harm worlds, {len(null_w)} null worlds, 400 / 1000 seeds). Uniform power-vs-labels curve: HG at nominal fractions .08 .10 .12 .16 .20 .25 .30 (same seeds) and the hard-capped HG arm. `label_matched_gain` = arm power minus the curve interpolated at the arm's realised labels (linear; the uniform curve is concave in this range, so linear interpolation slightly *overstates* the uniform comparator, i.e. is conservative for the candidates).

## Summary per arm (power over harm worlds, equally weighted)
{md(tab.round(4))}

## Primary paired comparisons at the same NOMINAL fraction (cluster bootstrap over worlds then seeds; Holm over {m} comparisons)
{md(st, "{:.4f}")}

A comparison counts as a label-efficiency gain only if the label-matched gain is >= +0.03 (the registered practical threshold) as well. In-scope null false alarm (columns `FA_in_scope_null_max`) must stay <= 0.07; dependent nulls are reported separately and are expected to be inflated.
"""
(D / "FINAL_CONFIRMATION_ROUND2_RESULTS.md").write_text(txt)
st.to_csv(O / "e15b_confirm_round2/comparisons.csv", index=False)
tab.to_csv(O / "e15b_confirm_round2/arm_summary.csv")
print(tab.loc[sorted(cand)].round(3).to_string())
print(st.round(4).to_string())
