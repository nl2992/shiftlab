"""Delay-2 long-horizon study (RB-DP d=2 solver), mirroring the delay-1 cell conventions of e2e3_fast_run.py.

Cells: symmetric chain t01 = t10 = t, e0 = e, e1 = 1 - e, prior1 = 0.5, c = k = 0, alpha = 1/10, risk grid N = 10 * 2^B.
Each (cell, mode) is solved in its own subprocess with a timeout. Output is appended to JSONL, resumable.

Commands (all deterministic, no seeds):
  sanity                      compare U with gamma_cell(d=2) on T <= 7 cells
  time T B t [n_beta]         time one cell (both modes), no output file
  reachgrid                   extra: reach belief grid on the whole B<=3 grid -> sens file
  sens801                     extra n_beta=801 cells -> sens file
  sens                        belief-grid sensitivity cells -> d2_longhorizon_sens.jsonl
  grid [minutes] [workers]    main grid -> d2_longhorizon_cells.jsonl
  one-solve (internal)        used by the subprocess
"""
from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction as Fr
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_v] = "1"

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/paper4_continuation/theory_C"))
RES = ROOT / "docs/paper4_continuation/rbdp/results"
CELLS = RES / "d2_longhorizon_cells.jsonl"
SENS = RES / "d2_longhorizon_sens.jsonl"
SELF = Path(__file__).resolve()
TS = ["2/3", "3/4", "9/10"]
TIMEOUT_S = 30 * 60
ALPHA_DEN = 10


def make_cfg(p: dict, mode: str):
    from shiftlab.paper4.risk_budget_dp_d2 import RBDP2Config

    t = float(Fr(p["t"]))
    e = float(Fr(p["e"]))
    return RBDP2Config(T=p["T"], B=p["B"], t01=t, t10=t, e0=e, e1=1 - e, prior1=0.5, c=0.0, k=0.0, alpha=0.1,
                       n_w_override=ALPHA_DEN * 2 ** p["B"], mode=mode, belief_grid=p["belief_grid"],
                       n_beta=p["n_beta"], max_reach_states=p.get("max_reach_states", 4000),
                       table_dir=os.environ.get("D2_TABLE_DIR") or None)


def one_solve(p: dict, mode: str) -> dict:
    from shiftlab.paper4.risk_budget_dp_d2 import solve

    return solve(make_cfg(p, mode))


MEM_CAP_EXIT = 97
PEAK = [0]


def phys_footprint_bytes() -> int:
    """Physical footprint of this process (macOS proc_pid_rusage; includes compressed memory). 0 if unavailable."""
    try:
        lib = ctypes.CDLL("/usr/lib/libproc.dylib")
        buf = (ctypes.c_uint64 * 64)()
        if lib.proc_pid_rusage(os.getpid(), 2, ctypes.byref(buf)) != 0:
            return 0
        return int(buf[9])  # 16-byte uuid, then user, system, pkg wkups, intr wkups, pageins, wired, resident, footprint
    except Exception:  # noqa: BLE001
        return 0


def start_mem_guard() -> None:
    """Abort this solve (exit code 97) once its footprint passes D2_MEM_CAP_GB (default 5 GB)."""
    cap = float(os.environ.get("D2_MEM_CAP_GB", "5")) * 2**30

    def watch() -> None:
        while True:
            fp = phys_footprint_bytes()
            PEAK[0] = max(PEAK[0], fp)
            if fp > cap:
                sys.stderr.write(f"MEMCAP: footprint {fp / 2**30:.2f} GB > cap {cap / 2**30:.2f} GB\n")
                sys.stderr.flush()
                os._exit(MEM_CAP_EXIT)
            time.sleep(0.5)

    threading.Thread(target=watch, daemon=True).start()


def run_sub(p: dict, mode: str, timeout: float) -> dict:
    """Run one solve in a subprocess; returns dict with status."""
    t0 = time.perf_counter()
    env = dict(os.environ)
    tdir = None
    if os.environ.get("D2_TABLES_ON_DISK"):  # per-solve directory for memory-mapped tables, removed afterwards
        tdir = tempfile.mkdtemp(prefix="d2_tables_")
        env["D2_TABLE_DIR"] = tdir
    try:
        cp = subprocess.run(["uv", "run", "--no-sync", "python", str(SELF), "one-solve", json.dumps(p), mode],
                            capture_output=True, text=True, timeout=timeout, cwd=str(ROOT), env=env)
    except subprocess.TimeoutExpired:
        return dict(status="timeout", wall_s=time.perf_counter() - t0, timeout_s=timeout)
    finally:
        if tdir:
            shutil.rmtree(tdir, ignore_errors=True)
    wall = time.perf_counter() - t0
    if cp.returncode == MEM_CAP_EXIT:
        return dict(status="memcap", wall_s=wall, stderr=cp.stderr[-500:])
    if cp.returncode != 0:
        return dict(status="error", wall_s=wall, stderr=cp.stderr[-2000:])
    try:
        out = json.loads(cp.stdout.strip().splitlines()[-1])
    except Exception as ex:  # noqa: BLE001
        return dict(status="error", wall_s=wall, stderr=f"parse: {ex}; {cp.stdout[-500:]}")
    out["status"] = "ok"
    out["wall_s"] = wall
    return out


def run_cell(p: dict, timeout: float = TIMEOUT_S) -> dict:
    rec = dict(p)
    for mode in ("causal", "iid"):
        rec[mode] = run_sub(p, mode, timeout)
        if rec[mode]["status"] != "ok":
            break
    sts = [rec[m]["status"] for m in ("causal", "iid") if m in rec]
    rec["status"] = "ok" if sts == ["ok", "ok"] else next(s for s in sts if s != "ok")
    if rec["status"] == "ok":
        c, i = rec["causal"], rec["iid"]
        rec["C0"] = c["C0"]
        rec["V_causal"], rec["V_iid"] = c["U"], i["U"]
        rec["Gamma"] = c["U"] - i["U"]
        rec["rho_Gamma"] = rec["Gamma"] / (c["C0"] - i["U"]) if c["C0"] - i["U"] > 0 else None
        rec["risk_causal_of_causal_policy"] = c["risk_causal"]
        rec["risk_causal_of_iid_policy"] = i["risk_causal"]
    return rec


def append(path: Path, rec: dict) -> None:
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")
        f.flush()
        os.fsync(f.fileno())


def cell(t: str, B: int, T: int, nb: int, bg: str) -> dict:
    return dict(t=t, e="1/10", B=B, T=T, n_beta=nb, belief_grid=bg, alpha="1/10", c=0, k=0, delay=2, N=ALPHA_DEN * 2 ** B)


def key(r: dict) -> tuple:
    return (r["t"], r["B"], r["T"], r["n_beta"], r["belief_grid"])


def done_keys(path: Path) -> set:
    return {key(json.loads(line)) for line in open(path)} if path.exists() else set()


def pool_run(cells: list[dict], path: Path, minutes: float, workers: int, timeout: float = TIMEOUT_S) -> None:
    deadline = time.time() + minutes * 60
    dk = done_keys(path)
    todo = [c for c in cells if key(c) not in dk]
    print(len(todo), "cells to run", flush=True)

    def work(c: dict):
        rem = deadline - time.time()
        if rem < 60:
            return None
        rec = run_cell(c, min(timeout, rem))
        rec["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        append(path, rec)
        print(key(rec), rec["status"], rec.get("rho_Gamma"), flush=True)
        return rec

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(work, todo))


def main_grid(belief_grid: str, n_beta: int, minutes: float, workers: int, with_b4: bool) -> None:
    cells = []
    for B in (1, 2, 3):
        for T in (8, 12, 16, 24, 32, 48, 64, 100):
            for t in TS:
                cells.append(cell(t, B, T, n_beta, belief_grid))
    if with_b4:
        for T in (8, 12, 16):
            for t in TS:
                cells.append(cell(t, 4, T, n_beta, belief_grid))
    # increasing cost order: B then T (already), so B=3 comes last
    cells.sort(key=lambda c: (c["B"], c["T"]))
    pool_run(cells, CELLS, minutes, workers)


def sanity() -> None:
    from gamma_lib import gamma_cell

    out = []
    for (T, B, t) in ((5, 2, "3/4"), (6, 3, "2/3"), (7, 2, "9/10")):
        p = dict(cell(t, B, T, 101, "auto"))
        ref = gamma_cell(T, B, 2, Fr(t), Fr(t), Fr("1/10"), Fr("9/10"), prior=Fr(1, 2), c=Fr(0), k=Fr(0), alpha=Fr(1, 10))
        for mode, k in (("iid", "U_IID"), ("causal", "U_causal")):
            r = one_solve(p, mode)
            ex = float(Fr(ref[k]))
            out.append(dict(T=T, B=B, t=t, mode=mode, U=r["U"], exact=ex, diff=r["U"] - ex,
                            belief_grid=r["belief_grid"], risk_causal=r["risk_causal"]))
            print(out[-1], flush=True)
    json.dump(out, open(RES / "d2_longhorizon_sanity.json", "w"), indent=1)


def sens_cells() -> list[dict]:
    cs = []
    for T in (16, 32):
        for B in (2, 3):
            for t in TS:
                for nb in (201, 401):
                    cs.append(cell(t, B, T, nb, "uniform"))
                cs.append(cell(t, B, T, 0, "reach"))
    return cs


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "one-solve":
        start_mem_guard()
        _out = one_solve(json.loads(a[1]), a[2])
        _out["peak_footprint_gb"] = max(PEAK[0], phys_footprint_bytes()) / 2**30
        print(json.dumps(_out))
    elif a[0] == "sanity":
        sanity()
    elif a[0] == "time":
        T, B, t = int(a[1]), int(a[2]), a[3]
        nb = int(a[4]) if len(a) > 4 else 201
        bg = a[5] if len(a) > 5 else "uniform"
        r = run_cell(cell(t, B, T, nb, bg), float(a[6]) if len(a) > 6 else TIMEOUT_S)
        print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk.startswith(("time", "wall", "status", "n_", "U", "belief"))}) for k, v in r.items()}))
    elif a[0] == "sens":
        pool_run(sens_cells(), SENS, float(a[1]) if len(a) > 1 else 90, int(a[2]) if len(a) > 2 else 4,
                 float(a[3]) if len(a) > 3 else TIMEOUT_S)
    elif a[0] == "sens801":  # extra: n_beta = 801 at T in {32, 64}, B in {2, 3}
        cs = [cell(t, B, T, 801, "uniform") for T in (32, 64) for B in (2, 3) for t in TS]
        cs += [cell(t, B, 64, 401, "uniform") for B in (2, 3) for t in TS]  # 401 at T=64 already in grid; keys dedupe in analysis
        pool_run([c for c in cs if c["n_beta"] == 801], SENS, 60, 4)
    elif a[0] == "reachgrid":  # extra: exact-belief ("reach") re-run of the whole B<=3 grid, 600 s per mode, 40 min pool
        cs = sorted((cell(t, B, T, 0, "reach") for B in (1, 2, 3) for T in (8, 12, 16, 24, 32, 48, 64, 100) for t in TS),
                    key=lambda c: (c["B"], c["T"]))
        pool_run(cs, SENS, 40, 4, 600)
    elif a[0] == "grid":
        # grid <belief_grid> <n_beta> <minutes> <workers> [b4]
        main_grid(a[1], int(a[2]), float(a[3]), int(a[4]), len(a) > 5 and a[5] == "b4")
    else:
        raise SystemExit(__doc__)
