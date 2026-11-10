"""EXPLORATORY/EXPOSED c4 real-stream inversion analysis (proxies from ex-post episode gain; no causal truth)."""

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from analyze_inversions import inversions, pooled, COMP  # noqa

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper3/atlas"
CORE = [
    "gated_mope",
    "discern_fixed",
    "smcs_retain",
    "cusum",
    "cusum_cal",
    "page_hinkley",
    "edetector",
    "edetector_cal",
    "wald_econ",
    "thinned_iid",
    "markov_skeleton",
    "iid_gate",
]
df = pd.concat([pd.read_json(f, lines=True) for f in glob.glob(str(OUT / "real/*.jsonl"))])
df["good"] = df.sumD >= 20  # challenger ex-post better by >=1% of T
df["bad"] = df.sumD <= -20
df["edd_p"] = np.where(df.ever_prom == 1, df.first_prom, 2000)


def table(d, streams):
    rows = []
    for s in streams:
        x = d[d.stream == s]
        for m in CORE:
            y = x[x.method == m]
            gd, bd = y[y.good], y[y.bad]
            if len(gd) < 3 or len(bd) < 3:
                continue
            rows.append(
                dict(
                    cell=s,
                    method=m,
                    J=y.J.mean(),
                    edd=gd.edd_p.mean(),
                    missed=1 - gd.ever_prom.mean(),
                    fa=bd.ever_prom.mean(),
                    **{c: 0.0 for c in COMP},
                )
            )
    return pd.DataFrame(rows)


streams = sorted(df.stream.unique())
tab = table(df, streams)
keep = tab.groupby("cell").method.count()
tab = tab[tab.cell.isin(keep[keep == len(CORE)].index)]
inv = inversions(tab)
pt = pooled(inv)
rng = np.random.default_rng(0)
bs = []
for _ in range(200):
    parts = []
    for s in tab.cell.unique():
        x = df[df.stream == s]
        eps = x.ep.unique()
        pick = rng.choice(eps, len(eps))
        w = pd.Series(pick).value_counts()
        parts.append(x[x.ep.isin(w.index)].assign(w=lambda z: z.ep.map(w)))  # noqa: B023 (lambda applied immediately)
    b = pd.concat(parts)
    rows = []
    for s in tab.cell.unique():
        for m in CORE:
            y = b[(b.stream == s) & (b.method == m)]
            gd, bd = y[y.good], y[y.bad]
            if len(gd) < 1 or len(bd) < 1:
                continue
            rows.append(
                {
                    "cell": s,
                    "method": m,
                    "J": np.average(y.J, weights=y.w),
                    "edd": np.average(gd.edd_p, weights=gd.w),
                    "missed": 1 - np.average(gd.ever_prom, weights=gd.w),
                    "fa": np.average(bd.ever_prom, weights=bd.w),
                }
            )
    t = pd.DataFrame(rows)
    ok = t.groupby("cell").method.count()
    t = t[t.cell.isin(ok[ok == len(CORE)].index)]
    bs.append(pooled(inversions(t)))
bs = pd.DataFrame(bs)
ci = {k: [float(bs[k].quantile(0.025)), float(bs[k].quantile(0.975))] for k in bs.columns}
nv = df[df.method == "never_switch"].groupby("stream").J.mean()
res = {
    "n_streams": int(tab.cell.nunique()),
    "n_streams_total": len(streams),
    "pooled": pt,
    "ci": ci,
    "mean_J": tab.groupby("method")[["J", "edd", "fa", "missed"]].mean().round(3).to_dict("index"),
    "never_switch_J": float(nv.loc[tab.cell.unique()].mean()),
    "repair_J": df[
        df.method.isin(
            [
                "c1_gapaware",
                "c1c3",
                "c3_spaced_iid",
                "markov_skeleton",
                "thinned_iid",
                "gated_mope",
                "never_switch",
            ]
        )
    ]
    .groupby("method")
    .J.mean()
    .round(2)
    .to_dict(),
    "repair_prom": df[
        df.method.isin(
            ["c1_gapaware", "c1c3", "c3_spaced_iid", "markov_skeleton", "thinned_iid", "gated_mope"]
        )
    ]
    .groupby("method")
    .ever_prom.mean()
    .round(3)
    .to_dict(),
}
(OUT / "real_results.json").write_text(json.dumps(res, indent=1, default=float))
print(json.dumps(res, indent=1, default=float))
