"""WP B: exact record of the symmetric-stationary counterexamples to Z2 / U-M / Lemma U.

For each cell: gamma_cell certified Gamma interval (repo FCG, exact rationals); for the main cell also
the exact Lagrangian data from the independent DP (wpB_lib): the hull vertex at lambda = 2/5 with the
least and largest IID risk over ALL Lagrangian-optimal pure plans, z-monotonicity, causal risk, the
optimal multiplier lambda*, and V*_IID = J(lambda*) - lambda* alpha (primal = dual).
usage: wpB_ce_record.py OUT.json
"""

from __future__ import annotations

import sys
from fractions import Fraction as F

sys.set_int_max_str_digits(0)
sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from wpB_lib import Model, risk_of, solve, z_monotone  # noqa: E402

CELLS = [
    ((5, 4, 1, F(1, 10), F(1, 10), F(1, 100), F(99, 100), F(1, 2), F(0), F(0)), F(25, 32)),
    ((6, 4, 2, F(1, 20), F(1, 20), F(1, 1000), F(999, 1000), F(1, 2), F(0), F(1, 20)), F(25, 32)),
    ((9, 6, 1, F(1, 100), F(1, 100), F(1, 100), F(99, 100), F(1, 2), F(1, 1000), F(1, 1000)), F(69, 128)),
]


def short(x):
    s = str(x)
    return s if len(s) < 120 else f"{float(x):.17g} (long rational)"


def main():
    out = sys.argv[1]
    recs = []
    for idx, (cell, alpha) in enumerate(CELLS):
        g = gamma_cell(*cell, alpha)
        rec = {"cell": [str(x) for x in cell], "alpha": str(alpha),
               "Gamma_lo": short(F(g["Gamma_lo"])), "Gamma_hi": short(F(g["Gamma_hi"])),
               "Gamma_positive_certified": g["Gamma_positive_certified"],
               "U_IID": short(F(g["U_IID"])), "U_causal": short(F(g["U_causal"])),
               "R_iid_of_IID_opt": g["R_iid_iid_opt_raw"], "R_causal_of_IID_opt": g["R_causal_iid_opt_raw"],
               "V_causal_source": g["V_causal_source"]}
        if idx == 0:
            m = Model(*cell, exact=True)
            lam = F(2, 5)
            v = {}
            for tie in ("minR", "maxR"):
                J, plan, info = solve(m, lam, tie=tie)
                ok, wit = z_monotone(plan, m)
                v[tie] = {"J": str(J), "R": str(info["R"]), "C": str(info["C"]),
                          "R_causal": str(risk_of(plan, m, causal=True)), "z_monotone": ok, "witness": str(wit)}
            _, p2, i2 = solve(m, F(1, 2), tie="minR")
            Rv, Cv = F(v["minR"]["R"]), F(v["minR"]["C"])
            lam_star = (i2["C"] - Cv) / (Rv - i2["R"])
            Jst, _, _ = solve(m, lam_star)
            w = (alpha - i2["R"]) / (Rv - i2["R"])
            rec["dp"] = {"lambda_2/5": v,
                         "vertex_lambda_1/2": {"R": str(i2["R"]), "C": str(i2["C"]), "z_monotone": z_monotone(p2, m)[0]},
                         "lambda_star": str(lam_star),
                         "V_IID_primal": str(w * Cv + (1 - w) * i2["C"]),
                         "V_IID_dual": str(Jst - lam_star * alpha),
                         "Gamma_upper_exact": str(F(g["U_causal"]) - (Jst - lam_star * alpha))}
        recs.append(rec)
        print(rec, flush=True)
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_v2/wpB_ce_record.py", "records": recs})


if __name__ == "__main__":
    main()
