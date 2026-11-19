"""Single certified B=3 cell inside the M6 open parameter rectangle.

One sequential solver worker, nice 18, resumable JSONL row, and refuse-overwrite
compact result. This is a consistency check, not a proof premise.
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
PARTIAL = os.path.join(ROOT, "outputs/paper4_theory_v2/wpM_b3_open_rect_partial.jsonl")
OUT = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_b3_open_rect_t504_e15_T16_v1.json")
CELL = dict(t=F(63, 125), T=16, B=3, d=1, e=F(3, 20), g=F(49, 100))
TIMEOUT_S = 3600


class CellTimeout(Exception):
    pass


def timeout_handler(_signum, _frame):
    raise CellTimeout(f"cell exceeded {TIMEOUT_S}s")


def run_cell():
    import gamma_lib as g

    cell = CELL
    t0 = time.time()
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_S)
    try:
        result = g.gamma_cell(
            cell["T"], cell["B"], cell["d"], cell["t"], cell["t"],
            cell["e"], 1-cell["e"], prior=F(1, 2), c=F(0), k=F(0), alpha=F(1, 10))
        elapsed = round(time.time()-t0, 1)
        signal.alarm(0)
        vlo, vhi = F(cell["T"], 2)-F(result["U_IID"]), F(cell["T"], 2)-F(result["L_IID"])
        glo, ghi = F(result["Gamma_lo"]), F(result["Gamma_hi"])
        assert 0 < vlo <= vhi and 0 < glo <= ghi
        return dict(t=str(cell["t"]), r=str(2*cell["t"]-1), e=str(cell["e"]), g=str(cell["g"]),
                    T=cell["T"], B=cell["B"], d=cell["d"], alpha="1/10",
                    Gamma=[float(glo), float(ghi)], Gamma_exact=[str(glo), str(ghi)],
                    VOI_IID=[float(vlo), float(vhi)], VOI_IID_exact=[str(vlo), str(vhi)],
                    rho=[float(glo/vhi), float(ghi/vlo)], rho_exact=[str(glo/vhi), str(ghi/vlo)],
                    certified_positive=True, solver_source=result.get("V_causal_source"),
                    runtime_s=elapsed, status="ok")
    except CellTimeout as exc:
        signal.alarm(0)
        return dict(t=str(cell["t"]), r=str(2*cell["t"]-1), e=str(cell["e"]), g=str(cell["g"]),
                    T=cell["T"], B=cell["B"], d=cell["d"], alpha="1/10",
                    status="timeout", runtime_s=TIMEOUT_S, detail=str(exc))


def main():
    if os.path.exists(OUT):
        raise SystemExit(f"refusing to overwrite {OUT}")
    os.makedirs(os.path.dirname(PARTIAL), exist_ok=True)
    done = []
    if os.path.exists(PARTIAL):
        with open(PARTIAL) as fh:
            done = [json.loads(line) for line in fh if line.strip()]
    row = next((x for x in done if x.get("T") == CELL["T"] and x.get("B") == CELL["B"]
                and x.get("t") == str(CELL["t"])), None)
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
