"""Check (c): Theorem 2 (dyadic breakpoints) in exact rational arithmetic, at EXACT beliefs (no belief grid).

For every reachable (t, beta, n), W(t, beta, n, .) is built as an exact piecewise-linear function:
  C_N = pos + W(t+1, prop beta, n, .)                                   (exact vertex list)
  C_Q(w') = pos + c + min{ sum_y P(y) W(t+1, beta_y, n-1, w_y) : constraint }   evaluated EXACTLY at any
          rational w' by enumerating all vertices of the 2-D polygon arrangement (independent of the
          slope-merging argument of the proof).
  Theorem 2 predicts C_Q linear on every dyadic cell [k/2^n, (k+1)/2^n]. Because C_Q is convex, it is
  linear on a cell iff its value at an interior point equals the chord; we test at 1/3, 1/2 and 2/3 of
  every cell (exact equality).  If that holds, C_Q is known exactly as a PL function.
  f = min(C_N, C_Q) on [0,1) with f(1) = min(C_N(1), C_Q(1), P) and W = lower convex hull of f, exact.
  We record every hull vertex not in D_n (violations of Theorem 2) and every failed chord test.
Also returns the exact root value W(1, beta_1, B, alpha) for comparison with the LP and RB-DP.
"""
from __future__ import annotations

import bisect
import json
import random
import sys
import time
from fractions import Fraction as F
from functools import lru_cache

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import Cell, post_value_fn  # noqa: E402


def ev(V, x):
    xs = [v[0] for v in V]
    i = bisect.bisect_right(xs, x) - 1
    if i >= len(V) - 1:
        return V[-1][1]
    (x0, y0), (x1, y1) = V[i], V[i + 1]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def lower_hull(pts):
    pts = sorted(pts)
    # collapse equal x keeping min
    dd = {}
    for x, y in pts:
        dd[x] = min(y, dd.get(x, y))
    pts = sorted(dd.items())
    h = []
    for p in pts:
        while len(h) >= 2:
            (x1, y1), (x2, y2) = h[-2], h[-1]
            # remove h[-1] if it is on or above segment h[-2] -> p
            if (y2 - y1) * (p[0] - x1) >= (p[1] - y1) * (x2 - x1):
                h.pop()
            else:
                break
        h.append(p)
    return h


def run(cell: Cell, mode: str, checks: dict):
    Vpost, P = post_value_fn(cell)

    @lru_cache(maxsize=None)
    def W(t: int, b: F, n: int):
        if t > cell.T:
            return ((F(0), F(0)), (F(1), F(0)))
        p = cell.pos(b)
        WN = W(t + 1, cell.prop(b), n)
        CN = [(x, y + p) for x, y in WN]
        D = 2**n
        lattice = [F(k, D) for k in range(D + 1)]
        xs = set(x for x, _ in CN) | set(lattice)
        CQ = None
        if n:
            g = []
            for y, py in ((0, 1 - p), (1, p)):
                Wy = W(t + 1, cell.prop(cell.post(b, y)), n - 1)
                g.append([(x, py * v) for x, v in Wy])
            X0 = [x for x, _ in g[0]]
            X1 = [x for x, _ in g[1]]

            def cq(w):
                best = None
                s = 2 * w
                cand = set()
                a_list = X0 + ([w] if mode == "causal" else []) + [F(0), F(1)]
                b_list = X1 + [F(0), F(1)]
                for a in a_list:
                    for bb in b_list:
                        cand.add((a, bb))
                    cand.add((a, s - a))
                for bb in b_list:
                    cand.add((s - bb, bb))
                for a, bb in cand:
                    if not (0 <= a <= 1 and 0 <= bb <= 1 and a + bb <= s):
                        continue
                    if mode == "causal" and a > w:
                        continue
                    v = ev(g[0], a) + ev(g[1], bb)
                    if best is None or v < best:
                        best = v
                return best + p + cell.c

            vals = {x: cq(x) for x in lattice}
            for k in range(D):
                lo, hi = lattice[k], lattice[k + 1]
                for fr in (F(1, 3), F(1, 2), F(2, 3)):
                    x = lo + fr * (hi - lo)
                    chord = vals[lo] + fr * (vals[hi] - vals[lo])
                    checks["chord_tests"] += 1
                    if cq(x) != chord:
                        checks["chord_fail"].append((t, str(b), n, str(x), float(cq(x) - chord)))
            CQ = [(x, vals[x]) for x in lattice]
        # f on [0,1): min of two PL functions; collect candidate points incl. crossings
        xs = sorted(xs)
        pts = []
        for i, x in enumerate(xs):
            yN = ev(CN, x)
            y = yN if CQ is None else min(yN, ev(CQ, x))
            if x == 1:
                y = min(y, P(t, n, b))
            pts.append((x, y))
            if CQ is not None and i + 1 < len(xs):
                x2 = xs[i + 1]
                d1 = ev(CN, x) - ev(CQ, x)
                d2 = ev(CN, x2) - ev(CQ, x2)
                if d1 * d2 < 0:
                    xc = x + (x2 - x) * d1 / (d1 - d2)
                    pts.append((xc, ev(CN, xc)))
                    checks["crossings"] += 1
        H = lower_hull(pts)
        checks["rows"] += 1
        for x, _ in H:
            if (x * D).denominator != 1:
                checks["offlattice_vertices"].append((t, str(b), n, str(x)))
        # sanity: convex and nonincreasing
        for (x0, y0), (x1, y1) in zip(H, H[1:]):
            if y1 > y0:
                checks["increasing"] += 1
        return tuple(H)

    root = W(1, cell.beta1, cell.B)
    return ev(root, cell.alpha), root


def rand_cell(rng):
    anti = rng.random() < 0.6
    lo, hi = (11, 19) if anti else (1, 19)
    num = lambda a, b, d: F(rng.randint(a, b), d)  # noqa: E731
    return Cell(
        T=rng.randint(3, 7), B=rng.randint(1, 3),
        t01=num(lo, hi, 20), t10=num(lo, hi, 20), e0=num(1, 9, 20), e1=num(11, 19, 20),
        prior=rng.choice([F(0), F(1, 3), F(1, 2), F(2, 7)]),
        c=rng.choice([F(0), F(1, 100), F(1, 30)]), k=rng.choice([F(0), F(1, 20), F(1, 7)]),
        alpha=rng.choice([F(1, 10), F(1, 7), F(3, 20), F(1, 3), F(2, 9), F(1, 20)]),
    )


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    from check_b_lp import CELLS

    out = {"fixed": {}, "random": []}
    for name, cell in CELLS.items():
        for mode in ("causal", "iid"):
            checks = {"rows": 0, "chord_tests": 0, "chord_fail": [], "offlattice_vertices": [],
                      "crossings": 0, "increasing": 0}
            v, _ = run(cell, mode, checks)
            out["fixed"][f"{name}/{mode}"] = {"V_exact": str(v), "V_float": float(v), **{
                k: (len(x) if isinstance(x, list) else x) for k, x in checks.items()}}
            print(name, mode, float(v), {k: (len(x) if isinstance(x, list) else x) for k, x in checks.items()})
    rng = random.Random(4242)
    tot = {"rows": 0, "chord_tests": 0, "chord_fail": 0, "offlattice_vertices": 0, "crossings": 0,
           "increasing": 0}
    t0 = time.time()
    for i in range(60):
        cell = rand_cell(rng)
        for mode in ("causal", "iid"):
            checks = {"rows": 0, "chord_tests": 0, "chord_fail": [], "offlattice_vertices": [],
                      "crossings": 0, "increasing": 0}
            v, _ = run(cell, mode, checks)
            rec = {"cell": {k: str(getattr(cell, k)) for k in cell.__dataclass_fields__}, "mode": mode,
                   "V_exact": str(v), **{k: (x if not isinstance(x, list) else x[:5]) for k, x in checks.items()}}
            out["random"].append(rec)
            for k in tot:
                x = checks[k]
                tot[k] += len(x) if isinstance(x, list) else x
            if checks["chord_fail"] or checks["offlattice_vertices"]:
                print("VIOLATION", rec)
    print("random cells: 60 x 2 modes", tot, f"{time.time() - t0:.1f}s")
    out["random_totals"] = tot
    with open(__file__.rsplit("/", 1)[0] + "/check_c_results.json", "w") as fh:
        json.dump(out, fh, indent=1, default=str)
