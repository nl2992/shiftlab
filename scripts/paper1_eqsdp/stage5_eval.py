"""Stage 5 runner: registry names and dynamic Stage 5 specs on one parity split.

A spec is {name: {"kind": "r1"|"cal"|"r2", ...kwargs}}; plain registry names (s2armr_H*, s2wald_*,
EQSDp_l0.98_g0.3, wald_l0.97_g0.2) are run unchanged. Episode index keeps its place in the seed
derivation (stage2_eval.make_jobs). Output: <out>/records.jsonl, meta.json, progress.txt.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_eval as ev
import stage2_policies as sp2
import stage5_policies as sp5
import trace_run as tr


def job5(args):
    base, specs = args
    for name, spec in specs.items():
        sp2.DYN[name] = sp5.make_factory(spec, name)
    return tr.job(base)


def run_specs(names, specs, split, out: Path, workers=16, budget=200):
    out.mkdir(parents=True, exist_ok=True)
    allnames = [*names, *specs]
    jobs = [(j, specs) for j in ev.make_jobs(split, allnames, budget)]
    (out / "meta.json").write_text(
        json.dumps({"split": split, "budget": budget, "policies": allnames, "specs": specs,
                    "jobs": len(jobs)}, indent=1)
    )  # fmt: skip
    with (
        open(out / "records.jsonl", "w") as f,
        mp.Pool(min(workers, 16), initializer=ev._warm) as pool,
    ):
        for i, rows in enumerate(pool.imap_unordered(job5, jobs, chunksize=2)):
            f.writelines(json.dumps(r) + "\n" for r in rows)
            if i % 50 == 0:
                f.flush()
                (out / "progress.txt").write_text(f"{i + 1}/{len(jobs)}")
    (out / "progress.txt").write_text(f"done {len(jobs)}/{len(jobs)}")
