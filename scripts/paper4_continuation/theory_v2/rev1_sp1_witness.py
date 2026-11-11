"""Reviewer 1: certified witnesses for the SP1 review findings (gamma_cell, force_fcg=True).
usage: rev1_sp1_witness.py OUT.json"""
import sys
from fractions import Fraction as F

sys.path.insert(0, "scripts/paper4_continuation/theory_C")
sys.path.insert(0, "scripts/paper4_continuation/theory_v2")
from gamma_lib import gamma_cell, save_refuse_overwrite  # noqa: E402
from rev1_sp1_lib import sp1_formula, n1_brute_sym  # noqa: E402

W = {
    # SP1-D bullet 1 ("g <= 2k => Gamma = 0") at T = d+1
    "SP1D_b1_T2_d1": (2, 1, F(1), F(1, 10), F(0), F(8, 25), F(1, 2)),
    "SP1D_b1_T2_d1_k2/5": (2, 1, F(1), F(1, 10), F(0), F(2, 5), F(1, 10)),
    "SP1D_b1_T4_d3": (4, 3, F(1), F(1, 4), F(0), F(1001, 8000), F(1, 2)),
    # SP1-C worked example: doc says bound gives Gamma >= 0.01; bound is 0.008 and exact T=3 value is 0.008
    "SP1C_example_T2": (2, 1, F(3, 4), F(1, 10), F(1, 100), F(1, 50), F(1, 10)),
    "SP1C_example_T3": (3, 1, F(3, 4), F(1, 10), F(1, 100), F(1, 50), F(1, 10)),
    "SP1C_example_T4": (4, 1, F(3, 4), F(1, 10), F(1, 100), F(1, 50), F(1, 10)),
    # fixed-T monotonicity in d fails for k > 0 (d -> d+2 with T = d+3)
    "dmono_r1_d3": (6, 3, F(1), F(1, 4), F(0), F(1, 8), F(1, 20)),
    "dmono_r1_d5": (6, 5, F(1), F(1, 4), F(0), F(1, 8), F(1, 20)),
    "dmono_r.98_d5": (8, 5, F(99, 100), F(1, 4), F(1, 100), F(1, 10), F(1, 4)),
    "dmono_r.98_d7": (8, 7, F(99, 100), F(1, 4), F(1, 100), F(1, 10), F(1, 4)),
}
rows = {}
for name, (T, d, t, e, c, k, al) in W.items():
    res = gamma_cell(T, 1, d, t, t, e, 1 - e, F(1, 2), c, k, al, force_fcg=True)
    rows[name] = dict(T=T, d=d, t=str(t), e=str(e), c=str(c), k=str(k), alpha=str(al),
                      Gamma_lo=res["Gamma_lo"], Gamma_hi=res["Gamma_hi"],
                      sp1=str(sp1_formula(T, d, t, e, c, k, al)), n1_brute=str(n1_brute_sym(T, d, t, e, c, k, al)))
    print(name, rows[name]["Gamma_lo"], rows[name]["Gamma_hi"], rows[name]["sp1"])
save_refuse_overwrite(sys.argv[1], dict(script="rev1_sp1_witness.py", rows=rows))
