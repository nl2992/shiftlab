"""Lattice-solver curves shared by fig_lattice (Fig. 4) and the value-curve inset of fig_overview.
Cell: T=6, B=3, transitions 19/20, e=1/50, alpha=1/10, n_beta=401 (N=80 risk steps). Needs PYTHONPATH=src."""
import numpy as np
from shiftlab.paper4 import risk_budget_dp_fast as F

T, B, TR, E = 6, 3, 0.95, 0.02


def solve_mode(mode):
    cfg = F.RBDPConfig(T=T, B=B, t01=TR, t10=TR, e0=E, e1=1 - E, alpha=0.1, n_beta=401, mode=mode,
                       lattice_exact=True, compute_upper=False, compute_lower=True)
    s = F._Solver(cfg)
    s._build_post()
    s._run_dp(lower=False, keep=True)
    loc = s.locate(np.array([s.beta1]))
    assert abs(s.beta1 - 0.5) < 1e-12
    return s, {n: F._lerp_rows(s.Vup[1][n], loc)[0] for n in range(1, B + 1)}, s.never_promote_cost()


def kinks(v):
    return np.where(np.abs(np.diff(v, 2)) > 1e-9)[0] + 1


def get():
    res = {m: solve_mode(m) for m in ("iid", "causal")}
    N = res["iid"][0].N
    assert N == 80 and res["iid"][2] == res["causal"][2]
    return res, N, res["iid"][2]
