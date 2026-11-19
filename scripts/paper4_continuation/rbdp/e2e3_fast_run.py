"""E3/E3b/E2 with the fast lattice-exact solver (risk_budget_dp_fast, lattice_exact=True).
Appends one JSON line per task to docs/paper4_continuation/rbdp/results/e2e3_fast_cells.jsonl.
Usage: uv run --no-sync python scripts/paper4_continuation/rbdp/e2e3_fast_run.py [deadline_minutes]"""
import os, sys, json, time, hashlib
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[v] = "1"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
from fractions import Fraction as Fr
from multiprocessing import Pool
from shiftlab.paper4 import risk_budget_dp_fast as FS

SCRIPT = os.path.abspath(__file__)
SOLVER = os.path.join(ROOT, "src/shiftlab/paper4/risk_budget_dp_fast.py")
OUT = os.path.join(ROOT, "docs/paper4_continuation/rbdp/results/e2e3_fast_cells.jsonl")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
TS = ["2/3", "3/4", "9/10"]
T32 = [4, 6, 8, 10, 12, 16, 20, 24, 32]

def tasks():
    q = []
    e3 = lambda t, B, T: ("E3", dict(t=t, e="1/10", B=B, T=T, n_beta=401))
    for B in range(1, 7):
        for T in T32:
            for t in TS: q.append(e3(t, B, T))
    for nb in (401, 801):
        for B in range(1, 7):
            for T in (16, 20, 32): q.append(("E3b", dict(t="63/125", e="3/20", B=B, T=T, n_beta=nb)))
    for T in (16, 32, 64, 128, 256):
        q.append(("E2", dict(t="3/4", e="1/10", B=3, T=T, n_beta=401)))
    for B in (1, 2, 4, 6, 8):
        q.append(("E2", dict(t="3/4", e="1/10", B=B, T=32, n_beta=401)))
    for B in range(1, 7):
        for T in (48, 64):
            for t in TS: q.append(e3(t, B, T))
    for B in range(1, 7):
        for t in TS: q.append(e3(t, B, 100))
    for B in (7, 8):
        for T in (16, 32, 64, 100): q.append(e3("3/4", B, T))
    for B in (1, 2, 3, 4, 5):
        q.append(e3("3/4", B, 200))
    for B in (7, 8):
        for T in (16, 32, 64, 100):
            for t in ("2/3", "9/10"): q.append(e3(t, B, T))
    return [x for x in q if x[1]["B"] <= x[1]["T"]]

def key(kind, p): return (kind, p["t"], p["e"], p["B"], p["T"], p["n_beta"])
def cfg(p, mode, **kw):
    t = float(Fr(p["t"])); e = float(Fr(p["e"]))
    return FS.RBDPConfig(T=p["T"], B=p["B"], t01=t, t10=t, e0=e, e1=1 - e, alpha=0.1, n_beta=p["n_beta"], mode=mode, lattice_exact=True, **kw)

def run(args):
    (kind, p), deadline = args
    if time.time() > deadline: return None
    rec = dict(kind=kind, **p)
    t0 = time.perf_counter()
    if kind == "E2":
        r = FS.solve(cfg(p, "causal")); rec["full"] = r
        rec["full_solve_s"] = r["time_total"]
        r2 = FS.solve(cfg(p, "causal", compute_upper=False)); rec["L_only"] = r2
        rec["L_only_s"] = r2["time_total"]
        r3 = FS.solve(cfg(p, "causal", compute_lower=False)); rec["U_only_s"] = r3["time_total"]
    else:
        for m in ("causal", "iid"):
            rec[m] = FS.solve(cfg(p, m))
        C0 = rec["causal"]["C0"]; Lc, Uc, Li, Ui = (rec["causal"]["L"], rec["causal"]["U"], rec["iid"]["L"], rec["iid"]["U"])
        rec.update(C0=C0, VOI_causal=C0 - Uc, VOI_iid=C0 - Ui, Gamma=Uc - Ui, rho_Gamma=(Uc - Ui) / (C0 - Ui),
                   rho_lo=(Lc - Ui) / (C0 - Li), rho_hi=(Uc - Li) / (C0 - Ui))
    rec["runtime_s"] = time.perf_counter() - t0
    rec.update(alpha=0.1, d=1, c=0, k=0, script_sha256=sha(SCRIPT), solver_sha256=sha(SOLVER))
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n"); f.flush(); os.fsync(f.fileno())
    return key(kind, p)

if __name__ == "__main__":
    mins = float(sys.argv[1]) if len(sys.argv) > 1 else 25
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
