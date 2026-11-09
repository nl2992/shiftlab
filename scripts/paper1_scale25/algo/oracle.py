# ruff: noqa
"""Evaluator-side hindsight bounds per episode (use l0, l1 arrays; never visible to learners).

J_fix   = min(L0, L1)                         best fixed model, no switch fee (trace_run convention)
J_orcK  = min over <= K switches of  loss + cs * switches, starting on model 0 (initial incumbent),
          paying NO label fee (so it is a lower bound on any label-paying policy's J)
Switch times are free in hindsight; a switch before event t takes effect at event t.
K=1 is the "best single switch time in hindsight"; K=2,3 allow mid-episode regime returns.
All values are net cost per episode in pp of T (x100/T).
"""

from __future__ import annotations

import numpy as np
import s25_common as sc


def oracle_batch(l0, l1, cs=sc.CS, K=3):
    """l0, l1: (E, T) arrays. Returns dict of (E,) arrays."""
    E, T = l0.shape
    ll = (l0.astype(np.float64), l1.astype(np.float64))
    INF = 1e18
    f = np.full((2, K + 1, E), INF)
    f[0, 0] = 0.0
    f[1, 1] = cs  # start on model 1: one switch from the initial incumbent
    for t in range(T):
        if t > 0:
            g = f.copy()
            for m in (0, 1):
                g[m, 1:] = np.minimum(f[m, 1:], f[1 - m, :-1] + cs)
            f = g
        f[0] += ll[0][:, t]
        f[1] += ll[1][:, t]
    best = f.min(axis=0)  # (K+1, E): best over model with exactly-<= s switches (s index)
    out = {
        "J_fix": np.minimum(l0.sum(1), l1.sum(1)) / T * 100,
        "L0": l0.sum(1) / T * 100,
        "L1": l1.sum(1) / T * 100,
    }
    run = np.full(E, INF)
    for s in range(K + 1):
        run = np.minimum(run, best[s])
        if s >= 1:
            out[f"J_orc{s}"] = run / T * 100
    return out


def oracle_table(pool):
    import pandas as pd

    rows = []
    for ds, (p, _, _) in sc.sealed(pool).items():
        z = np.load(p)
        o = oracle_batch(z["l0"], z["l1"])
        df = pd.DataFrame(o)
        df.insert(0, "ep", np.arange(len(df)))
        df.insert(0, "stream", ds)
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


if __name__ == "__main__":
    for pool in ("nine", "fresh"):
        t = oracle_table(pool)
        t.to_csv(sc.OUT / f"oracle_{pool}.csv", index=False)
        print(pool, t.groupby("stream")[["J_fix", "J_orc1", "J_orc2", "J_orc3"]].mean().round(3))
