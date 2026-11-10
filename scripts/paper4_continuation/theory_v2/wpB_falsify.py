"""WP B targeted falsification: Lagrangian hull vertices of the pure-plan (R_IID, C) set, by
parametric DP (wpB_lib.solve), and z-monotonicity of the DP-optimal plan at each vertex.

For each random cell of a family, all lambda >= 0 hull vertices are found (Eisner-Severance on the
concave dual function J(lambda)); at an interior lambda of each vertex's range every optimal plan
has that (R, C), so a vertex where some optimal plan is z-monotone certifies U2 there. The DP plan is
checked under two tie-breaks (prefer continue / prefer promote). A vertex where neither is
z-monotone is flagged 'U2-candidate' (not yet a failure: other optimal plans may exist); flagged
cells are re-examined exactly elsewhere.

usage: wpB_falsify.py OUT.json FAMILY SEED SECONDS [TMAX BMAX]   (defaults 9, 4)
FAMILY: static | sym | tp2m (TP2 + M_marg) | tp2any (TP2, no M) | antip (t01+t10>1, control)
"""

from __future__ import annotations

import random
import sys
import time

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import save_refuse_overwrite  # noqa: E402
from wpB_lib import Model, risk_of, solve, z_monotone  # noqa: E402


def marg_ok(t01, t10, e0, e1, prior, T, d):
    p = prior * (1 - t10) + (1 - prior) * t01
    for _t in range(1, T - d + 1):
        if e0 + (e1 - e0) * p < 0.5 - 1e-12:
            return False
        p = p * (1 - t10) + (1 - p) * t01
    return True


TMAX, BMAX = 9, 4


def draw(rng, family):
    T = rng.randint(3, TMAX)
    B = rng.randint(2, min(BMAX, T))
    d = rng.choice([1, 1, 2, 3])
    c = rng.choice([0, 0, 1e-4, 1e-3, 0.01, 0.05])
    k = rng.choice([0, 1e-3, 0.01, 0.05, 0.2, 0.5, 1.0])
    if family == "static":
        t01 = t10 = 0.0
        e0 = rng.choice([0.01, 0.1, 0.3, 0.45, 0.49])
        e1 = rng.choice([0.51, 0.55, 0.7, 0.9, 0.99])
        prior = rng.choice([0.02, 0.2, 0.5, 0.8, 0.98])
    elif family == "sym":
        t01 = t10 = rng.choice([0.001, 0.01, 0.05, 0.1, 0.25, 0.4, 0.49, 0.5])
        e1 = rng.choice([0.51, 0.55, 0.6, 0.75, 0.9, 0.99, 0.999])
        e0, prior = 1 - e1, 0.5
    else:
        while True:
            t01, t10 = rng.choice([0, 0.01, 0.05, 0.1, 0.25, 0.4, 0.5, 0.7, 0.9]), rng.choice([0, 0.01, 0.05, 0.1, 0.25, 0.4, 0.5, 0.7, 0.9])
            e0 = rng.choice([0.01, 0.1, 0.25, 0.4, 0.49])
            e1 = rng.choice([0.51, 0.6, 0.75, 0.9, 0.99])
            prior = rng.choice([0, 0.1, 0.3, 0.5, 0.7, 0.9, 1])
            tp2 = t01 + t10 <= 1
            if family == "antip" and not tp2:
                break
            if family == "tp2any" and tp2:
                break
            if family == "tp2m" and tp2 and marg_ok(t01, t10, e0, e1, prior, T, d):
                break
    return T, B, d, t01, t10, e0, e1, prior, c, k


def point(model, lam, tie):
    J, plan, _ = solve(model, lam, tie=tie)
    R = float(risk_of(plan, model))
    return J, R, J - lam * R, plan


def hull(model, lam_max=1e4, tol=1e-10):
    """Return list of (lam_lo, lam_hi) ranges, one per hull vertex (R decreasing)."""
    J0, R0, C0, _ = point(model, 0.0, "cont")
    Jm, Rm, Cm, _ = point(model, lam_max, "cont")
    verts = {}

    def rec(a, b):  # a=(lam,R,C) high R; b low R
        if a[1] - b[1] <= 1e-13:
            return
        lam = (b[2] - a[2]) / (a[1] - b[1])
        J, R, C, _ = point(model, lam, "cont")
        if J < a[2] + lam * a[1] - tol * (1 + abs(J)):
            m = (lam, R, C)
            rec(a, m)
            rec(m, b)
        else:
            verts[(a[1], b[1])] = lam

    rec((0.0, R0, C0), (lam_max, Rm, Cm))
    bps = sorted(verts.values())
    edges = [0.0] + bps + [lam_max]
    return [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]


def main():
    global TMAX, BMAX
    out, family, seed, secs = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
    if len(sys.argv) > 6:
        TMAX, BMAX = int(sys.argv[5]), int(sys.argv[6])
    rng = random.Random(seed)
    t0 = time.time()
    rows, nvert, flagged = [], 0, []
    while time.time() - t0 < secs:
        cell = draw(rng, family)
        model = Model(*cell)
        ranges = hull(model)
        cell_flags = []
        for lo, hi in ranges:
            lam = (lo + hi) / 2 if hi < 1e4 else lo + 1.0
            oks = []
            for tie in ("cont", "promote"):
                _, R, C, plan = point(model, lam, tie)
                ok, wit = z_monotone(plan, model)
                oks.append(ok)
            nvert += 1
            if not any(oks):
                cell_flags.append({"lam": lam, "range": [lo, hi], "R": R, "C": C, "witness": str(wit)})
        rows.append({"cell": cell, "n_vertices": len(ranges), "flags": cell_flags})
        if cell_flags:
            flagged.append(rows[-1])
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB_falsify.py", "family": family,
               "seed": seed, "Tmax": TMAX, "Bmax": BMAX, "seconds": time.time() - t0, "n_cells": len(rows), "n_vertices": nvert,
               "n_flagged_cells": len(flagged), "flagged": flagged,
               "cells": [r["cell"] for r in rows]}
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k not in ("flagged", "cells")})
    for f in flagged[:10]:
        print("FLAG", f["cell"], f["flags"][:2])


if __name__ == "__main__":
    main()
