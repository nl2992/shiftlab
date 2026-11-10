"""J pilot runner (dev seeds). Appends to the dualuse ledger."""

import argparse
import dataclasses
import json
import pathlib
import subprocess
import time

import numpy as np

from shiftlab.paper3.dualuse.jpilot import JCfg, run_j

LEDGER = pathlib.Path("papers/paper3_cost_aware_adaptation/2026_programme/ledger/dualuse.jsonl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--R", type=int, default=4000)
    ap.add_argument("--chunk", type=int, default=1000)
    ap.add_argument("--base", type=int, default=9_150_000)
    ap.add_argument("--cfg", type=json.loads, default={})
    a = ap.parse_args()
    cfg = JCfg(**a.cfg)
    t0 = time.time()
    acc = {}
    for c in range(a.R // a.chunk):
        o = run_j(cfg, a.chunk, np.random.default_rng([a.base, c]))
        for p, v in o.items():
            for k, x in v.items():
                acc.setdefault(p, {}).setdefault(k, []).append(x)
    A = {p: {k: np.concatenate(x) for k, x in v.items()} for p, v in acc.items()}
    n = a.R
    ref = "preq_all"
    res = {"n": n, "policies": {}}
    for p, v in A.items():
        d = v["J"] - A[ref]["J"]
        res["policies"][p] = {
            "J": float(v["J"].mean()),
            "loss": float(v["loss"].mean()),
            "nq": float(v["nq"].mean()),
            "retr": float(v["retr"].mean()),
            "prom_rate": float(v["promoted"].mean()),
            "dJ_vs_preq_mean": float(d.mean()),
            "dJ_vs_preq_ci": [
                float(d.mean() - 1.96 * d.std(ddof=1) / np.sqrt(n)),
                float(d.mean() + 1.96 * d.std(ddof=1) / np.sqrt(n)),
            ],
        }
    try:
        sha = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
            + "+dirty"
        )
    except Exception:  # noqa: BLE001
        sha = "unknown"
    rec = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "git_sha": sha,
        "kind": "dualuse_jpilot",
        "tag": a.tag,
        "config": dataclasses.asdict(cfg),
        "seeds": f"base {a.base}, chunks 0..{a.R // a.chunk - 1}",
        "status": "complete",
        "wall_s": round(time.time() - t0, 1),
        "result": res,
    }
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(a.tag)
    for p, r in res["policies"].items():
        print(
            f"{p:9s} J={r['J']:.2f} loss={r['loss']:.1f} nq={r['nq']:.0f} prom={r['prom_rate']:.3f} dJ_vs_preq={r['dJ_vs_preq_mean']:+.2f} {np.round(r['dJ_vs_preq_ci'], 2)}"
        )


if __name__ == "__main__":
    main()
