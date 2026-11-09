"""Shared evaluation machinery for Stage 2 / Stage 3.

* ``run_named``: run registry-named policies on one parity split (even = tuning, odd = selection
  check) with the Stage 0 traced job runner; episode ``ep`` keeps its index in the seed derivation,
  so an episode has the same seeds whichever split it is run in.
* ``Evaluator``: a persistent worker pool that evaluates Stage 2 configurations (dicts) on the
  even split and returns per-episode seed-means.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_policies as sp2
import trace_run as tr

SEEDS = 10
PARITY = {"even": 0, "odd": 1}
PER_EP_COLS = ["net", "loss", "labels", "switches"]


def make_jobs(split: str, names, budget=200):
    start = PARITY[split]
    jobs = []
    for ds, (p, delay, sb) in tr.sealed_paths().items():
        n_ep = np.load(p)["l0"].shape[0]
        jobs += [
            (ds, p, delay, e, s, sb, list(names), budget, ())
            for e in range(start, n_ep, 2)
            for s in range(SEEDS)
        ]
    return jobs


def job_dyn(args):
    """args = (base_job_args, {name: cfg}); registers the dynamic policies in this worker."""
    base, dyn = args
    for name, cfg in dyn.items():
        sp2.DYN[name] = sp2.stage2_factory(cfg, name)
    return tr.job(base)


def run_named(names, split, out: Path, workers=16, budget=200, dyn=None):
    out.mkdir(parents=True, exist_ok=True)
    jobs = make_jobs(split, names, budget)
    fn = tr.job
    if dyn:
        jobs, fn = [(j, dyn) for j in jobs], job_dyn
    (out / "meta.json").write_text(
        json.dumps({"split": split, "budget": budget, "policies": list(names), "jobs": len(jobs)})
    )
    with open(out / "records.jsonl", "w") as f, mp.Pool(min(workers, 16)) as pool:
        for i, rows in enumerate(pool.imap_unordered(fn, jobs, chunksize=2)):
            f.writelines(json.dumps(r) + "\n" for r in rows)
            if i % 50 == 0:
                f.flush()
                (out / "progress.txt").write_text(f"{i + 1}/{len(jobs)}")
    (out / "progress.txt").write_text(f"done {len(jobs)}/{len(jobs)}")


def episode_means(rows: list[dict]) -> pd.DataFrame:
    d = pd.DataFrame(rows)
    return d.groupby(["stream", "ep", "policy"])[PER_EP_COLS].mean().reset_index()


def pooled(e: pd.DataFrame, col: str) -> float:
    """Equal-dataset mean of the per-dataset episode means."""
    return float(e.groupby("stream")[col].mean().mean())


class Evaluator:
    def __init__(self, workers=16, split="even", budget=200):
        self.split, self.budget = split, budget
        self.pool = mp.Pool(min(workers, 16))

    def evaluate(self, cfgs: dict[str, dict], named=()) -> tuple[pd.DataFrame, pd.DataFrame, float]:
        """cfgs: name -> Stage2Policy kwargs; named: registry policy names run in the same jobs.
        Returns (full rows, per-episode seed means, seconds)."""
        t0 = time.perf_counter()
        names = [*cfgs, *named]
        args = [(j, cfgs) for j in make_jobs(self.split, names, self.budget)]
        rows = []
        for r in self.pool.imap_unordered(job_dyn, args, chunksize=4):
            rows.extend(r)
        d = pd.DataFrame(rows)
        e = d.groupby(["stream", "ep", "policy"])[PER_EP_COLS].mean().reset_index()
        return d, e, time.perf_counter() - t0

    def close(self):
        self.pool.close()
        self.pool.join()


os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
