"""R1: payback certificates on real c4 paired-loss episodes (protocol 04_EXPERIMENT_PROTOCOL_R1.md).

usage: run_real.py --data DIR --h 100 --alpha 0.1 --cq 0 --out outputs/paper3/payback/real_r1
Writes <out>/ep_h{h}.csv (one row per stream x episode x certificate); analysis: analyze_real.py.
"""

import argparse
import csv
import datetime
import json
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from shiftlab.paper3.payback.real import CERTS, net, run_all

MIN_EP = 6
HDR = [
    "stream",
    "episode",
    "h",
    "cert",
    "certified",
    "t",
    "labels",
    "gross",
    "hold",
    "net",
    "delay",
]


def job(args):
    path, h, alpha, cq = args
    z = np.load(path, allow_pickle=False)
    l0, l1, d = z["l0"], z["l1"], int(z["delay"])
    rows = []
    for ep in range(l0.shape[0]):
        for name, r in run_all(l0[ep], l1[ep], h=h, d=d, alpha=alpha).items():
            rows.append(
                [
                    Path(path).stem,
                    ep,
                    h,
                    name,
                    int(r["certified"]),
                    r["t"],
                    r["labels"],
                    r["gross"],
                    r["hold"],
                    net(r, cq),
                    d,
                ]
            )
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--h", type=int, required=True)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--cq", type=float, default=0.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    use, excl = [], []
    for f in sorted(Path(a.data).glob("*.npz")):
        n = np.load(f, allow_pickle=False)["l0"].shape[0]
        (use if n >= MIN_EP else excl).append((f, n))
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        res = list(ex.map(job, [(str(f), a.h, a.alpha, a.cq) for f, _ in use]))
    with open(out / f"ep_h{a.h}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        for rows in res:
            w.writerows(rows)
    el = time.time() - t0
    (out / f"meta_h{a.h}.json").write_text(
        json.dumps(
            {
                "h": a.h,
                "alpha": a.alpha,
                "cq": a.cq,
                "seconds": el,
                "excluded": [(f.stem, n) for f, n in excl],
                "n_streams": len(use),
                "certs": CERTS,
            }
        )
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    rec = {
        "timestamp": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "git_sha": sha + "+dirty",
        "kind": "R1_real_run",
        "config": {
            "registration": "04_EXPERIMENT_PROTOCOL_R1 @0e41146c",
            "h": a.h,
            "alpha": a.alpha,
            "cq": a.cq,
            "v": 0.002,
            "B": 150,
            "k": 3.0,
            "streams": len(use),
            "excluded": [f.stem for f, _ in excl],
        },
        "status": "complete",
        "seconds": round(el, 1),
        "metrics_path": f"{a.out}/ep_h{a.h}.csv",
    }
    with open("papers/paper3_cost_aware_adaptation/2026_programme/ledger/payback.jsonl", "a") as f:
        f.write(json.dumps(rec) + "\n")
    print("ok", round(el), "s")
