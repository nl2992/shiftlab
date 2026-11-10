"""H2 confirmation: flat-null class, certificates B0a,B0w,B0b,B1,B1n,B2 with pilot1 parameters,
alpha=.1, N=1000 streams, seed parts (5303100000, class_idx=2 (null_flat as in pilot1), i)."""

import json
import math
import sys
import time

import numpy as np

sys.path.insert(0, __file__.rsplit("h2_payback.py", 1)[0])
from _common import OUT as COUT
from _common import ledger

from shiftlab.paper3.payback.certificates import *
from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.sim import Spec, make_stream, run_one

BASE = 5303100000
N = 1000
CI = 2  # class index of null_flat in pilot1's CLASSES dict (kept so the seed parts have the same layout)
v, a = 0.002, 0.1
E0 = Envelope(v)
base = {"T": 400, "B": 150, "d": 5, "h": 30, "k": 3.0, "alpha": a}
spec = Spec(**base, env=E0)


def wilson(k, n, z=1.959964):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def main():
    t0 = time.time()
    e, al = spec.env, spec.alpha
    npl = plan_batch_size(e, al / 2, spec.B)
    cs = {
        "B0a": lambda: B0Window(e, al, npl),
        "B0w": lambda: B0Window(e, al, npl, gauss=True),
        "B0b": lambda: B0Forecast(e, al, npl),
        "B1": lambda: B1Certificate(e, al),
        "B1n": lambda: B1NaiveContinuation(e, al),
        "B2": lambda: B2Certificate(e, al),
    }
    streams = [make_stream("null_flat", spec, (BASE, CI, i)) for i in range(N)]
    out = {}
    for name, f in cs.items():
        rs = [run_one(spec, mu, z, f) for mu, z in streams]
        k = sum(r["wrong"] for r in rs)
        c = [r for r in rs if r["certified"]]
        lo, hi = wilson(k, N)
        out[name] = {
            "n": N,
            "wrong": int(k),
            "wrong_rate": k / N,
            "wilson95": [lo, hi],
            "cert_rate": len(c) / N,
            "labels": float(np.mean([r["labels"] for r in rs])),
            "delay": float(np.mean([r["t"] for r in c])) if c else None,
        }
        print(name, out[name], flush=True)
    sup = (
        out["B0w"]["wilson95"][0] > 0.1
        and out["B0b"]["wilson95"][0] > 0.1
        and out["B2"]["wilson95"][1] <= 0.1
    )
    res = {"H2_SUPPORTED": bool(sup), "certs": out}
    (COUT / "h2" / "summary.json").write_text(json.dumps(res, indent=1))
    ledger(
        "H2",
        "confirm_run",
        {"base": BASE, "class_idx": CI, "N": N, "alpha": a, "base_spec": base, "v": v},
        res,
        time.time() - t0,
    )
    print("H2_SUPPORTED", sup)


if __name__ == "__main__":
    main()
