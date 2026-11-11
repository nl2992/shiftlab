"""wpG scan: relative premium rho = Gamma / (C0 - V_IID) for deterministic alternation (t = 1), d = 1, c = k = 0,
calendar 1..B, via the fixed-calendar LP of wpG_lib (float HiGHS).  Part 'check' compares against the exact
certified gamma_cell on small cells.  Descriptive / numerical; not confirmatory.

usage: uv run --no-sync python scripts/paper4_continuation/theory_v2/wpG_scan.py OUT.json MODE [args]
  MODE check                 -> exact cross-check vs gamma_cell (t = 1 cells and t = 9/10 calendar-gap cells)
  MODE grid E BMAX           -> t = 1 grid for e = E (fraction string), B = 1..BMAX
"""

import hashlib
import json
import sys
import time
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "theory_C"))
from wpG_lib import gamma  # noqa: E402

ALPHAS = [F(1, 20), F(1, 10), F(1, 4), F(1, 2)]


def check():
    from gamma_lib import gamma_cell

    rows = []
    cells = [
        (3, 1, F(1, 10), F(1, 10)), (4, 1, F(1, 10), F(1, 10)), (4, 2, F(1, 10), F(1, 10)),
        (4, 2, F(1, 10), F(1, 20)), (5, 2, F(1, 10), F(1, 4)), (5, 3, F(1, 10), F(1, 10)),
        (6, 3, F(1, 10), F(1, 20)), (6, 4, F(1, 10), F(1, 10)), (7, 4, F(1, 10), F(1, 20)),
        (5, 3, F(1, 5), F(1, 2)), (6, 4, F(1, 5), F(1, 4)), (7, 5, F(1, 10), F(1, 2)),
        (7, 3, F(1, 5), F(1, 20)), (8, 5, F(1, 10), F(1, 20)),
    ]
    for T, B, e, a in cells:
        t0 = time.time()
        g = gamma_cell(T, B, 1, 1, 1, e, 1 - e, F(1, 2), 0, 0, a)
        m = gamma(T, B, 1.0, float(e), float(a))
        rows.append(dict(T=T, B=B, t="1", e=str(e), alpha=str(a),
                         exact_V_IID=[g["L_IID"], g["U_IID"]], exact_V_causal=[g["L_causal"], g["U_causal"]],
                         exact_Gamma=[g["Gamma_lo_f"], g["Gamma_hi_f"]], cal_V_IID=m["V_IID"],
                         cal_V_causal=m["V_causal"], cal_Gamma=m["Gamma"], cal_rho=m["rho"],
                         dIID=abs(m["V_IID"] - float(F(g["U_IID"]))),
                         dC=abs(m["V_causal"] - float(F(g["U_causal"]))), sec=time.time() - t0))
        print(rows[-1], flush=True)
    return rows


def grid(e, bmax):
    rows = []
    for B in range(1, bmax + 1):
        dts = list(range(1, 9)) + ([30, 31] if B <= 12 else [])
        for dT in dts:
            for a in ALPHAS:
                t0 = time.time()
                m = gamma(B + dT, B, 1.0, float(e), float(a))
                m.update(alpha=str(a), e=str(e), t="1", sec=time.time() - t0)
                rows.append(m)
        print("B", B, "done", flush=True)
    return rows


def main():
    out = Path(sys.argv[1])
    if out.exists():
        print(f"refusing to overwrite {out}", file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[2]
    t0 = time.time()
    if mode == "check":
        rows = check()
    else:
        rows = grid(F(sys.argv[3]), int(sys.argv[4]))
    payload = dict(script=str(Path(__file__).resolve()),
                   script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   lib_sha256=hashlib.sha256((HERE / "wpG_lib.py").read_bytes()).hexdigest(),
                   argv=sys.argv[1:], elapsed_s=time.time() - t0,
                   note="t=1, d=1, c=k=0, prior 1/2, e1=1-e; calendar 1..B float LP; descriptive", rows=rows)
    out.write_text(json.dumps(payload, indent=1, default=str))
    print("wrote", out)


if __name__ == "__main__":
    main()
