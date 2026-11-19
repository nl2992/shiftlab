"""Driver for E3 (long-horizon premium), E3b (theorem rectangle), E2 (scaling). 3 worker processes.
Each finished task is appended to docs/paper4_continuation/rbdp/results/e2e3_cells.jsonl immediately.
Usage: uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_run.py [deadline_minutes]"""
import os, sys, json, time
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[v] = "1"
sys.path.insert(0, os.path.dirname(__file__))
from multiprocessing import Pool
from e2e3_common import *

SCRIPT = os.path.abspath(__file__)
OUT = os.path.join(RES, "e2e3_cells.jsonl")
TS = ["2/3", "3/4", "9/10"]
T32 = [4, 6, 8, 10, 12, 16, 20, 24, 32]

def tasks():
    q = []
    e3 = lambda t, B, T, nb=201: ("E3", dict(t=t, e="1/10", B=B, T=T, n_beta=nb, wdiv=20))
    for B in (1, 2, 3, 4):
        for T in T32:
            for t in TS: q.append(e3(t, B, T))
    for B in range(1, 7):                                   # E3b rectangle, default grid
        for T in (16, 20, 32):
            q.append(("E3b", dict(t="63/125", e="3/20", B=B, T=T, n_beta=401, wdiv=20)))
    for B in (5, 6):
        for T in T32:
            for t in TS: q.append(e3(t, B, T))
    for B in (1, 2, 3, 4):
        for t in TS: q.append(e3(t, B, 48))
    for (B, T, nb, wd) in [(2, 16, 801, 40), (3, 16, 801, 40)]:
        q.append(("E3b_sens", dict(t="63/125", e="3/20", B=B, T=T, n_beta=nb, wdiv=wd)))
    for T in (16, 32, 64, 128):
        q.append(("E2", dict(t="3/4", e="1/10", B=3, T=T, n_beta=401, wdiv=20)))
    for B in (1, 2, 4, 6, 8):
        q.append(("E2", dict(t="3/4", e="1/10", B=B, T=32, n_beta=401, wdiv=20)))
    for B in (1, 2, 3, 4):
        for t in TS: q.append(e3(t, B, 64))
    q.append(("E2", dict(t="3/4", e="1/10", B=3, T=256, n_beta=401, wdiv=20)))
    for B in (5, 6):
        for T in (48, 64):
            for t in TS: q.append(e3(t, B, T))
    for B in (1, 2, 3, 4):
        for t in TS: q.append(e3(t, B, 100))
    for T in (16, 32, 64):
        for t in TS: q.append(e3(t, 8, T))
    return [x for x in q if x[1]["B"] <= x[1]["T"]]   # solver requires B <= T

def key(kind, p): return (kind, p["t"], p["e"], p["B"], p["T"], p["n_beta"], p["wdiv"])

def run(args):
    (kind, p), deadline = args
    if time.time() > deadline: return None
    if kind == "E2":
        rec = dict(kind=kind, **p)
        c = cfg_of(p["t"], p["e"], p["T"], p["B"], "causal", p["n_beta"], p["wdiv"])
        r = R.solve(c)
        rec.update(full_solve_s=r["time_total"], upper_only_s=r["time_setup"] + r["time_post"] + r["time_upper"] + r["time_eval"],
                   lower_dp_s=r["time_lower"], time_breakdown={k: r[k] for k in r if k.startswith("time_")},
                   L=r["L"], U=r["U"], n_pre_nodes=r["n_pre_nodes"], n_post_nodes=r["n_post_nodes"], mode="causal")
    else:
        rec = dict(kind=kind, **p)
        t0 = time.perf_counter()
        for m in ("causal", "iid"):
            r = upper_only(cfg_of(p["t"], p["e"], p["T"], p["B"], m, p["n_beta"], p["wdiv"]))
            rec[m] = r
        C0 = rec["causal"]["C0"]
        Uc, Ui = rec["causal"]["U"], rec["iid"]["U"]
        rec.update(C0=C0, VOI_causal=C0 - Uc, VOI_iid=C0 - Ui, Gamma=Uc - Ui,
                   rho_Gamma=(Uc - Ui) / (C0 - Ui) if C0 - Ui != 0 else None,
                   runtime_s=time.perf_counter() - t0)
    rec["alpha"] = 0.1; rec["d"] = 1; rec["c"] = 0; rec["k"] = 0
    append(OUT, rec, SCRIPT)
    return key(kind, p)

if __name__ == "__main__":
    mins = float(sys.argv[1]) if len(sys.argv) > 1 else 40
    deadline = time.time() + mins * 60
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l); done.add(key(r["kind"], r))
    todo = [x for x in tasks() if key(*x) not in done]
    print(len(todo), "tasks", flush=True)
    with Pool(3) as pool:
        for k in pool.imap_unordered(run, [(x, deadline) for x in todo], chunksize=1):
            if k: print("done", k, flush=True)
