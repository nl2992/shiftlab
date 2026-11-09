"""Stage 0 headroom diagnostic (docs/paper1_eqsdp/10_JOINTBAYES_PLAN.md, Stage 0).

Subcommands (all on the nine datasets, even episodes only, 10 policy seeds):
  run      run named policies at a given budget with the traced runner -> records.jsonl
  analyze  reproduction check, reference baseline, decomposition, free-label ceiling, stop rule

Usage:
  python stage0_headroom.py run --out DIR --budget 200 [--policies P1 P2 ...] [--workers 16]
  python stage0_headroom.py analyze --p1 DIR --ceiling DIR
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trace_run as tr

ROOT = tr.ROOT
OUT = ROOT / "outputs/paper1_eqsdp/stage0"
TABLES = ROOT / "docs/paper1_eqsdp/tables"
SEEDS = 10
NBOOT = 2000


def cmd_run(a):
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    names = a.policies or [tr.ARM_R, *tr.WALD_GRID]
    check = (tr.ARM_R,) if a.check_orig else ()
    sp = tr.sealed_paths()
    jobs = []
    for ds, (p, delay, sb) in sp.items():
        n_ep = np.load(p)["l0"].shape[0]
        jobs += [
            (ds, p, delay, e, s, sb, names, a.budget, check)
            for e in range(0, n_ep, 2)
            for s in range(SEEDS)
        ]
    (out / "meta.json").write_text(
        json.dumps({"budget": a.budget, "policies": names, "jobs": len(jobs)})
    )
    with open(out / "records.jsonl", "w") as f, mp.Pool(min(a.workers, 16)) as pool:
        for i, rows in enumerate(pool.imap_unordered(tr.job, jobs, chunksize=2)):
            f.writelines(json.dumps(r) + "\n" for r in rows)
            if i % 50 == 0:
                f.flush()
                (out / "progress.txt").write_text(f"{i + 1}/{len(jobs)}")
    (out / "progress.txt").write_text(f"done {len(jobs)}/{len(jobs)}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--budget", type=int, default=200)
    r.add_argument("--policies", nargs="*")
    r.add_argument("--workers", type=int, default=16)
    r.add_argument("--check-orig", action="store_true")
    r.set_defaults(f=cmd_run)
    an = sub.add_parser("analyze")
    an.add_argument("--p1", default=str(OUT / "p1"))
    an.add_argument("--ceiling", default=str(OUT / "b400"))
    an.set_defaults(f=lambda a: __import__("stage0_analysis").analyze(a))
    a = ap.parse_args()
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    a.f(a)


if __name__ == "__main__":
    main()
