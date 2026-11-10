"""Check Lemma Zc (query-order coupling): every pure plan whose promotion event is monotone in the
sequence of QUERIED labels (z_1, z_2, ... in query order) has causal risk = IID risk.

Enumerates all reachable pure pre-promotion plans of small games (T, B, d) and reports counts of
tape-monotone, z-monotone, both, and any z-monotone plan with R_causal != R_IID (should be 0).
usage: fu_zcoupling_check.py OUT.json
"""

from __future__ import annotations

import sys
from fractions import Fraction as F
from itertools import product

from gamma_lib import save_refuse_overwrite


def plans(T, B, d):
    """Yield pure plans as dicts info -> (a, q) over reachable pre-promotion info sets."""

    def info(history, outcomes):
        t = len(history) + 1
        return history, tuple((s, y) for s, y in outcomes if s + d <= t)

    def expand(frontier, plan):
        # frontier: list of (history, outcomes) nodes still to decide
        if not frontier:
            yield dict(plan)
            return
        (history, outcomes), rest = frontier[0], frontier[1:]
        t = len(history) + 1
        if t > T:
            yield from expand(rest, plan)
            return
        key = info(history, outcomes)
        remaining = B - sum(q for _, q in history)
        choices = list(product((0, 1), (0, 1) if remaining else (0,)))
        options = [plan[key]] if key in plan else choices
        for a, q in options:
            new = dict(plan)
            new[key] = (a, q)
            nxt = []
            if not a:
                h2 = history + ((a, q),)
                if q:
                    nxt = [(h2, outcomes + ((t, 0),)), (h2, outcomes + ((t, 1),))]
                else:
                    nxt = [(h2, outcomes)]
            yield from expand(nxt + rest, new)

    yield from expand([((), ())], {})


def run(plan, T, d, label_of):
    """Simulate; label_of(t, j) gives the label of the j-th query made at time t."""
    history, outcomes, j = (), (), 0
    for t in range(1, T + 1):
        key = (history, tuple((s, y) for s, y in outcomes if s + d <= t))
        a, q = plan[key]
        if a:
            return 1
        history = history + ((a, q),)
        if q:
            outcomes = outcomes + ((t, label_of(t, j)),)
            j += 1
    return 0


def monotone(fun, n):
    for x in product((0, 1), repeat=n):
        for i in range(n):
            if not x[i]:
                y = x[:i] + (1,) + x[i + 1:]
                if fun(x) > fun(y):
                    return False
    return True


def risks(plan, T, d):
    def visit(history, outcomes, causal):
        t = len(history) + 1
        if t > T:
            return F(0)
        key = (history, tuple((s, y) for s, y in outcomes if s + d <= t))
        a, q = plan[key]
        if a:
            return F(1)
        h2 = history + ((a, q),)
        if not q:
            return visit(h2, outcomes, causal)
        v0 = visit(h2, outcomes + ((t, 0),), causal)
        v1 = visit(h2, outcomes + ((t, 1),), causal)
        return max(v0, (v0 + v1) / 2) if causal else (v0 + v1) / 2

    return visit((), (), False), visit((), (), True)


def main():
    out = sys.argv[1]
    res = {}
    for T, B, d in [(3, 2, 1), (3, 2, 2), (4, 2, 1), (3, 3, 1)]:
        n = tm = zm = both = zm_bad = tm_bad = zonly_ineq = 0
        example = None
        for plan in plans(T, B, d):
            n += 1
            g_tape = lambda y: run(plan, T, d, lambda t, j: y[t - 1])  # noqa: B023,E731
            g_z = lambda z: run(plan, T, d, lambda t, j: z[j])  # noqa: B023,E731
            is_t, is_z = monotone(g_tape, T), monotone(g_z, B)
            r_iid, r_c = risks(plan, T, d)
            tm += is_t
            zm += is_z
            both += is_t and is_z
            zm_bad += is_z and r_c != r_iid
            tm_bad += is_t and r_c != r_iid
            if is_z and not is_t:
                zonly_ineq += 1
                if example is None and r_iid > 0:
                    example = {"plan": {str(k): v for k, v in plan.items()},
                               "R_IID": str(r_iid), "R_causal": str(r_c)}
        res[f"T{T}_B{B}_d{d}"] = {"n_plans": n, "tape_monotone": tm, "z_monotone": zm, "both": both,
                                  "z_monotone_not_tape": zonly_ineq,
                                  "z_monotone_with_R_causal_ne_R_IID": zm_bad,
                                  "tape_monotone_with_R_causal_ne_R_IID": tm_bad,
                                  "example_z_not_tape": example}
        print(T, B, d, {k: v for k, v in res[f"T{T}_B{B}_d{d}"].items() if k != "example_z_not_tape"},
              flush=True)
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_C/fu_zcoupling_check.py",
                                "results": res})


if __name__ == "__main__":
    main()
