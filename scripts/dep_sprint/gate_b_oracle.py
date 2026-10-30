"""Oracle (known-parameter) likelihood-ratio power ceiling at T=2000 for the lazy-resample chain, null pi=r0 vs alt pi=r0+eps."""

import json
from pathlib import Path

import numpy as np

T, R0, ALPHA, S = 2000, 0.3, 0.05, 6000
rng = np.random.default_rng(11)


def sim(delta, pi, S, T):
    x = np.zeros((S, T), dtype=np.int8)
    cur = (rng.random(S) < pi).astype(np.int8)
    for t in range(T):
        sw = rng.random(S) < delta
        cur = np.where(sw, (rng.random(S) < pi).astype(np.int8), cur)
        x[:, t] = cur
    return x


def loglik(x, delta, pi):
    lp = np.log(np.where(x[:, 0] == 1, pi, 1 - pi))
    same = x[:, 1:] == x[:, :-1]
    fresh = np.where(x[:, 1:] == 1, pi, 1 - pi)
    return lp + np.log((1 - delta) * same + delta * fresh).sum(1)


out = {}
for eps in (0.05, 0.1):
    for tdelta in (0.2, 1, 5, 20, 100, 500):
        delta = tdelta / T
        x0, x1 = sim(delta, R0, S, T), sim(delta, R0 + eps, S, T)
        lr0 = loglik(x0, delta, R0 + eps) - loglik(x0, delta, R0)
        lr1 = loglik(x1, delta, R0 + eps) - loglik(x1, delta, R0)
        thr = np.quantile(lr0, 1 - ALPHA)
        out[f"eps={eps},T*delta={tdelta}"] = {
            "oracle_power": float((lr1 > thr).mean()),
            "coupling_ceiling": min(1.0, ALPHA + eps * (1 + tdelta)),
        }
        print(eps, tdelta, out[f"eps={eps},T*delta={tdelta}"], flush=True)
Path("outputs/dep_sprint/gate_b_oracle.json").write_text(json.dumps(out, indent=1))
