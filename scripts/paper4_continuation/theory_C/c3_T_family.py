"""C3: Gamma along T for the anti-persistent family (B, d=1, t01=t10=tr, emissions e,1-e).

usage: c3_T_family.py OUT.json B tr_num tr_den e_num e_den T1 T2 ... [--budget S]
"""

from __future__ import annotations

import sys
import time
from fractions import Fraction as F

from gamma_lib import gamma_cell, save_refuse_overwrite


def main():
    args = sys.argv[1:]
    budget = 540.0
    if "--budget" in args:
        i = args.index("--budget")
        budget = float(args[i + 1])
        args = args[:i] + args[i + 2:]
    out, B = args[0], int(args[1])
    tr = F(int(args[2]), int(args[3]))
    e = F(int(args[4]), int(args[5]))
    Ts = [int(a) for a in args[6:]]
    started = time.time()
    rows = []
    for T in Ts:
        if time.time() - started > budget:
            rows.append({"T": T, "skipped": "time budget"})
            continue
        t0 = time.time()
        r = gamma_cell(T, B, 1, tr, tr, e, 1 - e, F(1, 2), F(1, 100), F(1, 10), F(1, 10),
                       force_fcg=True)
        r["seconds"] = time.time() - t0
        rows.append(r)
        print(T, r["Gamma_lo"], r["Gamma_hi"], r["L_IID"], r["U_causal"], round(r["seconds"], 1),
              flush=True)
    save_refuse_overwrite(out, {"script": "scripts/paper4_continuation/theory_C/c3_T_family.py",
                                "argv": sys.argv[1:], "rows": rows})


if __name__ == "__main__":
    main()
