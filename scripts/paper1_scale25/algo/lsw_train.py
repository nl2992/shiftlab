# ruff: noqa
"""Fit the LSW ridge model on EVEN development episodes only (nine registered + fresh windows).

Behaviour policy: EQ+cut+E48+F60 (the v1 pair) with the LREC recorder, so the label stream resembles the
deployed acquisition. Target for a release at time t: fraction of challenger-correct outcomes among the
next W=300 disagreement events after t (evaluator-side arrays; used offline for fitting only).
Odd episodes are never read.
    python lsw_train.py [--per-ds 12] [--seeds 2]
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import s25_common as sc
import s25_modules as sm  # noqa: F401
from s25_v2 import LREC, LSW_FEATS, LSW_JSON

W = 300


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-ds", type=int, default=12)
    ap.add_argument("--seeds", type=int, default=2)
    a = ap.parse_args()
    import compositor as comp
    import trace_run as tr

    spec = {
        "name": "lrec_pair",
        "modules": [
            {"id": "E48", "setting": 0},
            {"id": "F60", "setting": 0},
            {"id": "LREC", "setting": 0},
        ],
    }
    comp.register_specs([spec])
    X, Y, meta = [], [], []
    for pool in ("nine", "fresh"):
        sl = sc.sealed(pool)
        for ds, (p, delay, sb) in sl.items():
            z = np.load(p)
            n = z["l0"].shape[0]
            even = list(range(0, n, 2))
            sel = even[:: max(1, len(even) // a.per_ds)][: a.per_ds]
            for ep in sel:
                l0, l1 = z["l0"][ep].astype(np.int8), z["l1"][ep].astype(np.int8)
                losses = np.stack([l0, l1], axis=1)
                dis = np.flatnonzero(l0 != l1)
                d = (l0.astype(int) - l1.astype(int))[
                    dis
                ] > 0  # challenger correct on disagreements
                for seed in range(a.seeds):
                    LREC.REC = []
                    tr.run_policies(["lrec_pair"], losses, delay, ep, seed, sb, ds, 200)
                    for r in LREC.REC:
                        j = np.searchsorted(dis, r["t"], side="right")
                        fut = d[j : j + W]
                        if len(fut) < 30:
                            continue
                        X.append(r["x"])
                        Y.append(float(fut.mean()))
                        meta.append((pool, ds, ep))
    LREC.REC = None
    X, Y = np.array(X), np.array(Y)
    lam = 1.0
    w = np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ Y)
    res = Y - X @ w
    # baseline for comparison: posterior mean alone
    base = Y - X[:, 0]
    par = {
        "features": LSW_FEATS,
        "w": w.tolist(),
        "sigma0": float(res.std()),
        "n_samples": len(Y),
        "mse_model": float((res**2).mean()),
        "mse_posterior_mean": float((base**2).mean()),
        "episodes_used": sorted({(m[0], m[1], m[2]) for m in meta}),
        "target_window": W,
        "procedure": "ridge(1.0) on even episodes only; behaviour EQ+cut+E48+F60; y = future "
        "challenger-correct fraction over next 300 disagreement events",
    }
    LSW_JSON.write_text(json.dumps(par, indent=1, default=str), encoding="utf-8")
    print({k: par[k] for k in ("w", "sigma0", "n_samples", "mse_model", "mse_posterior_mean")})


if __name__ == "__main__":
    main()
