"""WP B: test U1 (uniform pure-plan domination) by exhaustive enumeration on small cells.

U1: every non-monotone pure plan pi has a z-monotone (or tape-monotone) pure plan pi' with
C(pi') <= C(pi) and R_IID(pi') <= R_IID(pi) (so pi' dominates for every lambda at once).
U2 (existence of a monotone Lagrangian-optimal plan for each lambda) is implied by U1 but not conversely.
Exact rationals; enumeration and costs from theory_C tools.
usage: wpB_u1_check.py OUT.json FAMILY SEED N
"""

from __future__ import annotations

import random
import sys
from fractions import Fraction as F

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
from fu_lagrangian_monotone import plan_cost  # noqa: E402
from fu_zcoupling_check import monotone, plans, risks, run  # noqa: E402
from gamma_lib import make, save_refuse_overwrite  # noqa: E402
from shiftlab.paper4.frontier_cuts import exact_costs, learner_only_game  # noqa: E402

SHAPES = [(3, 2, 1), (3, 2, 2), (4, 2, 1), (3, 3, 1), (4, 2, 2)]


def main():
    out, family, seed, n = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        T, B, d = rng.choice(SHAPES)
        if family == "static":
            t01 = t10 = F(0)
            prior = rng.choice([F(1, 10), F(1, 4), F(1, 2), F(3, 4), F(9, 10)])
            e0 = rng.choice([F(1, 20), F(1, 10), F(1, 4), F(2, 5)])
            e1 = rng.choice([F(11, 20), F(3, 5), F(3, 4), F(9, 10)])
        else:
            t01 = t10 = rng.choice([F(1, 20), F(1, 10), F(1, 4), F(1, 2)])
            e1 = rng.choice([F(3, 5), F(3, 4), F(9, 10), F(99, 100)])
            e0, prior = 1 - e1, F(1, 2)
        c, k = rng.choice([F(0), F(1, 100), F(1, 10)]), rng.choice([F(0), F(1, 100), F(1, 10)])
        config, model = make(T, B, d, t01, t10, e0, e1, prior, c, k, F(1, 10))
        game = learner_only_game(config, model)
        costs = exact_costs(game)
        mono, non = [], []
        for plan in plans(T, B, d):
            C = plan_cost(game, costs, plan, T)
            R, _ = risks(plan, T, d)
            is_z = monotone(lambda z: run(plan, T, d, lambda t, j: z[j]), B)  # noqa: B023
            is_t = monotone(lambda y: run(plan, T, d, lambda t, j: y[t - 1]), T)  # noqa: B023
            (mono if (is_z or is_t) else non).append((R, C))
        undominated = [p for p in set(non) if not any(r <= p[0] and cc <= p[1] for r, cc in mono)]
        rows.append({"cell": [str(x) for x in (T, B, d, t01, t10, e0, e1, prior, c, k)],
                     "n_monotone": len(mono), "n_nonmonotone": len(non),
                     "n_undominated_nonmonotone_points": len(undominated),
                     "example": [str(x) for x in min(undominated)] if undominated else None})
        print(rows[-1], flush=True)
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB_u1_check.py", "family": family, "seed": seed,
               "n_cells": len(rows), "n_cells_U1_fails": sum(r["n_undominated_nonmonotone_points"] > 0 for r in rows),
               "rows": rows}
    save_refuse_overwrite(out, payload)
    print({k: v for k, v in payload.items() if k != "rows"})


if __name__ == "__main__":
    main()
