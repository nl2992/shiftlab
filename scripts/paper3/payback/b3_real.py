"""B3 on c4 streams, even/odd episode split (design 03B3 section 4b/4c).
usage: b3_real.py --split even|odd --certs C0,C1,B2 --v 0.002 --h 100 --out outputs/paper3/payback/b3/X.csv
Certificates: C0..C4 = B3 dev grid; B2 = existing B2 under the same driver (for v != .002 sensitivity)."""

import argparse
import csv
import datetime
import json
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from shiftlab.paper3.payback.certificates import B2Certificate, plan_batch_size
from shiftlab.paper3.payback.envelope import Envelope
from shiftlab.paper3.payback.variance_adaptive import B3Certificate, plan_batch_size_var, run_events

B, K, ALPHA = 150, 3.0, 0.1
GRID = {  # name: (mode, sigma_plan, lam_max)
    "C0": ("batch", 1.0, 0.5),
    "C1": ("batch", 0.1, 0.5),
    "C2": ("batch", 1.0, 0.75),
    "C3": ("single", 1.0, 0.5),
    "C4": ("single", 0.1, 0.75),
}
HDR = ["stream", "episode", "h", "v", "cert", "certified", "t", "labels", "gross", "hold", "delay"]


def make(name, env):
    if name == "B2":
        return B2Certificate(env, ALPHA), plan_batch_size(env, ALPHA / 2, B)
    mode, sp, lm = GRID[name]
    return B3Certificate(env, ALPHA, mode, lm), plan_batch_size_var(env, ALPHA / 2, B, sp)


def job(a):
    path, split, certs, v, h = a
    z = np.load(path, allow_pickle=False)
    l0, l1, d = z["l0"], z["l1"], int(z["delay"])
    env, rows = Envelope(v), []
    par = 0 if split == "even" else 1
    for ep in range(l0.shape[0]):
        if ep % 2 != par:
            continue
        zz = np.concatenate([[0.0], l0[ep].astype(float) - l1[ep].astype(float)])
        for cn in certs:
            cert, n = make(cn, env)
            r = run_events(zz, cert, h=h, d=d, B=B, k=K, n_plan=n, truncate=True)
            rows.append(
                [
                    Path(path).stem,
                    ep,
                    h,
                    v,
                    cn,
                    int(r["certified"]),
                    r["t"],
                    r["labels"],
                    r["gross"],
                    r["hold"],
                    d,
                ]
            )
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=["even", "odd"])
    ap.add_argument("--certs", required=True)
    ap.add_argument("--v", type=float, default=0.002)
    ap.add_argument("--h", type=int, default=100)
    ap.add_argument("--data", default="../shift-research-starter/data/c4_sealed")
    ap.add_argument("--out", required=True)
    ap.add_argument("--kind", default="B3_real_dev")
    a = ap.parse_args()
    certs = a.certs.split(",")
    files = sorted(Path(a.data).glob("*.npz"))
    t0 = time.time()
    with ProcessPoolExecutor(20) as ex:
        res = list(ex.map(job, [(str(f), a.split, certs, a.v, a.h) for f in files]))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        for r in res:
            w.writerows(r)
    sha = subprocess.run(  # noqa: PLW1510
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    rec = {
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "git_sha": sha + "+dirty",
        "kind": a.kind,
        "config": {
            "split": a.split,
            "certs": certs,
            "v": a.v,
            "h": a.h,
            "alpha": ALPHA,
            "B": B,
            "k": K,
            "streams": len(files),
            "protocol": "03B3_VARIANCE_ADAPTIVE_DESIGN",
        },
        "status": "complete",
        "seconds": round(time.time() - t0, 1),
        "metrics_path": a.out,
    }
    with open("papers/paper3_cost_aware_adaptation/2026_programme/ledger/payback.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    print("ok", round(time.time() - t0), "s")
