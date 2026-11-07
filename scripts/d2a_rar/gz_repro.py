"""Gong & Zhang reproduction checks (own synthetic instances). Smoke/consistency only, not confirmatory evidence.

PYTHONPATH=src python scripts/d2a_rar/gz_repro.py phase   # free-budget phase transition (T=2000, |A|=3, |Pi|=10, c=.3)
PYTHONPATH=src python scripts/d2a_rar/gz_repro.py table2  # Alg 3 at d=10, |A|=5, T=10000, c=.5 (paper Table 2: 2899.75 +- 48.80)
"""

import sys

import numpy as np

from shiftlab.sota.gong_zhang import (
    LinearPolicyGame,
    MetaController,
    OracleEfficientPaid,
    PaidExp4,
    run_paid,
)
from shiftlab.sota.gong_zhang.core import free_budget_threshold


def phase():
    T, A, P, c = 2000, 3, 10, 0.3
    print("threshold", free_budget_threshold(c, A, P, T))
    for form in ("printed", "balanced"):
        print(form)
        for B in (0, 100, 300, 1000, 2000, 3000, 6000):
            R = []
            for s in range(6):
                g = LinearPolicyGame(T, 4, A, P, seed=s, cost_range=(c, c), bias=0.3)
                rng = np.random.default_rng(100 + s)
                alg = (
                    PaidExp4(A, P, T, mode="free_II", B=0, c=c, rng=rng)
                    if B == 0
                    else MetaController(A, P, T, B, c, eta_form=form, rng=rng)
                )
                r = run_paid(g, alg, rng)
                R.append((r["regret"], r["learning"], r["obs_cost"]))
            print(B, getattr(alg, "mode", None), np.round(np.mean(R, 0), 1))


def table2():
    d, A, T, c = 10, 5, 10000, 0.5
    res = []
    for rep in range(5):
        rng = np.random.default_rng(rep)
        W = rng.normal(size=(A, d))
        X = rng.normal(size=(T, d))
        X /= np.linalg.norm(X, axis=1, keepdims=True)
        mu = X @ W.T
        alg = OracleEfficientPaid(A, d, T)
        loss = paid = 0.0
        for t in range(T):
            out = alg.step(X[t], np.full(A, c), rng)
            loss += mu[t, out.action]
            paid += out.paid
            alg.update(out, mu[t] + rng.normal(size=A))
        res.append((loss - mu.min(1).sum() + paid, loss - mu.min(1).sum(), paid))
        print(rep, np.round(res[-1], 1), flush=True)
    r = np.array(res)
    print("mean", r.mean(0), "sd(total)", r[:, 0].std(ddof=1))


if __name__ == "__main__":
    {"phase": phase, "table2": table2}[sys.argv[1]]()
