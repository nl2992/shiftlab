"""Resumable dev pilot: 32 cells x N seeds x {alt, null twin} x methods. Per-cell checkpoint files.
Usage: run_pilot.py --seeds 30 --seed-base 7300000 --tag dev1 [--methods ...]
"""

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from shiftlab.paper3.atlas import ledger
from shiftlab.paper3.atlas.cells import design
from shiftlab.paper3.atlas.runner import MAIN, REPAIR, run_one

ROOT = Path(__file__).resolve().parents[3]


def job(a):
    cid, seeds, methods, sb, path = a
    cell = design()[cid]
    rows = []
    for s in seeds:
        for null in (False, True):
            rows += run_one(cell, s, methods, null, sb)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text("\n".join(json.dumps(r) for r in rows))
    os.replace(tmp, path)
    return cid, len(rows)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed-base", type=int, default=7300000)
    ap.add_argument("--tag", default="dev1")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--cells", default="all")
    ap.add_argument("--methods", default="")
    a = ap.parse_args()
    methods = a.methods.split(",") if a.methods else MAIN + ["iid_gate"] + REPAIR
    out = ROOT / "outputs/paper3/atlas" / a.tag
    out.mkdir(parents=True, exist_ok=True)
    cells = design()
    ids = range(len(cells)) if a.cells == "all" else [int(x) for x in a.cells.split(",")]
    seeds = list(range(a.seeds))
    todo = [
        (c, seeds, methods, a.seed_base, out / f"cell_{c:02d}.jsonl")
        for c in ids
        if not (out / f"cell_{c:02d}.jsonl").exists()
    ]
    cfg = {
        "tag": a.tag,
        "methods": methods,
        "seed_base": a.seed_base,
        "n_seeds": a.seeds,
        "T": 2000,
    }
    (out / "config.json").write_text(json.dumps(cfg))
    t = time.time()
    print("todo", len(todo), flush=True)
    with ProcessPoolExecutor(a.workers) as ex:
        for cid, n in ex.map(job, todo):
            print("cell", cid, n, round(time.time() - t), flush=True)
    ledger.append(
        "dev_pilot", cfg, f"seed_idx 0..{a.seeds - 1} x base {a.seed_base}", "complete", str(out)
    )
