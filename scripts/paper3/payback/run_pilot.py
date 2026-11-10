# ruff: noqa: SIM115, PLW1510
"""Dev pilot of B0/B1/B2 certificates.  usage: run_pilot.py [N] [tag]"""

import datetime
import json
import subprocess
import sys
import time

import numpy as np

from shiftlab.paper3.payback.certificates import *
from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.sim import DEV_BASE, Spec, make_stream, run_one

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
tag = sys.argv[2] if len(sys.argv) > 2 else "pilot1"
v, a = 0.002, 0.1
E0, ED, EH = Envelope(v), Envelope(v, 0.15, 40), Envelope(v, 1.8, 100)
base = {"T": 400, "B": 150, "d": 5, "h": 30, "k": 3.0, "alpha": a}
CLASSES = {  # name: (spec, label, honest-env for B2 on that class)
    "drift": (Spec(**base, env=E0), "in-class"),
    "boundary": (Spec(**base, env=E0), "in-class"),
    "null_flat": (Spec(**base, env=E0), "in-class null"),
    "null_decline:60": (Spec(**base, env=E0), "in-class null (tight)"),
    "dwell": (Spec(**base, env=ED), "in-class (jump J=.15, hd=40)"),
    "stress_reversal": (Spec(**base, env=E0), "STRESS jump .9"),
    "stress_fastdrift": (Spec(**base, env=E0), "STRESS drift 3v"),
    "stress_dep": (Spec(**base, env=E0), "STRESS dependent labels"),
    "stress_flip": (Spec(**{**base, "T": 500, "h": 100}, env=E0), "STRESS flip hp=100 (E case)"),
}


def certs(spec):
    e, al = spec.env, spec.alpha
    npl = plan_batch_size(e, al / 2, spec.B)
    d = {
        "B0a": lambda: B0Window(e, al, npl),
        "B0w": lambda: B0Window(e, al, npl, gauss=True),
        "B0b": lambda: B0Forecast(e, al, npl),
        "B1": lambda: B1Certificate(e, al),
        "B1n": lambda: B1NaiveContinuation(e, al),
        "B2": lambda: B2Certificate(e, al),
    }
    return d


out, t0 = {}, time.time()
for ci, (cname, (spec, label)) in enumerate(CLASSES.items()):
    cs = dict(certs(spec))
    if (
        cname == "stress_flip"
    ):  # honest declaration of the flip class: jump up to 2*amp_max, dwell 100
        eh = Envelope(v, 1.8, 100)
        cs["B2honest"] = lambda: B2Certificate(eh, spec.alpha)  # noqa: B023 (called within the loop iteration)
    streams = [
        make_stream(cname.split(":")[0] if False else cname, spec, (DEV_BASE, ci, i))
        for i in range(N)
    ]
    for name, f in cs.items():
        rs = [run_one(spec, mu, z, f) for mu, z in streams]
        c = [r for r in rs if r["certified"]]
        out[f"{cname}|{name}"] = {
            "cls": cname,
            "cert": name,
            "n": N,
            "cert_rate": len(c) / N,
            "wrong_rate": sum(r["wrong"] for r in rs) / N,
            "wrong_given_cert": (float(np.mean([r["wrong"] for r in c])) if c else None),
            "delay": (float(np.mean([r["t"] for r in c])) if c else None),
            "labels": float(np.mean([r["labels"] for r in rs])),
            "net_real_mean": float(np.mean([r["net_real"] for r in rs])),
            "net_mean_mean": float(np.mean([r["net_mean"] for r in rs])),
        }
    print(cname, "done", round(time.time() - t0), "s", flush=True)
json.dump(out, open(f"outputs/paper3/payback/{tag}.json", "w"), indent=1)
sha = (
    subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    + "+dirty"
)
rec = {
    "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
    "git_sha": sha,
    "kind": "dev_pilot",
    "config": {
        "tag": tag,
        "N": N,
        "seed_base": DEV_BASE,
        "base": base,
        "v": v,
        "alpha": a,
        "classes": list(CLASSES),
    },
    "seeds": f"SeedSequence([{DEV_BASE}, class_idx, i]) i<{N}",
    "status": "complete",
    "metrics_path": f"outputs/paper3/payback/{tag}.json",
}
open("papers/paper3_cost_aware_adaptation/2026_programme/ledger/payback.jsonl", "a").write(
    json.dumps(rec) + "\n"
)
print("ok")
