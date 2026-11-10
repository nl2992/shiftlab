"""WP B: numerical audit of the static fixed-calendar proof (Theorem S-c0 in MULTILABEL_ZERO_PREMIUM.md).

Checks, on random static cells with the greedy calendar (queries at 1..B, c = 0):
 (1) the closed 1-D recursion for G_t(x) = D_t(x, 0) equals the exact DP (wpB_static) value;
 (2) the recursion D_t(x,y) = E_t(x) + sum_y L1_y D_{t+1}^+(x l_y, y l^N_y), E_t = G_t - sum L1 G_{t+1}^+,
     equals the exact DP value at y > 0;
 (3) D_t is nondecreasing in x and in y, and D_t - G_t is nondecreasing in x (the induction hypotheses),
     on a log grid of (x, y).
usage: wpB_static_proofcheck.py OUT.json SEED SECONDS
"""

from __future__ import annotations

import math
import random
import sys
import time
from functools import lru_cache

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import save_refuse_overwrite  # noqa: E402
from wpB_static import static_solve  # noqa: E402


def recursions(T, B, d, e0, e1, k):
    rel = {d + j for j in range(1, B + 1) if d + j <= T}

    def branches(t):
        return [(1 - e0, 0.5, 1 - e1), (e0, 0.5, e1)] if (t + 1) in rel else [(1.0, 1.0, 1.0)]

    @lru_cache(None)
    def G(t, x):
        if t == T:
            return x * (1 - 2 * e0 + k) + (1 - 2 * e1 + k)
        out = x * (1 - 2 * e0) + (1 - 2 * e1)
        for L0, _LN, L1 in branches(t):
            xl = x * L0 / L1
            out += L1 * min(max(G(t + 1, xl), 0.0), 2 * k * (1 + xl))
        return out

    @lru_cache(None)
    def D(t, x, y):
        if t == T:
            return y + G(T, x)
        E = G(t, x) - sum(L1 * max(G(t + 1, x * L0 / L1), 0.0) for L0, _LN, L1 in branches(t))
        return E + sum(L1 * max(D(t + 1, x * L0 / L1, y * LN / L1), 0.0) for L0, LN, L1 in branches(t))

    return G, D


def main():
    out, seed, secs = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    rng = random.Random(seed)
    t0 = time.time()
    n = err_g = err_d = 0
    mono_viol, gap_viol = [], []
    xs = [math.exp(u / 6) for u in range(-36, 37)]
    ys = [0.0] + [math.exp(u / 4) for u in range(-20, 21)]
    while time.time() - t0 < secs:
        T = rng.randint(2, 10)
        B = rng.randint(1, T)
        d = rng.randint(1, 3)
        e0 = rng.choice([0.001, 0.05, 0.2, 0.4, 0.49])
        e1 = rng.choice([0.51, 0.6, 0.8, 0.95, 0.999])
        k = rng.choice([0, 0.01, 0.05, 0.3, 1, 3])
        G, D = recursions(T, B, d, e0, e1, k)
        for _ in range(3):
            x, y = rng.choice(xs), rng.choice(ys)
            _, _, Dt = static_solve(T, B, d, e0, e1, 0, k, x, y, 1.0, greedy=True)
            ref = Dt[(1, (), B, 0, 0)]
            err_g = max(err_g, abs(static_solve(T, B, d, e0, e1, 0, k, x, 0.0, 1.0, greedy=True)[2][(1, (), B, 0, 0)] - G(1, x)))
            err_d = max(err_d, abs(ref - D(1, x, y)))
        for t in range(1, T + 1):
            grid = [[D(t, x, y) for y in ys] for x in xs]
            gx = [G(t, x) for x in xs]
            tol = 1e-9
            for i in range(len(xs)):
                for j in range(len(ys)):
                    if i and grid[i][j] < grid[i - 1][j] - tol * (1 + abs(grid[i][j])):
                        mono_viol.append((T, B, d, e0, e1, k, t, "x", xs[i], ys[j]))
                    if j and grid[i][j] < grid[i][j - 1] - tol * (1 + abs(grid[i][j])):
                        mono_viol.append((T, B, d, e0, e1, k, t, "y", xs[i], ys[j]))
                    if i and (grid[i][j] - gx[i]) < (grid[i - 1][j] - gx[i - 1]) - tol * (1 + abs(grid[i][j])):
                        gap_viol.append((T, B, d, e0, e1, k, t, xs[i], ys[j]))
        n += 1
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB_static_proofcheck.py", "seed": seed,
               "seconds": time.time() - t0, "n_cells": n, "max_err_G_recursion_vs_DP": err_g,
               "max_err_D_recursion_vs_DP": err_d, "n_monotonicity_violations": len(mono_viol),
               "n_gap_violations": len(gap_viol), "examples": (mono_viol + gap_viol)[:10]}
    save_refuse_overwrite(out, payload)
    print(payload)


if __name__ == "__main__":
    main()
