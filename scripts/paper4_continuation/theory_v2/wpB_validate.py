"""Validate wpB_lib.solve (exact) against exhaustive pure-plan enumeration (theory_C tools)."""
import sys
from fractions import Fraction as F
sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from fu_zcoupling_check import plans, risks  # noqa: E402
from fu_lagrangian_monotone import plan_cost  # noqa: E402
from gamma_lib import make  # noqa: E402
from shiftlab.paper4.frontier_cuts import exact_costs, learner_only_game  # noqa: E402
from wpB_lib import Model, solve  # noqa: E402

cells = [(3, 2, 1, 0, 0, F(1, 10), F(3, 5), F(1, 4), F(0), F(1, 10)),
         (3, 2, 2, F(1, 4), F(1, 4), F(1, 10), F(9, 10), F(1, 2), F(1, 100), F(0)),
         (4, 2, 1, F(1, 2), F(1, 10), F(1, 10), F(3, 5), F(0), F(0), F(0)),
         (3, 3, 1, F(2, 5), F(1, 20), F(1, 10), F(3, 5), F(0), F(1, 10), F(1, 100))]
for cell in cells:
    T, B, d, t01, t10, e0, e1, p, c, k = cell
    config, model = make(T, B, d, t01, t10, e0, e1, p, c, k, F(1, 10))
    game = learner_only_game(config, model)
    costs = exact_costs(game)
    pts = [(risks(pl, T, d)[0], plan_cost(game, costs, pl, T)) for pl in plans(T, B, d)]
    m = Model(T, B, d, t01, t10, e0, e1, p, c, k, exact=True)
    for lam in [F(0), F(1, 10), F(1, 2), F(1), F(3, 2), F(3)]:
        ref = min(C + lam * R for R, C in pts)
        J, plan, info = solve(m, lam)
        print(cell[:3], float(lam), ref == J, float(ref), float(J))
