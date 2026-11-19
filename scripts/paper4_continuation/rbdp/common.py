"""Shared helpers for RB-DP validation/baseline scripts."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys, time
from fractions import Fraction as F

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RES = os.path.join(ROOT, "docs/paper4_continuation/rbdp/results")
SOLVER = os.path.join(ROOT, "src/shiftlab/paper4/risk_budget_dp.py")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def meta(script):
    return {"script": os.path.relpath(script, ROOT), "script_sha256": sha(script),
            "solver_sha256": sha(SOLVER)}


def rb(cell, mode, n_beta, w_step_div):
    from shiftlab.paper4.risk_budget_dp import RBDPConfig, solve
    t0 = time.perf_counter()
    r = solve(RBDPConfig(T=cell["T"], B=cell["B"], t01=float(F(cell["t01"])), t10=float(F(cell["t10"])),
                         e0=float(F(cell["e0"])), e1=float(F(cell["e1"])), prior1=float(F(cell["prior"])),
                         c=float(F(cell["c"])), k=float(F(cell["k"])), alpha=float(F(cell["alpha"])),
                         n_beta=n_beta, w_step_div=w_step_div, mode=mode))
    r = {k: v for k, v in r.items()}
    r["wall_s"] = time.perf_counter() - t0
    return r


_REF = r'''
import sys, json
sys.set_int_max_str_digits(0)
sys.path.insert(0, "%s/scripts/paper4_continuation/theory_C")
from gamma_lib import gamma_cell
from fractions import Fraction as F
c = json.loads(sys.argv[1])
out = gamma_cell(c["T"], c["B"], 1, F(c["t01"]), F(c["t10"]), F(c["e0"]), F(c["e1"]),
                 F(c["prior"]), F(c["c"]), F(c["k"]), F(c["alpha"]))
print("@@" + json.dumps({k: out[k] for k in ("L_IID","U_IID","L_causal","U_causal","V_causal_source")}))
'''


def ref(cell, timeout=120):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "-c", _REF % ROOT, json.dumps(cell)], capture_output=True,
                           text=True, timeout=timeout, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "runtime_s": time.time() - t0}
    for line in p.stdout.splitlines():
        if line.startswith("@@"):
            d = json.loads(line[2:]); d.update(status="ok", runtime_s=time.time() - t0); return d
    return {"status": "error", "err": p.stderr[-500:], "runtime_s": time.time() - t0}


_EP = r'''
import sys, json
sys.path.insert(0, "%s/scripts/paper4_continuation/theory_C")
from fractions import Fraction as F
from gamma_lib import make
from shiftlab.dive.eprocess_gated_planner import EProcessGatedPlanner
c = json.loads(sys.argv[1]); th = int(sys.argv[2])
cfg, model = make(c["T"], c["B"], 1, F(c["t01"]), F(c["t10"]), F(c["e0"]), F(c["e1"]), F(c["prior"]), F(c["c"]), F(c["k"]), F(c["alpha"]))
cost, _ = EProcessGatedPlanner(cfg, model, stake=F(1), threshold=F(th)).solve_gated()
print("@@" + json.dumps({"cost": float(cost)}))
'''


def eproc(cell, th, timeout=120):
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, "-c", _EP % ROOT, json.dumps(cell), str(th)], capture_output=True,
                           text=True, timeout=timeout, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "runtime_s": time.time() - t0}
    for line in p.stdout.splitlines():
        if line.startswith("@@"):
            d = json.loads(line[2:]); d.update(status="ok", runtime_s=time.time() - t0); return d
    return {"status": "error", "err": p.stderr[-500:], "runtime_s": time.time() - t0}
