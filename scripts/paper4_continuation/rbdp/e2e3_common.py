"""Shared helpers for E2/E3 runs: upper-only RB-DP solve, JSONL append, hashes."""
from __future__ import annotations
import hashlib, json, os, sys, time
from fractions import Fraction as F
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from shiftlab.paper4 import risk_budget_dp as R

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SOLVER = os.path.join(ROOT, "src/shiftlab/paper4/risk_budget_dp.py")
RES = os.path.join(ROOT, "docs/paper4_continuation/rbdp/results")

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def upper_only(cfg):
    t0 = time.perf_counter()
    s = R._Solver(cfg); s._build_post(); s._run_dp(lower=False)
    ev = R.evaluate_policy(s)
    return dict(U=ev["cost_exact"], risk_causal=ev["risk_causal"], risk_iid=ev["risk_iid"],
                C0=s.never_promote_cost(), runtime_s=time.perf_counter() - t0, n_beta_grid=s.G, n_w=s.Nw)

def cfg_of(t, e, T, B, mode, n_beta=401, wdiv=20, alpha=0.1):
    t = float(F(t)); e = float(F(e))
    return R.RBDPConfig(T=T, B=B, t01=t, t10=t, e0=e, e1=1 - e, alpha=alpha, n_beta=n_beta,
                        w_step_div=wdiv, mode=mode)

def append(path, rec, script):
    rec = dict(rec, script_sha256=sha(script), solver_sha256=sha(SOLVER))
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n"); f.flush(); os.fsync(f.fileno())
