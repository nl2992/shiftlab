"""One certified B=2, T=17 cell at t=9/10; one worker, resumable, refuse-overwrite."""
from __future__ import annotations

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
PARTIAL = os.path.join(ROOT, "outputs/paper4_theory_v2/wpM_b2_t17_t9_partial.jsonl")
OUT = os.path.join(ROOT, "docs/paper4_continuation/theory_v2/results/wpM_b2_t17_t9_v1.json")
TIMEOUT_S = 3600
CELL = dict(t=F(9, 10), T=17)


def worker(conn):
    try:
        from gamma_lib import gamma_cell

        t, T = CELL["t"], CELL["T"]
        result = gamma_cell(T, 2, 1, t, t, F(1, 10), F(9, 10), prior=F(1, 2),
                            c=F(0), k=F(0), alpha=F(1, 10))
        voi_lo = F(T, 2) - F(result["U_IID"])
        voi_hi = F(T, 2) - F(result["L_IID"])
        lo, hi = F(result["Gamma_lo"]), F(result["Gamma_hi"])
        assert 0 < voi_lo <= voi_hi
        conn.send(("ok", dict(t=str(t), T=T, B=2, d=1, alpha="1/10",
                               Gamma=[float(lo), float(hi)], Gamma_exact=[str(lo), str(hi)],
                               VOI=[float(voi_lo), float(voi_hi)],
                               VOI_exact=[str(voi_lo), str(voi_hi)],
                               rho=[float(lo / voi_hi), float(hi / voi_lo)],
                               rho_exact=[str(lo / voi_hi), str(hi / voi_lo)],
                               certified_positive=lo > 0,
                               source=result.get("V_causal_source"))))
    except Exception as exc:  # noqa: BLE001
        conn.send(("error", repr(exc)))
    finally:
        conn.close()


def main():
    if os.path.exists(OUT):
        sys.exit(f"refusing to overwrite {OUT}")
    os.makedirs(os.path.dirname(PARTIAL), exist_ok=True)
    done = {}
    if os.path.exists(PARTIAL):
        with open(PARTIAL) as fh:
            for line in fh:
                row = json.loads(line)
                if row.get("status") == "ok":
                    done[(row["t"], row["T"])] = row
    if (str(CELL["t"]), CELL["T"]) not in done:
        recv, send = mp.get_context("spawn").Pipe(duplex=False)
        proc = mp.get_context("spawn").Process(target=worker, args=(send,))
        start = time.time()
        proc.start()
        send.close()
        proc.join(TIMEOUT_S)
        if proc.is_alive():
            proc.terminate()
            proc.join()
            status, value = "timeout", None
        elif recv.poll():
            status, value = recv.recv()
        else:
            status, value = "error", f"worker exited {proc.exitcode} without a result"
        recv.close()
        row = value if status == "ok" else dict(t=str(CELL["t"]), T=CELL["T"], B=2,
                                                 status=status, error=value)
        row["status"] = status
        row["runtime_s"] = round(time.time() - start, 1)
        with open(PARTIAL, "a") as partial:
            partial.write(json.dumps(row) + "\n")
            partial.flush()
        print(row, flush=True)
        if status != "ok":
            print("incomplete; partial file retained for resume", flush=True)
            return
        done[(row["t"], row["T"])] = row
    payload = dict(script_sha256=hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
                   timeout_s=TIMEOUT_S, cells=list(done.values()))
    with open(OUT, "x") as out:
        json.dump(payload, out, indent=1)
    print("wrote", OUT, flush=True)


if __name__ == "__main__":
    main()
