"""Direct test of the Lemma U premise by exhaustive pure-plan enumeration (exact rationals).

For a cell, enumerate every reachable pure pre-promotion plan, its exact alternative cost C (with the
decomposed game's optimal post-promotion continuation) and IID risk R.  The premise of Lemma R holds
(for M = z-monotone plans, Lemma Zc) iff every vertex of the lower convex hull of {(R, C)} on the
lambda >= 0 side is attained by a z-monotone plan.  Reports, per cell, the hull vertices, whether each
is attained by a z-monotone (and by a tape-monotone) plan, and the first failing vertex if any.
usage: fu_lagrangian_monotone.py OUT.json FAMILY   (FAMILY in {static, sympersist, mixed})
"""

from __future__ import annotations

import random
import sys
import time
from fractions import Fraction as F

from fu_zcoupling_check import monotone, plans, risks, run
from gamma_lib import make, save_refuse_overwrite
from shiftlab.paper4.frontier_cuts import exact_costs, learner_only_game


def plan_cost(game, costs, plan, T):
    total = F(0)
    for key, (a, q) in plan.items():
        _p, children, choices = game.learner.infos[key]
        total += costs[children[choices.index((a, q))]]
    return total


def lower_hull(points):
    """Vertices of the lower hull relevant to min C + lam R, lam >= 0 (from R-min to C-min)."""
    pts = sorted(set(points))
    hull = []
    for p in pts:
        while len(hull) >= 2:
            (x1, y1), (x2, y2) = hull[-2], hull[-1]
            if (y2 - y1) * (p[0] - x1) >= (p[1] - y1) * (x2 - x1):
                hull.pop()
            else:
                break
        hull.append(p)
    cmin = min(y for _, y in pts)
    out = []
    for p in hull:
        out.append(p)
        if p[1] == cmin:
            break
    return out


def check(T, B, d, t01, t10, e0, e1, prior, c, k):
    config, model = make(T, B, d, t01, t10, e0, e1, prior, c, k, F(1, 10))
    game = learner_only_game(config, model)
    costs = exact_costs(game)
    best_z, best_t, pts = {}, {}, []
    for plan in plans(T, B, d):
        if any(key not in game.learner.infos for key in plan):
            raise AssertionError("plan info not in learner tree")
        C = plan_cost(game, costs, plan, T)
        R, _ = risks(plan, T, d)
        pts.append((R, C))
        is_z = monotone(lambda z: run(plan, T, d, lambda t, j: z[j]), B)  # noqa: B023
        is_t = monotone(lambda y: run(plan, T, d, lambda t, j: y[t - 1]), T)  # noqa: B023
        if is_z:
            best_z[(R, C)] = True
        if is_t:
            best_t[(R, C)] = True
    hull = lower_hull(pts)
    fail_z = [v for v in hull if v not in best_z]
    fail_t = [v for v in hull if v not in best_t]
    return {"n_plans": len(pts), "hull": [[str(r), str(cst)] for r, cst in hull],
            "premise_z": not fail_z, "premise_tape": not fail_t,
            "fail_z": [[str(r), str(cst)] for r, cst in fail_z][:3]}


SHAPES = [(3, 2, 1), (3, 2, 2), (4, 2, 1), (4, 2, 2), (3, 3, 1)]


def main():
    out, family = sys.argv[1], sys.argv[2]
    rng = random.Random({"static": 41, "sympersist": 42, "mixed": 43}[family])
    started = time.time()
    rows = []
    while time.time() - started < 500 and len(rows) < 400:
        T, B, d = rng.choice(SHAPES)
        if family == "static":
            t01 = t10 = F(0)
            prior = rng.choice([F(1, 10), F(1, 4), F(1, 2), F(3, 4)])
            e0, e1 = rng.choice([F(1, 20), F(1, 10), F(1, 4), F(2, 5)]), rng.choice([F(11, 20), F(3, 5), F(3, 4), F(9, 10)])
        elif family == "sympersist":
            t01 = t10 = rng.choice([F(1, 20), F(1, 10), F(1, 4), F(2, 5), F(1, 2)])
            e1 = rng.choice([F(3, 5), F(3, 4), F(9, 10)])
            e0, prior = 1 - e1, F(1, 2)
        else:  # TP2, asymmetric, including the CE-C2a ingredients
            t01, t10 = rng.choice([(F(1, 2), F(1, 10)), (F(2, 5), F(1, 20)), (F(1, 2), F(0)), (F(1, 4), F(1, 4))])
            e0, e1 = rng.choice([(F(1, 10), F(3, 5)), (F(1, 10), F(9, 10))])
            prior = rng.choice([F(0), F(1, 2)])
        c, k = rng.choice([F(0), F(1, 100), F(1, 10)]), rng.choice([F(0), F(1, 100), F(1, 10)])
        r = check(T, B, d, t01, t10, e0, e1, prior, c, k)
        r["cell"] = [str(x) for x in (T, B, d, t01, t10, e0, e1, prior, c, k)]
        rows.append(r)
    payload = {"script": "scripts/paper4_continuation/theory_C/fu_lagrangian_monotone.py",
               "family": family, "n_cells": len(rows),
               "n_premise_z": sum(r["premise_z"] for r in rows),
               "n_premise_tape": sum(r["premise_tape"] for r in rows),
               "seconds": time.time() - started, "rows": rows}
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "rows"})
    for r in rows:
        if not r["premise_z"]:
            print("FAIL", r["cell"], r["fail_z"])


if __name__ == "__main__":
    main()
