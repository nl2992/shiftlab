"""B3 synthetic validity / power (design 03B3 section 4a).  usage: b3_synth.py [N] [out_json]"""

import datetime
import json
import math
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from shiftlab.paper3.payback.certificates import B2Certificate, plan_batch_size
from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.sim import Spec, make_stream
from shiftlab.paper3.payback.variance_adaptive import (
    B3Certificate,
    B3GatedCertificate,
    make_sparse_stream,
    plan_batch_size_var,
    run_events,
)

BASE = 5301600000
ENV = Envelope(0.002)
SPEC = Spec(T=400, B=150, d=5, h=30, k=3.0, alpha=0.1, env=ENV)
# (name, kind, p, role)
CLASSES = [
    ("null_flat", "null_flat", None, "null"),
    ("null_decline60", "null_decline:60", None, "null"),
    ("sparse_null_flat_p.15", "sparse_null_flat", 0.15, "null"),
    ("sparse_null_flat_p.30", "sparse_null_flat", 0.30, "null"),
    ("sparse_null_decline60_p.15", "sparse_null_decline:60", 0.15, "null"),
    ("sparse_null_decline60_p.30", "sparse_null_decline:60", 0.30, "null"),
    ("drift", "drift", None, "power"),
    ("boundary", "boundary", None, "power"),
    ("sparse_in_p.30", "sparse_in", 0.30, "power"),
    ("sparse_in_p.45", "sparse_in", 0.45, "power"),
]
CERTS = ["B2", "B3_batch_s1", "B3_batch_s.25", "B3_single_s.25", "B3_gated"]


def wilson(x, n, z=1.96):
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - hw), min(1.0, c + hw)


def make_cert(name):
    a = SPEC.alpha
    if name == "B2":
        return B2Certificate(ENV, a), plan_batch_size(ENV, a / 2, SPEC.B)
    if name == "B3_batch_s1":
        return B3Certificate(ENV, a, "batch"), plan_batch_size_var(ENV, a / 2, SPEC.B, 1.0)
    if name == "B3_batch_s.25":
        return B3Certificate(ENV, a, "batch"), plan_batch_size_var(ENV, a / 2, SPEC.B, 0.25)
    if name == "B3_single_s.25":
        return B3Certificate(ENV, a, "single"), plan_batch_size_var(ENV, a / 2, SPEC.B, 0.25)
    if name == "B3_gated":
        return B3GatedCertificate(ENV, a), plan_batch_size_var(ENV, a, SPEC.T, 0.25)
    raise ValueError(name)


def job(args):
    ci, i = args
    _name, kind, p, _ = CLASSES[ci]
    seed = (BASE, ci, i)
    if p is None:
        mu, z = make_stream(kind, SPEC, seed)
        dis = None
    else:
        mu, z, dis = make_sparse_stream(kind, SPEC, seed, p)
    out = {}
    for cn in CERTS:
        if cn == "B3_gated" and dis is None:
            continue
        cert, n = make_cert(cn)
        r = run_events(
            z,
            cert,
            h=SPEC.h,
            d=SPEC.d,
            B=SPEC.B,
            k=SPEC.k,
            n_plan=n,
            dis=dis if cn == "B3_gated" else None,
            truncate=False,
        )
        if r["certified"]:
            t = r["t"]
            nm = float(mu[t : t + SPEC.h].sum() - SPEC.k)
            out[cn] = (1, r["t"], r["labels"], r["gross"], int(nm <= 1e-9))
        else:
            out[cn] = (0, 0, r["labels"], 0.0, 0)
    return ci, out


def main(N, outp):
    t0 = time.time()
    agg = {c[0]: {cn: [] for cn in CERTS} for c in CLASSES}
    with ProcessPoolExecutor(20) as ex:
        for ci, out in ex.map(
            job, [(c, i) for c in range(len(CLASSES)) for i in range(N)], chunksize=20
        ):
            for cn, v in out.items():
                agg[CLASSES[ci][0]][cn].append(v)
    res = {}
    for cname, d in agg.items():
        res[cname] = {}
        for cn, rows in d.items():
            if not rows:
                continue
            a = np.array(rows, float)
            n, nc, nw = len(a), int(a[:, 0].sum()), int(a[:, 4].sum())
            lo, hi = wilson(nw, n)
            c = a[:, 0] == 1
            res[cname][cn] = {
                "N": n,
                "cert_rate": nc / n,
                "wrong": nw,
                "P_wrong": nw / n,
                "wilson": [lo, hi],
                "P_wrong_given_cert": (nw / nc) if nc else None,
                "delay": float(a[c, 1].mean()) if nc else None,
                "labels": float(a[:, 2].mean()),
                "net_real_mean": float(a[:, 3].mean()),
            }
    json.dump(res, open(outp, "w"), indent=1)  # noqa: SIM115
    sha = subprocess.run(  # noqa: PLW1510
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    rec = {
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "git_sha": sha + "+dirty",
        "kind": "B3_synth_validity",
        "config": {
            "N": N,
            "base_seed": BASE,
            "T": 400,
            "B": 150,
            "d": 5,
            "h": 30,
            "k": 3,
            "alpha": 0.1,
            "v": 0.002,
        },
        "status": "complete",
        "seconds": round(time.time() - t0, 1),
        "metrics_path": outp,
    }
    with open("papers/paper3_cost_aware_adaptation/2026_programme/ledger/payback.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    for cname, d in res.items():
        print(cname)
        for cn, v in d.items():
            print(
                f"  {cn:16s} cert {v['cert_rate']:.3f} Pwrong {v['P_wrong']:.4f} W[{v['wilson'][0]:.3f},{v['wilson'][1]:.3f}]"
                f" delay {v['delay']} labels {v['labels']:.0f} net {v['net_real_mean']:.2f}"
            )


if __name__ == "__main__":
    main(
        int(sys.argv[1]) if len(sys.argv) > 1 else 1000,
        sys.argv[2] if len(sys.argv) > 2 else "outputs/paper3/payback/b3/synth.json",
    )
