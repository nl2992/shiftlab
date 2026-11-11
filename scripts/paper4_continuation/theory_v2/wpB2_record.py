"""WP B follow-up: exact record of symmetric-stationary counterexamples at alpha <= 1/2 (Z2<=1/2).

For each cell: certified gamma_cell at the listed alphas, and the exact DP description of the
non-monotone hull vertex: the least/largest IID risk over all Lagrangian-optimal pure plans at an
interior lambda, the causal risk, the z-monotonicity witness, and the promotion event as a set of
query-order label strings.
usage: wpB2_record.py OUT.json
"""

from __future__ import annotations

import sys
from fractions import Fraction as F
from itertools import product

sys.set_int_max_str_digits(0)
sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
import wpB2_halfscan as H  # noqa: E402
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from wpB_lib import Model, risk_of, run_z, solve, z_monotone  # noqa: E402

CASES = [
    ((8, 4, 2, F(1, 4), F(1, 4), F(1, 1000), F(999, 1000), F(1, 2), F(0), F(0)), [F(9, 32), F(5, 16), F(1, 2)]),
    ((7, 6, 1, F(1, 4), F(1, 4), F(1, 100), F(99, 100), F(1, 2), F(0), F(1, 100)), [F(21, 64), F(3, 8), F(1, 2)]),
]


def main():
    out = sys.argv[1]
    recs = []
    for cell, alphas in CASES:
        verts, rel, _ = H.vertex_data("sym", cell)
        m = Model(*cell, exact=True)
        vrec = []
        for v in verts:
            if v["monotone"] or v["R"] > 0.5:
                continue
            lam = F(v["lam"]).limit_denominator(10**6)
            d = {}
            for tie in ("minR", "maxR"):
                _, plan, info = solve(m, lam, tie=tie)
                ok, wit = z_monotone(plan, m)
                ev = ["".join(map(str, z)) for z in product((0, 1), repeat=min(m.B, m.T)) if run_z(plan, m, z)]
                d[tie] = {"R": str(info["R"]), "C": str(info["C"]), "R_causal": str(risk_of(plan, m, causal=True)),
                          "z_monotone": ok, "witness": str(wit), "event": ev}
            vrec.append({"lambda": str(lam), "range": v["range"], "plans": d})
        g = {}
        for a in alphas:
            r = gamma_cell(*cell, a)
            g[str(a)] = {"Gamma_lo": r["Gamma_lo_f"], "Gamma_hi": r["Gamma_hi_f"],
                         "certified_positive": r["Gamma_positive_certified"],
                         "R_iid_IIDopt": r["R_iid_iid_opt_raw"], "R_causal_IIDopt": r["R_causal_iid_opt_raw"]}
        rec = {"cell": [str(x) for x in cell], "hull_R": [v["R"] for v in verts],
               "hull_monotone": [v["monotone"] for v in verts], "nonmonotone_vertices_le_half": vrec, "gamma": g}
        recs.append(rec)
        print({k: v for k, v in rec.items() if k != "nonmonotone_vertices_le_half"}, flush=True)
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_v2/wpB2_record.py", "records": recs})


if __name__ == "__main__":
    main()
