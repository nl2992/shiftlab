"""Cumulative C4 analysis over registered batches (c4_amendment_A2.md).

usage: analyze_c4_batches.py REG1.json:RECORDS1.jsonl [REG2.json:RECORDS2.jsonl ...]
Applies the locked per-dataset rule of analyze_c4_confirm.py to each batch and reports the
cumulative X/N, the binomial count bound P(X >= x | N, p=.05), the sign test and the pooled
secondary vs the Qiu-style adapter.
"""

import json
import sys

import numpy as np
import pandas as pd
from scipy import stats

ARM, PRIMARY, SECONDARY = "EQSDp_l0.9_g0.2", "gongT_w100_m10", "qiu_delayed_movement"


def batch(reg_path, rec_path, label):
    with open(reg_path) as fh:
        reg = {d["name"]: d for d in json.load(fh)["datasets"]}
    d = pd.read_json(rec_path, lines=True)
    e = d.groupby(["stream", "ep", "policy"]).net.mean().unstack()
    rng = np.random.default_rng(0)  # same resampling stream as the locked batch-1 script
    rows = []
    for name in reg:
        x = e.loc[name]
        dl = (x[ARM] - x[PRIMARY]).to_numpy()
        bs = np.array([dl[rng.integers(0, len(dl), len(dl))].mean() for _ in range(2000)])
        ub = float(np.percentile(bs, 95))
        rows.append(
            {
                "batch": label,
                "dataset": name,
                "org": reg[name]["org"],
                "city": reg[name]["city"],
                "episodes": len(dl),
                "delta_primary": dl.mean(),
                "ub95": ub,
                "supports": ub < 0,
                "delta_secondary": float((x[ARM] - x[SECONDARY]).mean()),
            }
        )
    return rows


def main(pairs):
    rows = []
    for k, p in enumerate(pairs, 1):
        reg, rec = p.rsplit(":", 1) if p.count(":") > 1 else p.split(":")
        rows += batch(reg, rec, k)
    r = pd.DataFrame(rows)
    print(r.round(3).to_string(index=False))
    for k, g in r.groupby("batch"):
        x, n = int(g.supports.sum()), len(g)
        print(
            f"batch {k}: {x}/{n} supporting; binomial P(X>={x}|N={n},.05)={stats.binom.sf(x - 1, n, 0.05):.3g}"
        )
    sup = r[r.supports]
    x, n = sup.org.nunique(), len(r)
    neg = int((r.delta_primary < 0).sum())
    print(
        f"\nCUMULATIVE: {x}/{n} supporting (distinct orgs); one-per-city: {sup.drop_duplicates('city').shape[0]}"
    )
    print(f"binomial count bound P(X>={x}|N={n}, p=.05) = {stats.binom.sf(x - 1, n, 0.05):.3g}")
    print(
        f"sign test: {neg}/{n} negative, one-sided p={stats.binomtest(neg, n, 0.5, alternative='greater').pvalue:.3g}"
    )
    t = stats.ttest_1samp(r.delta_secondary, 0.0, alternative="less")
    print(
        f"pooled secondary vs Qiu-style: mean {r.delta_secondary.mean():+.2f}, one-sided p={t.pvalue:.3g}"
    )
    print("TARGET (>=8 supporting):", "REACHED" if x >= 8 else "NOT REACHED")


if __name__ == "__main__":
    main(sys.argv[1:])
