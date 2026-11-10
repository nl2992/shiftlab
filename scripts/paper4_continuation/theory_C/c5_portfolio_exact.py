"""C5: causal value of a PRIVATE root portfolio over opportunity calendars (constraint generation).

A portfolio draws calendar C with prob w_C privately at the root, then plays a C-restricted
policy.  Its realization plan is x = sum_C x_C with x_C in w_C * Flow(C), and since the null sees
only public actions its causal risk is max_nu r_nu . x (Lemma 2 of the structural audit), so
the problem is an LP over (x_C, w_C) with the same cut rows as FCG.
Reported: float LP value (lower bound up to LP tolerance) and the exact cost of the recovered,
exactly-verified and root-repaired portfolio policy (upper bound).
usage: c5_portfolio_exact.py OUT.json CELLNAME   (cells from c5_adaptivity_gap CELLS/LONG_CELLS)
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F
from itertools import combinations

import numpy as np
from scipy.optimize import linprog
from scipy.sparse import csr_matrix, hstack, vstack

from c5_adaptivity_gap import CELLS, LONG_CELLS
from gamma_lib import make, save_refuse_overwrite
from shiftlab.paper4.frontier_cuts import best_response_null
from shiftlab.paper4.frontier_cuts_fast import FastGame, _repair, float_risk_row


def portfolio_value(cell, alpha=F(1, 10), max_iters=60):
    T, B = cell[0], cell[1]
    config, model = make(*cell, alpha=alpha)
    game = FastGame(config, model)
    game._alternative((), (), 0, F(1), model.prior1, F(0))
    game.built = True
    n = game.learner.count
    flow, rhs = game.learner.matrix()
    obj = np.zeros(n)
    for key, value in game.cost.items():
        obj[key] = value
    cals = list(combinations(range(1, T + 1), B))
    m = len(cals)
    # disallowed sequences per calendar
    banned = []
    for cal in cals:
        bad = set()
        for (history, _rel), (_p, children, choices) in game.learner.infos.items():
            t = len(history) + 1
            for (a, q), child in zip(choices, children):
                if q and t not in cal:
                    bad.add(child)
        banned.append(bad)
    eq_blocks = []
    e_col = csr_matrix(rhs.reshape(-1, 1))
    for i in range(m):
        left = [csr_matrix((flow.shape[0], n))] * m
        left[i] = flow
        wcols = [csr_matrix((flow.shape[0], 1))] * m
        wcols[i] = -e_col
        eq_blocks.append(hstack(left + wcols))
    a_eq = vstack(eq_blocks + [hstack([csr_matrix((1, m * n)), csr_matrix(np.ones((1, m)))])]).tocsr()
    b_eq = np.r_[np.zeros(a_eq.shape[0] - 1), 1.0]
    bounds = []
    for i in range(m):
        bounds += [(0, 0) if j in banned[i] else (0, None) for j in range(n)]
    bounds += [(0, None)] * m
    cvec = np.r_[np.tile(obj, m), np.zeros(m)]
    rows = [float_risk_row(game, {}, n)]

    def stacked(row):
        return hstack([row] * m + [csr_matrix((1, m))])

    for it in range(max_iters):
        a_ub = vstack([stacked(r) for r in rows]).tocsr()
        res = linprog(cvec, A_ub=a_ub, b_ub=np.full(len(rows), float(alpha)), A_eq=a_eq, b_eq=b_eq,
                      bounds=bounds, method="highs",
                      options={"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10})
        if not res.success:
            raise RuntimeError(res.message)
        x = res.x[: m * n].reshape(m, n).sum(axis=0)
        weights = res.x[m * n:]
        policy, _ = game.recover(x)
        risk, strategy = best_response_null(game, policy)
        if risk <= alpha * (1 + F(1, 10**6)):
            break
        rows.append(float_risk_row(game, strategy, n))
    repaired, upper, act = _repair(game, policy, risk, alpha)
    return {
        "lp_value": float(res.fun), "U_exact": str(upper), "U_float": float(upper),
        "raw_robust_risk": str(risk), "activation": str(act), "iterations": it + 1,
        "weights": {str(c): float(w) for c, w in zip(cals, weights) if w > 1e-9},
    }


def main():
    out, name = sys.argv[1], sys.argv[2]
    cell = {**CELLS, **LONG_CELLS}[name]
    started = time.time()
    r = portfolio_value(cell)
    r.update({"cell_name": name, "cell": [str(x) for x in cell], "seconds": time.time() - started,
              "script": "scripts/paper4_continuation/theory_C/c5_portfolio_exact.py"})
    save_refuse_overwrite(out, r)
    print(r)


if __name__ == "__main__":
    main()
