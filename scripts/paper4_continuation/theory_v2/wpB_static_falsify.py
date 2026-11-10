"""WP B: static-alternative (t01 = t10 = 0) falsification at larger sizes, count-based DP (wpB_static).

All lambda >= 0 Lagrangian hull vertices are found by parametric DP; at an interior lambda of each
vertex range the DP-optimal plan (two tie-breaks) is tested for z-monotonicity. Any vertex where both
fail is flagged as a U2 candidate. Emphasis on c > 0 (endogenous query timing), the open case.
usage: wpB_static_falsify.py OUT.json SEED SECONDS TMAX BMAX
"""

from __future__ import annotations

import random
import sys
import time

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import save_refuse_overwrite  # noqa: E402
from wpB_static import rc_static, static_solve, z_monotone_static  # noqa: E402


def point(cell, lam, tie):
    T, B, d, e0, e1, p, c, k = cell
    J, plan, _ = static_solve(T, B, d, e0, e1, c, k, 1 - p, lam, p, tie=tie)
    R = float(rc_static(plan, T, B, d, e0, e1, 1 - p, p, exact=False))
    return J, R, J - lam * R, plan


def hull(cell, lam_max=1e4, tol=1e-10):
    J0, R0, C0, _ = point(cell, 0.0, "cont")
    Jm, Rm, Cm, _ = point(cell, lam_max, "cont")
    bps = []

    def rec(a, b):
        if a[1] - b[1] <= 1e-13:
            return
        lam = (b[2] - a[2]) / (a[1] - b[1])
        J, R, C, _ = point(cell, lam, "cont")
        if J < a[2] + lam * a[1] - tol * (1 + abs(J)):
            m = (lam, R, C)
            rec(a, m)
            rec(m, b)
        else:
            bps.append(lam)

    rec((0.0, R0, C0), (lam_max, Rm, Cm))
    edges = [0.0] + sorted(bps) + [lam_max]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def main():
    out, seed, secs = sys.argv[1], int(sys.argv[2]), float(sys.argv[3])
    tmax, bmax = int(sys.argv[4]), int(sys.argv[5])
    rng = random.Random(seed)
    t0 = time.time()
    ncell = nvert = 0
    flagged = []
    while time.time() - t0 < secs:
        T = rng.randint(3, tmax)
        B = rng.randint(2, min(bmax, T))
        d = rng.choice([1, 1, 2, 3])
        e0 = rng.choice([0.001, 0.01, 0.1, 0.3, 0.45, 0.49])
        e1 = rng.choice([0.51, 0.55, 0.7, 0.9, 0.99, 0.999])
        p = rng.choice([0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99])
        c = rng.choice([1e-4, 1e-3, 0.01, 0.03, 0.1, 0.3])
        k = rng.choice([0, 1e-3, 0.01, 0.1, 0.5, 2.0])
        cell = (T, B, d, e0, e1, p, c, k)
        for lo, hi in hull(cell):
            lam = (lo + hi) / 2 if hi < 1e4 else lo + 1.0
            oks = [z_monotone_static(point(cell, lam, tie)[3], T, B, d)[0] for tie in ("cont", "promote")]
            nvert += 1
            if not any(oks):
                flagged.append({"cell": cell, "lam": lam})
        ncell += 1
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB_static_falsify.py", "seed": seed,
               "Tmax": tmax, "Bmax": bmax, "seconds": time.time() - t0, "n_cells": ncell,
               "n_vertices": nvert, "n_flagged": len(flagged), "flagged": flagged[:50]}
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "flagged"}, flagged[:5])


if __name__ == "__main__":
    main()
