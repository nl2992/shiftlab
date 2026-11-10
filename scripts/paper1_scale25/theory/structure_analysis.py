"""When do pending labels and the remaining horizon change the optimal action? (exact DP, stationary flat prior)

Writes docs/paper1_scale25/theory/structure_tables.json and prints the tables quoted in THEORETICAL_ANALYSIS.md.
dQ = c0 - c1 is the advantage of buying a label at the current step (positive = buy), evaluated on the
post-release, post-switch value-to-go, so it isolates the acquisition decision at fixed evidence (k, n).
"""

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reduced_dp as R

OUT = HERE.parents[2] / "docs/paper1_scale25/theory/structure_tables.json"


def run(inst, evid=((1, 2), (3, 5), (6, 10)), pends=(0, 1, 2, 3, 5)):
    rec = {}
    frac = {}

    def hook(t, c0, c1, feas):
        dQ = c0 - c1  # (2, K, K, QR)
        for k, n in evid:
            for p in pends:
                if p < inst.d:
                    qr = (1 << p) - 1  # p most recent steps pending
                    rec.setdefault((k, n, p), {})[t] = float(dQ[0, k, n, qr])
        # fraction of reachable-looking states (n+pop<=B-1) where buying is strictly optimal
        m = (dQ > 0) & feas[None, None]
        tot = feas[None, None] & np.ones_like(dQ, bool)
        frac[t] = float(m.sum() / max(1, tot.sum()))

    v, _ = R.solve_optimal(inst, hook=hook)
    return v, rec, frac


if __name__ == "__main__":
    out = {}
    base = R.Inst(T=160, B=24, d=8, cs=2.0, cq=0.05, name="cs2_d8")
    v, rec, frac = run(base)
    out["V_opt"] = v
    ts = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150]
    out["dQ"] = {
        f"k{k}n{n}_pend{p}": {t: round(rec[(k, n, p)][t], 4) for t in ts} for (k, n, p) in rec
    }
    out["frac_buy"] = {t: round(frac[t], 4) for t in ts}
    last = max([t for t, f in frac.items() if f > 0.01], default=-1)
    out["last_t_with_>1pct_states_buying"] = last
    # value of delay and of budget
    out["V_opt_by_delay"] = {
        d: round(R.solve_optimal(R.Inst(T=160, B=24, d=d, cs=2.0))[0], 4) for d in (1, 2, 4, 6, 8)
    }
    out["V_opt_by_budget"] = {
        B: round(R.solve_optimal(R.Inst(T=160, B=B, d=6, cs=2.0))[0], 4)
        for B in (0, 4, 8, 16, 24, 32)
    }
    out["V_opt_by_cs"] = {
        cs: round(R.solve_optimal(R.Inst(T=160, B=24, d=6, cs=cs))[0], 4)
        for cs in (0.5, 1, 2, 5, 10)
    }
    out["V_opt_by_T"] = {
        T: round(R.solve_optimal(R.Inst(T=T, B=24, d=6, cs=2.0))[0] / T, 4)
        for T in (60, 100, 160, 240)
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("V_opt", v, "last t with >1% states buying:", last)
    print("fraction of states buying by t:", out["frac_buy"])
    for key, row in out["dQ"].items():
        print(key, row)
    for k in ("V_opt_by_delay", "V_opt_by_budget", "V_opt_by_cs", "V_opt_by_T"):
        print(k, out[k])
