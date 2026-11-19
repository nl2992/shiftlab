"""Certified M11 consistency cell at B=3, its minimum horizon, and small r.

One sequential solver worker; resumable JSONL output, refuse-overwrite result.
This tests a point inside the explicit fixed-B and simultaneous finite-range
regions. It is a consistency check, not a proof premise.
"""
from __future__ import annotations

import hashlib
import json
import os
import signal
import sys
import time
from fractions import Fraction as F

sys.set_int_max_str_digits(0)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "paper4_continuation", "theory_C"))
PARTIAL = os.path.join(ROOT, "outputs/paper4_theory_v2/wpM_b3_general_B_partial.jsonl")
OUT = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_b3_general_B_T9_r1e5_g49_v1.json")
CELL = dict(t=F(100001, 200000), T=9, B=3, d=1, e=F(3, 20))
TIMEOUT_S = 1800


class CellTimeout(Exception):
    pass


def timeout_handler(_signum, _frame):
    raise CellTimeout(f"cell exceeded {TIMEOUT_S}s")


def run_cell():
    import gamma_lib as g
    from shiftlab.paper4.frontier_cuts_fast import frontier_cut_generation_fast

    # The default wrapper caps FCG-fast at 100 cuts. This difficult in-region
    # cell receives a bounded 1,000-cut allowance; exact certification is still
    # performed by the same solver after convergence.
    g.frontier_cut_generation_fast = lambda config, model: frontier_cut_generation_fast(
        config, model, max_iters=1000)

    t0 = time.time()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_S)
    try:
        result = g.gamma_cell(
            CELL["T"], CELL["B"], CELL["d"], CELL["t"], CELL["t"],
            CELL["e"], 1-CELL["e"], prior=F(1, 2), c=F(0), k=F(0), alpha=F(1, 10))
        elapsed = round(time.time()-t0, 1)
        signal.alarm(0)
        voi_lo = F(CELL["T"], 2)-F(result["U_IID"])
        voi_hi = F(CELL["T"], 2)-F(result["L_IID"])
        gamma_lo, gamma_hi = F(result["Gamma_lo"]), F(result["Gamma_hi"])
        assert 0 < voi_lo <= voi_hi and 0 < gamma_lo <= gamma_hi
        return dict(t=str(CELL["t"]), r=str(2*CELL["t"]-1), e=str(CELL["e"]), g="49/100",
                    T=CELL["T"], B=CELL["B"], d=CELL["d"], alpha="1/10",
                    Gamma=[float(gamma_lo), float(gamma_hi)],
                    Gamma_exact=[str(gamma_lo), str(gamma_hi)],
                    VOI_IID=[float(voi_lo), float(voi_hi)],
                    VOI_IID_exact=[str(voi_lo), str(voi_hi)],
                    rho=[float(gamma_lo/voi_hi), float(gamma_hi/voi_lo)],
                    rho_exact=[str(gamma_lo/voi_hi), str(gamma_hi/voi_lo)],
                    certified_positive=True, solver_source=result.get("V_causal_source"),
                    runtime_s=elapsed, status="ok")
    except CellTimeout as exc:
        signal.alarm(0)
        return dict(t=str(CELL["t"]), r=str(2*CELL["t"]-1), e=str(CELL["e"]), g="49/100",
                    T=CELL["T"], B=CELL["B"], d=CELL["d"], alpha="1/10",
                    status="timeout", runtime_s=TIMEOUT_S, detail=str(exc))
    except Exception as exc:
        signal.alarm(0)
        return dict(t=str(CELL["t"]), r=str(2*CELL["t"]-1), e=str(CELL["e"]), g="49/100",
                    T=CELL["T"], B=CELL["B"], d=CELL["d"], alpha="1/10",
                    status="error", runtime_s=round(time.time()-t0, 1),
                    detail=f"{type(exc).__name__}: {exc}")


def main():
    if os.path.exists(OUT):
        raise SystemExit(f"refusing to overwrite {OUT}")
    os.makedirs(os.path.dirname(PARTIAL), exist_ok=True)
    done = []
    if os.path.exists(PARTIAL):
        with open(PARTIAL) as fh:
            done = [json.loads(line) for line in fh if line.strip()]
    row = next((x for x in done if x.get("T") == CELL["T"] and x.get("B") == CELL["B"]
                and x.get("r") == str(2*CELL["t"]-1) and x.get("g") == "49/100"), None)
    if row is None:
        row = run_cell()
        with open(PARTIAL, "a") as fh:
            fh.write(json.dumps(row) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    payload = dict(script_sha256=hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
                   timeout_s=TIMEOUT_S, cells=[row])
    with open(OUT, "x") as fh:
        json.dump(payload, fh, indent=1)
    print(row, flush=True)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
