"""Exposed-real-stream development analysis (counts for nothing in C4).

Per stream: episode means (over policy seeds) of each arm; stream-equal pooled mean; for chosen
arms, pooled Δ vs a comparator with a stream bootstrap CI and per-stream sign counts.
usage: analyze_nm_real.py records.jsonl [comparator]
"""

import sys

import numpy as np
import pandas as pd


def main(path, comp=None):
    d = pd.read_json(path, lines=True)
    e = d.groupby(["stream", "ep", "policy"]).net.mean().unstack()
    s = e.groupby(level=0).mean()  # stream x policy
    pooled = s.mean().sort_values()
    W = [c for c in pooled.index if c.startswith("wald_")]
    comp = comp or pooled[W].idxmin()
    print(f"streams={len(s)} comparator={comp} pooled={pooled[comp]:.2f}")
    print(pooled.head(30).round(2).to_string())
    rng = np.random.default_rng(0)
    rows = []
    for a in pooled.index:
        if a == comp:
            continue
        dd = (s[a] - s[comp]).to_numpy()
        bs = [dd[rng.integers(0, len(dd), len(dd))].mean() for _ in range(2000)]
        big = (e.groupby(level=0).size() >= 5).reindex(s.index).to_numpy()
        rows.append(
            (
                a,
                dd.mean(),
                *np.percentile(bs, [2.5, 97.5]),
                int((dd < 0).sum()),
                int((dd[big] < 0).sum()),
                int(big.sum()),
            )
        )
    r = pd.DataFrame(rows, columns=["arm", "d", "lo", "hi", "neg", "neg_big", "n_big"])
    print(r.sort_values("d").round(2).to_string(index=False))
    return s, comp


if __name__ == "__main__":
    s, comp = main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    cols = [
        comp,
        "dep_l0.9_g0.15_lr0.99_rp5.0",
        "dep_l0.9_g0.15_lr0.97_rp5.0",
        "wald_l0.97_g0.15",
        "sgr_l0.9_g0.15_W150_z2.5_L20",
        "bocpd_h0.01_g0.1",
        "gongT_w100_m10",
        "CONTROL_never_switch",
    ]
    print(s[[c for c in cols if c in s]].round(1).to_string())
