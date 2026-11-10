"""Independent audit checks for workstream B (MANUAL_FALLBACK)."""

import math

import numpy as np

from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.theory import gamma_lb, gamma_ub

print("== A. UB/LB ratio over a wider grid (pure drift, base=k/h+S) ==")
rows = []
for alpha in (0.2, 0.1, 0.05, 0.01, 0.001):
    for beta in (0.5, 0.2, 0.05, 0.01, 0.001):
        for v in (0, 1e-4, 1e-3, 1e-2):
            for B in (50, 200, 1000, 10000):
                for base in (0.0, 0.1, 0.3):
                    lb = gamma_lb(B, v, base, alpha, beta)
                    ub, n = gamma_ub(B, Envelope(v), alpha, beta)
                    feas = (ub + base < 1) and math.isfinite(lb)
                    rows.append(
                        (
                            alpha,
                            beta,
                            v,
                            B,
                            base,
                            lb,
                            ub,
                            ub / lb if math.isfinite(lb) and lb > 0 else math.nan,
                            feas,
                        )
                    )
fe = [r for r in rows if r[-1]]
rat = np.array([r[7] for r in fe])
print(
    "feasible cells",
    len(fe),
    "of",
    len(rows),
    "ratio min/median/max",
    rat.min(),
    np.median(rat),
    rat.max(),
)
for r in sorted(fe, key=lambda r: -r[7])[:6]:
    print("worst", r[:8])
b = [r for r in fe if r[1] == 0.2 and r[0] == 0.05]
print("alpha=.05,beta=.2 max ratio", max(r[7] for r in b))
b = [r for r in fe if r[1] <= 0.01]
print("beta<=.01 max ratio", max(r[7] for r in b))
b = [r for r in fe if r[4] == 0.3]
print("base=.3 max ratio", max(r[7] for r in b))
print("infeasible (UB needs L>1) fraction:", 1 - len(fe) / len(rows))
# the published B=6,10,14 rows
for B in (6, 10, 14):
    print(
        "B",
        B,
        "ub",
        gamma_ub(B, Envelope(0.0), 0.05, 0.2)[0],
        "base+ub>1?",
        gamma_ub(B, Envelope(0.0), 0.05, 0.2)[0] + 0.1 > 1,
    )

print("== B. T4 independent DP (Rademacher mean .1, Hoeffding-naive, any look <=M) ==")


def cross(M, alpha, mu0, rule):
    p = (1 + mu0) / 2  # S = sum Z, states integers -M..M ; absorbing on cross
    prob = {0: 1.0}
    hit = 0.0
    for m in range(1, M + 1):
        new = {}
        for s, pr in prob.items():
            for z, q in ((1, p), (-1, 1 - p)):
                new[s + z] = new.get(s + z, 0) + pr * q
        prob = {}
        for s, pr in new.items():
            if rule(m, s):
                hit += pr
            else:
                prob[s] = pr
    return hit


al = 0.05
hoef = lambda m, s: s / m - math.sqrt(2 * math.log(1 / al) / m) > 0.1 + 1e-12
for M in (10, 100, 300, 1000):
    print("M", M, cross(M, al, 0.1, hoef))
print(
    "single look m=100:",
    sum(0 for _ in []) or cross(100, al, 0.1, lambda m, s: m == 100 and hoef(m, s)),
)

print("== C. T1 clipping: unclipped null sum<=k but clipped>k? random search (pure drift) ==")
rng = np.random.default_rng(1)
bad = 0
for _ in range(200000):
    L = rng.uniform(-1, 1)
    v = 10 ** rng.uniform(-4, -0.5)
    d = int(rng.integers(1, 200))
    h = int(rng.integers(1, 300))
    k = rng.uniform(0, 5)
    a = d + np.arange(h)
    un = L - v * a
    cl = np.maximum(un, -1)
    if un.sum() <= k and cl.sum() > k:
        bad += 1
print("violations", bad)
# ledger clipping condition v(h-1)/2<=1+k/h does not prevent clipping:
v, d, h, k, L = 0.01, 300, 3, 0, 0.6
print(
    "ledger condition holds:", v * (h - 1) / 2 <= 1 + k / h, "but L-v(d+h-1) =", L - v * (d + h - 1)
)
