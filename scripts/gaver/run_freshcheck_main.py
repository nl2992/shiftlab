"""WP3 FreshCheck screening runner (resumable, chunked, parallel).

Studies (all seeds inside the WP3 block 101120000-101159999, one stream seed per (cell, replicate)
shared by every method):
  alt       : persistent/reversal/transient x onset {0.2,0.5} x d {1,10}, 60 seeds, base 101120000
  null500   : boundary-null stream, d {1,10}, 500 seeds, base 101130000
  persist500: persistent cells, onset {0.2,0.5} x d {1,10}, 500 seeds, base 101140000 (false rollback)
  keepnull500: strong-better window then benefit exactly h (in H_keep), d {1,10}, 500 seeds, base 101150000

Usage: python scripts/gaver/run_freshcheck_main.py [--smoke] [--workers N] [--out DIR]
Appends one JSON line per (study, cell, chunk) to <out>/records.jsonl; rerun resumes.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from pathlib import Path

from shiftlab.gaver import freshcheck as fc

CHUNK = 10
METHODS_RUN = fc.METHODS
D_VALUES = (1, 10)


def design(smoke: bool):
    tasks = []
    n_alt = 10 if smoke else 60
    n_big = 20 if smoke else 500
    ci = 0
    for kind in ("persistent", "reversal", "transient"):
        for onset in (fc.EARLY, fc.LATE):
            for d in D_VALUES:
                tasks.append(("alt", fc.Wp3Cell(kind, onset, d), 101120000 + 100 * ci, n_alt))
                ci += 1
    for i, d in enumerate(D_VALUES):
        tasks.append(("null500", fc.Wp3Cell("null", d=d), 101130000 + 1000 * i, n_big))
    ci = 0
    for onset in (fc.EARLY, fc.LATE):
        for d in D_VALUES:
            tasks.append(
                ("persist500", fc.Wp3Cell("persistent", onset, d), 101140000 + 1000 * ci, n_big)
            )
            ci += 1
    for i, d in enumerate(D_VALUES):
        tasks.append(
            ("keepnull500", fc.Wp3Cell("keepnull", fc.EARLY, d), 101150000 + 1000 * i, n_big)
        )
    out = []
    for study, cell, s0, n in tasks:
        assert fc.WP3_SEED_RANGE[0] <= s0 and s0 + n - 1 <= fc.WP3_SEED_RANGE[1]
        for k in range(0, n, CHUNK):
            out.append((study, cell, s0 + k, min(CHUNK, n - k)))
    return out


def work(task):
    study, cell, s0, n = task
    rows = []
    for sd in range(s0, s0 + n):
        rows += fc.run_cell_seed(cell, sd, METHODS_RUN)
    for r in rows:
        r["study"] = study
    return (study, cell.cell_id, s0), rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default="outputs/gaver/wp3")
    ap.add_argument("--methods", default="", help="comma list; default all")
    ap.add_argument("--tag", default="", help="records file suffix (e.g. ext)")
    a = ap.parse_args()
    out = Path(a.out)
    if a.smoke:
        out = out / "smoke"
    out.mkdir(parents=True, exist_ok=True)
    global METHODS_RUN
    if a.methods:
        METHODS_RUN = tuple(a.methods.split(","))
    rec = out / (f"records_{a.tag}.jsonl" if a.tag else "records.jsonl")
    done = set()
    if rec.exists():
        for line in rec.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(tuple(json.loads(line)["key"]))
    todo = [t for t in design(a.smoke) if (t[0], t[1].cell_id, t[2]) not in done]
    print(f"{len(todo)} chunks to run ({len(done)} done)", flush=True)
    t0 = time.time()
    with mp.Pool(a.workers) as pool, rec.open("a", encoding="utf-8") as f:
        for i, (key, rows) in enumerate(pool.imap_unordered(work, todo), 1):
            f.write(json.dumps({"key": list(key), "rows": rows}) + "\n")
            f.flush()
            if i % 10 == 0 or i == len(todo):
                print(f"{i}/{len(todo)} chunks, {time.time() - t0:.0f}s", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
