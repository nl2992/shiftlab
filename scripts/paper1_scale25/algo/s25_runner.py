# ruff: noqa
"""Run named policies / spec files on a development pool (nine | fresh), detached-friendly.

    python s25_runner.py --pool nine --specs specs.json --out DIR [--extra NAME ...] [--split all|even|odd]
                         [--workers 8] [--seeds 10]

Spec files are JSON lists of compositor specs (see eval60). A spec may carry ``"datasets": [..]`` to be
run on those datasets only (per-dataset calibrated controls). Same rng derivation and rows as
eval60 / trace_run (== sota_nine); every record carries the code SHA and pool.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import time
from pathlib import Path

import s25_common as sc
import compositor as comp
import eval60 as e60
import stage2_eval as ev
import trace_run as tr


def _init():
    ev._warm()
    import s25_modules  # noqa: F401  (registers modules in this worker)


def _job(args):
    import s25_modules  # noqa: F401

    return e60._job(args)


def run(
    specs,
    out,
    pool,
    extra=(),
    seeds=sc.SEEDS,
    split="all",
    workers=8,
    episodes=None,
    budget=200,
    log=print,
):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    import s25_modules  # noqa: F401

    sealed = sc.sealed(pool)
    tr.sealed_paths = lambda *a, **k: sealed
    for s in specs:
        comp.validate_spec(s)
    reg = {comp.config_id(s): s for s in specs}
    key = hashlib.sha256(json.dumps(reg, sort_keys=True, default=str).encode()).hexdigest()
    eps = e60.select_episodes(split, episodes, None, sealed)
    jobs = []
    for ds, (p, delay, sb) in sealed.items():
        names = [n for n, s in reg.items() if ds in s.get("datasets", [ds])] + list(extra)
        jobs += [((ds, p, delay, e, sd, sb, names, budget, ()), reg, key)
                 for e in eps.get(ds, []) for sd in seeds]  # fmt: skip
    sha = e60.code_sha()
    (out / "meta.json").write_text(
        json.dumps(
            {
                "sha": sha,
                "pool": pool,
                "split": split,
                "seeds": list(seeds),
                "budget": budget,
                "policies": list(reg) + list(extra),
                "specs": reg,
                "jobs": len(jobs),
            },
            indent=1,
            default=str,
        )
    )
    t0 = time.perf_counter()
    mpool = mp.Pool(min(workers, 16), initializer=_init)
    try:
        with open(out / "records.jsonl", "w") as f:
            for i, rs in enumerate(mpool.imap_unordered(_job, jobs, chunksize=4)):
                for r in rs:
                    rec = {k: r[k] for k in e60.KEEP if k in r} | {
                        "config_id": r["policy"],
                        "sha": sha,
                        "pool": pool,
                    }
                    f.write(json.dumps(rec) + "\n")
                if i % 100 == 0:
                    f.flush()
                    (out / "progress.txt").write_text(f"{i + 1}/{len(jobs)}")
    finally:
        mpool.terminate()
    (out / "progress.txt").write_text(
        f"done {len(jobs)}/{len(jobs)} in {time.perf_counter() - t0:.0f}s"
    )
    (out / "DONE").write_text("ok")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True, choices=["nine", "fresh"])
    ap.add_argument("--specs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--split", default="all", choices=["all", "even", "odd"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=10)
    a = ap.parse_args()
    specs = json.loads(Path(a.specs).read_text(encoding="utf-8")) if a.specs else []
    run(specs, a.out, a.pool, a.extra, tuple(range(a.seeds)), a.split, a.workers)


if __name__ == "__main__":
    main()
