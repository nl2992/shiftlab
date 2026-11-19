"""Cross-check my independent LP (check_b_lp) and exact PL DP (check_c_lattice) against the repo's own
sequence-form reference gamma_cell on the repo test cell T5B2_t.9 (c=1/100, k=1/10, alpha=1/10)."""
import sys
from fractions import Fraction as F
sys.path.insert(0, __file__.rsplit("/", 1)[0])
sys.path.insert(0, "scripts/paper4_continuation/theory_C")
from common import Cell
from check_b_lp import exact_values
from check_c_lattice import run
from gamma_lib import gamma_cell

cell = Cell(5, 2, F(9, 10), F(9, 10), F(1, 10), F(9, 10), c=F(1, 100), k=F(1, 10), alpha=F(1, 10))
ex = exact_values(cell)
pl = {m: run(cell, m, {"rows": 0, "chord_tests": 0, "chord_fail": [], "offlattice_vertices": [], "crossings": 0, "increasing": 0})[0] for m in ("causal", "iid")}
ref = gamma_cell(5, 2, 1, F(9, 10), F(9, 10), F(1, 10), F(9, 10), F(1, 2), F(1, 100), F(1, 10), F(1, 10))
print("my LP:", ex)
print("my exact PL DP:", {m: (str(v), float(v)) for m, v in pl.items()})
print("repo gamma_cell:", {k: ref[k] for k in ("L_causal", "U_causal", "L_IID", "U_IID")})
