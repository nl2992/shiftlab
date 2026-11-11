"""Certified B=3 horizon extension for the general-B attempt (descriptive).

Cells: symmetric stationary anti-persistent chains, t in {2/3, 3/4}, e=(1/10, 9/10), d=1, c=k=0, alpha=1/10,
B=3, T=13..15. 2 worker processes. Resumes from a partial JSONL; final compact JSON is refuse-overwrite.

    WPMB3_PARTIAL=<path> nice -n 10 .venv/bin/python scripts/paper4_continuation/theory_v2/wpM_b3ext.py
"""
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
from fractions import Fraction as F

sys.set_int_max_str_digits(0)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "paper4_continuation", "theory_C"))
PARTIAL = os.environ.get("WPMB3_PARTIAL", os.path.join(ROOT, "outputs/paper4_theory_v2/wpM_b3ext_partial.jsonl"))
OUT = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_b3ext_v1.json")
NPROC = 2
CELLS = [dict(t=t, T=T) for T in (13, 14, 15) for t in (F(2, 3), F(3, 4))]


def run(cell):
    import gamma_lib as g
    t, T = cell["t"], cell["T"]
    t0 = time.time()
    o = g.gamma_cell(T, 3, 1, t, t, F(1, 10), F(9, 10), prior=F(1, 2), c=F(0), k=F(0), alpha=F(1, 10))
    voi = F(T, 2) - F(o["U_IID"])
    lo, hi = F(o["Gamma_lo"]), F(o["Gamma_hi"])
    return dict(t=str(t), T=T, B=3, d=1, alpha="1/10", Gamma=[float(lo), float(hi)], VOI=float(voi),
                rho=[float(lo / voi), float(hi / voi)], certified_positive=lo > 0, source=o.get("V_causal_source"),
                runtime_s=round(time.time() - t0, 1), status="ok")


def main():
    if os.path.exists(OUT):
        sys.exit(f"refusing to overwrite {OUT}")
    os.makedirs(os.path.dirname(PARTIAL), exist_ok=True)
    done = {}
    if os.path.exists(PARTIAL):
        for line in open(PARTIAL):
            r = json.loads(line)
            done[(r["t"], r["T"])] = r
    todo = [c for c in CELLS if (str(c["t"]), c["T"]) not in done]
    print(f"{len(done)} resumed, {len(todo)} to run", flush=True)
    with mp.get_context("spawn").Pool(NPROC) as pool, open(PARTIAL, "a") as pf:
        for r in pool.imap_unordered(run, todo):
            pf.write(json.dumps(r) + "\n"); pf.flush()
            done[(r["t"], r["T"])] = r
            print(r["t"], r["T"], r["rho"], r["runtime_s"], flush=True)
    sha = hashlib.sha256(open(__file__, "rb").read()).hexdigest()
    with open(OUT, "x") as fh:
        json.dump(dict(script_sha256=sha, cells=sorted(done.values(), key=lambda r: (r["t"], r["T"]))), fh, indent=1)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
