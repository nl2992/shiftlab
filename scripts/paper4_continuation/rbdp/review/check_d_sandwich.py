"""Corollary 3 sandwich L <= V* <= U with GENUINE belief-interpolation error: coarse uniform belief grids,
no reachable-belief extras (n_extra_max=0), lattice_exact=True. V* from my exact PL DP (check_c_lattice)."""
import sys, warnings
from fractions import Fraction as F
warnings.filterwarnings("ignore")
sys.path.insert(0, __file__.rsplit("/", 1)[0])
sys.setrecursionlimit(100000)
from check_b_lp import CELLS
from check_c_lattice import run
from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, solve

viol = 0; n = 0; worst_gap = 0.0
for name, cell in CELLS.items():
    for mode in ("causal", "iid"):
        v = float(run(cell, mode, {"rows": 0, "chord_tests": 0, "chord_fail": [], "offlattice_vertices": [], "crossings": 0, "increasing": 0})[0])
        for nb in (3, 5, 11, 41):
            r = solve(RBDPConfig(T=cell.T, B=cell.B, t01=float(cell.t01), t10=float(cell.t10), e0=float(cell.e0),
                                 e1=float(cell.e1), prior1=float(cell.prior), c=float(cell.c), k=float(cell.k),
                                 alpha=float(cell.alpha), mode=mode, n_beta=nb, n_extra_max=0, lattice_exact=True))
            risk = r["risk_causal"] if mode == "causal" else r["risk_iid"]
            bad = not (r["L"] <= v + 1e-12 and v <= r["U"] + 1e-12 and risk <= float(cell.alpha) + 1e-12)
            viol += bad; n += 1; worst_gap = max(worst_gap, r["U"] - r["L"])
            print(f"{name:20s} {mode:6s} n_beta={nb:3d} L={r['L']:.10f} V*={v:.10f} U={r['U']:.10f} risk={risk:.6f} {'VIOLATION' if bad else ''}")
print("runs", n, "violations", viol, "max U-L", worst_gap)
