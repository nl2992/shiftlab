"""Evaluate RB-DP cells for a fitted chain (causal and iid mode), each solve in its own subprocess.

Delay 1: risk_budget_dp_fast, lattice_exact=True, alpha=1/10, c=k=0, n_beta=401 (as in e2e3_fast_run.py).
Delay 2: risk_budget_dp_d2, n_w_override=10*2**B, belief_grid="uniform", n_beta=201 (n_beta overridable).
Quantities: U, Gamma = U_causal - U_iid, rho_Gamma = Gamma/(C0 - U_iid), true causal risk of the IID-mode policy.
Internal command: `evaluate.py one-solve '<json cfg>'` prints one JSON line.
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
import threading
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
SELF = Path(__file__).resolve()
TIMEOUT_S = 120
MEM_CAP = 3 * 2**30
GRID_D1 = [(T, B) for T in (16, 32) for B in (1, 2, 3, 4)]
GRID_D2 = [(16, 2), (16, 3)]
PRIMARY = (32, 3)


def _solve_inproc(c: dict) -> dict:
    keys = ("T", "B", "t01", "t10", "e0", "e1", "prior1", "mode")
    kw = {k: c[k] for k in keys}
    if c["delay"] == 1:
        from shiftlab.paper4.risk_budget_dp_fast import RBDPConfig, solve

        cfg = RBDPConfig(alpha=0.1, c=0.0, k=0.0, n_beta=c.get("n_beta", 401), lattice_exact=True, **kw)
        r = solve(cfg)
        return {k: r[k] for k in ("U", "L", "risk_causal", "risk_iid", "C0", "time_total")}
    from shiftlab.paper4.risk_budget_dp_d2 import RBDP2Config, solve

    cfg = RBDP2Config(alpha=0.1, c=0.0, k=0.0, n_w_override=10 * 2 ** c["B"], belief_grid="uniform",
                      n_beta=c.get("n_beta", 201), **kw)
    r = solve(cfg)
    out = {k: r[k] for k in ("U", "risk_causal", "risk_iid", "C0", "time_total")}
    out["L"] = float("nan")
    return out


def _guard() -> None:
    def watch() -> None:
        while True:
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
            if rss > MEM_CAP:
                sys.stderr.write(f"MEMCAP {rss}\n")
                os._exit(97)
            time.sleep(0.5)

    threading.Thread(target=watch, daemon=True).start()


def run_sub(c: dict, timeout: float = TIMEOUT_S) -> dict:
    t0 = time.perf_counter()
    try:
        cp = subprocess.run([sys.executable, str(SELF), "one-solve", json.dumps(c)], capture_output=True,
                            text=True, timeout=timeout, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return dict(status="timeout", wall_s=time.perf_counter() - t0)
    wall = time.perf_counter() - t0
    if cp.returncode == 97:
        return dict(status="memcap", wall_s=wall)
    if cp.returncode != 0:
        return dict(status="error", wall_s=wall, stderr=cp.stderr[-1500:])
    out = json.loads(cp.stdout.strip().splitlines()[-1])
    out.update(status="ok", wall_s=wall)
    return out


def eval_cell(sp: dict, T: int, B: int, delay: int, n_beta: int | None = None, timeout: float = TIMEOUT_S) -> dict:
    """sp: solver params (t01, t10, e0, e1, prior1). Returns a dict with both modes and the derived quantities."""
    base = dict(T=T, B=B, delay=delay, **{k: sp[k] for k in ("t01", "t10", "e0", "e1", "prior1")})
    if n_beta is not None:
        base["n_beta"] = n_beta
    rec = dict(delay=delay, T=T, B=B, n_beta=n_beta if n_beta is not None else (401 if delay == 1 else 201))
    for mode in ("causal", "iid"):
        rec[mode] = run_sub(dict(base, mode=mode), timeout)
        if rec[mode]["status"] != "ok":
            rec["status"] = f"{mode}:{rec[mode]['status']}"
            return rec
    c, i = rec["causal"], rec["iid"]
    C0 = c["C0"]
    rec.update(status="ok", C0=C0, U_causal=c["U"], U_iid=i["U"], L_causal=c["L"], L_iid=i["L"],
               Gamma=c["U"] - i["U"],
               rho_Gamma=(c["U"] - i["U"]) / (C0 - i["U"]) if C0 - i["U"] > 1e-12 else 0.0,
               degenerate_zero_voi=bool(C0 - i["U"] <= 1e-12),
               risk_causal_of_causal_policy=c["risk_causal"], risk_causal_of_iid_policy=i["risk_causal"],
               risk_iid_of_iid_policy=i["risk_iid"], wall_s=c["wall_s"] + i["wall_s"])
    if delay == 1 and c["L"] == c["L"] and i["L"] == i["L"] and C0 - i["U"] > 1e-12 and C0 - i["L"] > 1e-12:
        rec["rho_lo"] = (c["L"] - i["U"]) / (C0 - i["L"])
        rec["rho_hi"] = (c["U"] - i["L"]) / (C0 - i["U"])
    return rec


def eval_chain(sp: dict, delay1: bool = True, delay2: bool = False, cells=None, log=print) -> list[dict]:
    out = []
    if delay1:
        order = [PRIMARY] + [c for c in (cells or GRID_D1) if c != PRIMARY]
        for T, B in order:
            r = eval_cell(sp, T, B, 1)
            out.append(r)
            log(f"  d1 T={T} B={B} {r['status']} rho={r.get('rho_Gamma')} wall={r.get('wall_s')}")
    if delay2:
        for T, B in GRID_D2:
            r = eval_cell(sp, T, B, 2)
            out.append(r)
            log(f"  d2 T={T} B={B} {r['status']} rho={r.get('rho_Gamma')} wall={r.get('wall_s')}")
    return out


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "one-solve":
        _guard()
        print(json.dumps(_solve_inproc(json.loads(sys.argv[2]))))
