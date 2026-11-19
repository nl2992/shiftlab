"""Check (c), adversarial draw: B up to 4, T up to 8, extreme / asymmetric parameters, non-dyadic alpha,
nonzero c and k.  Exact Theorem 2 test as in check_c_lattice.run, plus comparison of the exact root value
W(1, beta_1, B, alpha) with RB-DP (lattice_exact=True, N = d_alpha * 2^B) and with a w grid that contains
alpha but is not a multiple of 2^B (N = 3 d_alpha)."""
from __future__ import annotations

import json
import random
import sys
import time
from fractions import Fraction as F

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from check_c_lattice import run  # noqa: E402
from common import Cell  # noqa: E402


def draw(rng):
    pick = lambda xs: rng.choice(xs)  # noqa: E731
    tvals = [F(0), F(1, 20), F(1, 3), F(1, 2), F(13, 20), F(9, 10), F(19, 20), F(1)]
    return Cell(
        T=rng.randint(4, 8), B=rng.randint(1, 4),
        t01=pick(tvals), t10=pick(tvals),
        e0=pick([F(1, 100), F(1, 10), F(9, 20), F(49, 100)]), e1=pick([F(51, 100), F(11, 20), F(9, 10), F(99, 100)]),
        prior=pick([F(0), F(1), F(1, 2), F(3, 7)]),
        c=pick([F(0), F(1, 100), F(1, 9), F(1, 2)]), k=pick([F(0), F(1, 13), F(1, 3)]),
        alpha=pick([F(1, 3), F(2, 7), F(1, 11), F(3, 13), F(1, 100), F(1, 10), F(5, 6)]),
    )


def rbdp_root(cell, mode, n_cells=None):
    from shiftlab.paper4 import risk_budget_dp_fast as fast

    kw = dict(T=cell.T, B=cell.B, t01=float(cell.t01), t10=float(cell.t10), e0=float(cell.e0), e1=float(cell.e1),
              prior1=float(cell.prior), c=float(cell.c), k=float(cell.k), alpha=float(cell.alpha), mode=mode,
              n_beta=201)
    if n_cells is None:
        r = fast.solve(fast.RBDPConfig(lattice_exact=True, **kw))
        return r["L"], r["U"], r["risk_causal"] if mode == "causal" else r["risk_iid"]
    k = F(n_cells) * cell.alpha
    assert k.denominator == 1
    solver = fast._Solver(fast.RBDPConfig(w_step_div=int(k), **kw))
    assert solver.N == n_cells
    solver._build_post()
    tab = solver._run_dp(lower=False, keep=False)
    lo, hi = solver.root_indices()
    return solver.root_value(tab, lo)


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    rng = random.Random(777)
    tot = {"rows": 0, "chord_tests": 0, "chord_fail": 0, "offlattice_vertices": 0, "crossings": 0, "increasing": 0}
    recs = []
    worst_L = worst_U = 0.0
    ctrl_worse = 0
    ctrl_max = 0.0
    t0 = time.time()
    for i in range(50):
        cell = draw(rng)
        for mode in ("causal", "iid"):
            checks = {"rows": 0, "chord_tests": 0, "chord_fail": [], "offlattice_vertices": [], "crossings": 0,
                      "increasing": 0}
            v, _ = run(cell, mode, checks)
            for k in tot:
                x = checks[k]
                tot[k] += len(x) if isinstance(x, list) else x
            rec = {"cell": {k: str(getattr(cell, k)) for k in cell.__dataclass_fields__}, "mode": mode,
                   "V_exact": str(v), "fails": checks["chord_fail"][:3], "off": checks["offlattice_vertices"][:3]}
            if cell.e0 < F(1, 2) < cell.e1 and 0 < cell.alpha <= 1:
                try:
                    L, U, risk = rbdp_root(cell, mode)
                    rec.update(L=L, U=U, risk=risk, dL=L - float(v), dU=U - float(v))
                    worst_L = max(worst_L, abs(L - float(v)))
                    worst_U = max(worst_U, abs(U - float(v)))
                    if cell.B >= 1:
                        ctrl = rbdp_root(cell, mode, 3 * cell.alpha.denominator)
                        rec["ctrl_minus_exact"] = ctrl - float(v)
                        ctrl_max = max(ctrl_max, ctrl - float(v))
                        ctrl_worse += (ctrl - float(v)) > 1e-9
                except Exception as exc:  # report, do not hide
                    rec["rbdp_error"] = repr(exc)
            recs.append(rec)
            if checks["chord_fail"] or checks["offlattice_vertices"] or "rbdp_error" in rec or abs(rec.get("dU", 0)) > 1e-9:
                print("NOTE", json.dumps(rec, default=str))
            sys.stdout.flush()
    print("adversarial 50 cells x 2 modes:", tot)
    print(f"RB-DP lattice vs exact: max|L-V|={worst_L:.3e} max|U-V|={worst_U:.3e}; control grid 3*d_alpha worse in "
          f"{ctrl_worse} of {len(recs)} runs, by up to {ctrl_max:.3e}; {time.time() - t0:.1f}s")
    with open(__file__.rsplit("/", 1)[0] + "/check_c2_results.json", "w") as fh:
        json.dump({"totals": tot, "records": recs}, fh, indent=1, default=str)
