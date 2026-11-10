"""WP B: independent weak-duality certificate for Gamma > 0 (does not use FCG).

V*_causal >= min_pi [C(pi) + l1 R_IID(pi) + l2 R_nu(pi)] - (l1 + l2) alpha for any l1, l2 >= 0 and any fixed
causal null nu, because a causal-feasible mixture has R_IID <= alpha and R_nu <= alpha and both risks
are linear in the mixture.  nu here: the j-th queried label (query order) is Ber(p_j), p_j in [0,1/2]
a function of the query time and the labels already visible (public), so nu is a valid causal null.  V*_IID is computed exactly
from the Lagrangian hull (max over lambda of J(lambda) - lambda alpha).  The DP is wpB_lib's, extended
with a second null world.  Everything is exact (Fractions) at the final multipliers.
usage: wpB_dual_check.py OUT.json 'cell tuple' ALPHA 'lambda tq, rel: p'   (p as a Fraction)
"""

from __future__ import annotations

import sys
from fractions import Fraction as F

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import save_refuse_overwrite  # noqa: E402
from wpB_lib import Model  # noqa: E402


def rec_wrapper(model, l1, l2, pfun):
    """min over pure plans of C + l1 R_IID + l2 R_nu.

    nu is a causal null given by pfun(query_time, released) -> p in [0, 1/2], where released is the
    tuple of (query_time, label) visible to the learner at the query time (public information).
    """
    T, B = model.T, model.B
    half = model.half

    def rec(t, nq, rel, plist, masses, n1, n2):
        b = B - nq
        best = None
        for a in (1, 0):
            for qq in ((0, 1) if b else (0,)):
                if a == 1:
                    v = model.promote_value(t, b, masses, qq) + n1 + n2
                else:
                    v = sum(m * model.em(s) for (s, _), m in masses.items()) + model.c * qq * sum(masses.values())
                    if t < T:
                        nxt = model.step(t, masses, qq)
                        pl = plist + ((t, pfun(t, rel)),) if qq else plist
                        for y, sub in model.release(t + 1, nxt):
                            if y is None:
                                v += rec(t + 1, nq + qq, rel, pl, sub, n1, n2)
                            else:
                                tq, p = pl[0]
                                v += rec(t + 1, nq + qq, rel + ((tq, y),), pl[1:], sub, n1 * half,
                                         n2 * (p if y else 1 - p))
                if best is None or v < best:
                    best = v
        return best

    return rec(1, 0, (), (), model.root(), l1, l2)


def main():
    out = sys.argv[1]
    cell = eval(sys.argv[2])
    alpha = F(sys.argv[3])
    pfun_exact = eval(sys.argv[4])

    def pfun_float(tq, rel):
        return float(pfun_exact(tq, rel))
    mf = Model(*[float(x) for x in cell])
    # coarse float search over (l1, l2)
    best = (-1e9, None)
    grid = [i / 20 for i in range(0, 41)]
    for l1 in grid:
        for l2 in grid:
            v = rec_wrapper(mf, l1, l2, pfun_float) - (l1 + l2) * float(alpha)
            if v > best[0]:
                best = (v, (l1, l2))
    # local refinement
    step = 1 / 40
    l1, l2 = best[1]
    for _ in range(200):
        improved = False
        for dl1, dl2 in ((step, 0), (-step, 0), (0, step), (0, -step), (step, -step), (-step, step), (step, step), (-step, -step)):
            a, b = max(0, l1 + dl1), max(0, l2 + dl2)
            v = rec_wrapper(mf, a, b, pfun_float) - (a + b) * float(alpha)
            if v > best[0] + 1e-15:
                best, l1, l2, improved = (v, (a, b)), a, b, True
        if not improved:
            step /= 2
            if step < 1e-7:
                break
    l1e, l2e = F(l1).limit_denominator(10**6), F(l2).limit_denominator(10**6)
    me = Model(*cell, exact=True)
    lb_causal = rec_wrapper(me, l1e, l2e, pfun_exact) - (l1e + l2e) * alpha
    # exact V_IID: max over lambda of J(lambda) - lambda alpha with l2 = 0; use same search on l1 then exact
    bi = (-1e9, None)
    for i in range(0, 4001):
        lam = i / 1000
        v = rec_wrapper(mf, lam, 0.0, lambda tq, rel: 0.5) - lam * float(alpha)
        if v > bi[0]:
            bi = (v, lam)
    payload = {"script": "scripts/paper4_continuation/theory_v2/wpB_dual_check.py",
               "cell": [str(x) for x in cell], "alpha": str(alpha), "nu": sys.argv[4],
               "multipliers_exact": [str(l1e), str(l2e)], "V_causal_lower_bound_exact": str(lb_causal),
               "V_causal_lower_bound_float": float(lb_causal), "V_IID_dual_float_grid": bi[0], "lambda_IID_grid": bi[1]}
    save_refuse_overwrite(out, payload)
    print(payload)


if __name__ == "__main__":
    main()
