"""GAVE-R WP5 runner: evidence x acquisition factorial, plus PAVE null completion (step 0).

Stages (each resumable; rows appended to ``<out>/rows.csv``):
  pavenull  step 0: raw (ungated) PAVE, reserve off, kappa=.1 q=.03, 500 fresh streams on the 16
            Atlas dependence-null cells with B/T<=0.1, d in {1,10}; DSS alongside.
  alt       2x2(+envelope) on the WP2 31-cell alternative set, 60 paired seeds.
  null      factorial on 29 null cells, 500 streams.

Seeds (WP5 block 101160000-101199999 only): pavenull 101160000+500*i, null 101170000+500*i,
alt 101190000+100*i (i = cell index in the order below).

Usage (repo root):  python scripts/gaver/run_gaver_factorial.py --stage alt --workers 8
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from multiprocessing import Pool
from pathlib import Path

for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts"), str(ROOT / "scripts" / "gaver")]

import numpy as np
import run_pave_eval as rpe
from run_atlas_cycle6_validity_v1 import build_null_cell
from run_atlas_cycle7_validation_v1 import make_method
from run_atlas_dss_tuning_v1 import build_cell

from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver.integrated import ACQS, EVIDENCES, PAVE_TUNED, GaverMethod, pave_active
from shiftlab.gaver.pave import PaveMethod

WP5_LO, WP5_HI = 101160000, 101199999
BASES = {"pavenull": (101160000, 500), "null": (101170000, 500), "alt": (101190000, 100)}
N_DEFAULT = {"pavenull": 500, "null": 500, "alt": 60}
FIELDS = [
    "stage", "cell", "seed", "arm", "cost", "loss", "query_cost", "switch_cost", "queries",
    "switches", "fp", "promoted", "detect", "delay",
]  # fmt: skip
FACTORIAL = [f"gaver:{e}:{a}" for e in EVIDENCES for a in ACQS]
RHOS = (0.0, 0.5, 0.8, 0.95)


def null_cells() -> list[tuple[str, object]]:
    """29 null cells: dep d in {1,10} x bt<=.1 (PAVE inactive), d=50 x bt<=.1, d=10 x bt=.25, F1 d50."""
    out = []
    for d in (1, 10):
        for bt in (0.05, 0.1):
            for r in RHOS:
                p = {"rho": r, "bt": bt, "d": d}
                out.append((f"dep_rho{r:g}_bt{bt:g}_d{d}", build_null_cell("dep", p, 1000)))
    for bt in (0.05, 0.1):
        for r in RHOS:
            p = {"rho": r, "bt": bt, "d": 50}
            out.append((f"dep_rho{r:g}_bt{bt:g}_d50", build_null_cell("dep", p, 1000)))
    for r in RHOS:
        p = {"rho": r, "bt": 0.25, "d": 10}
        out.append((f"dep_rho{r:g}_bt0.25_d10", build_null_cell("dep", p, 1000)))
    out.append(
        ("f1null_d50_b0.05", build_cell("on0.6_L1_strong_harmful_d50_b0.05_s0.1").null_twin())
    )
    return out


def pavenull_cells() -> list[tuple[str, object]]:
    return [x for x in null_cells()[:16]]


def alt_cells() -> list[tuple[str, object]]:
    return [(c.cell_id, c) for c in rpe.cells_for("eval")]


def arms_for(stage: str, cell) -> list[str]:
    if stage == "pavenull":
        return ["dss", "pave_raw"]
    ref = ["uniform", "episode_front"] if stage == "alt" else []
    gated_on = pave_active(cell.config(0))
    arms = FACTORIAL if gated_on or stage == "alt" else [f"gaver:{e}:dss" for e in EVIDENCES]
    if stage == "null":  # compute: mlr:pave dropped from null (7 s/stream); see results doc
        arms = [a for a in arms if a != "gaver:mlr:pave"]
    return ref + arms


def make(arm: str, cfg, sp):
    if arm.startswith("gaver:"):
        _, e, a = arm.split(":")
        return GaverMethod(e, a)
    if arm == "pave_raw":
        return PaveMethod(PAVE_TUNED)
    return make_method(arm, cfg, sp)


def task(job):
    stage, cid, cell, seeds, arms = job
    sp = rpe.all_specs()
    rows = []
    for sd in seeds:
        cfg, stream = cell.config(sd), fa.make_stream(cell, sd)
        reg = stream.truth.regime
        onset = int(np.argmax(reg)) + 1 if reg.any() else None
        for arm in arms:
            r = fa.run_for(cell, stream, make(arm, cfg, sp), cfg)
            assert r.queries <= cfg.B, "hard budget violated"
            hit = np.nonzero((r.actions == 1) & (reg == 1))[0]
            rows.append(
                {
                    "stage": stage, "cell": cid, "seed": sd, "arm": arm,
                    "cost": r.cost / cell.T, "loss": r.decision_loss / cell.T,
                    "query_cost": r.query_cost / cell.T, "switch_cost": r.switch_cost / cell.T,
                    "queries": r.queries, "switches": r.switches,
                    "fp": int((r.fp_regime or 0) > 0), "promoted": int(r.promotions > 0),
                    "detect": int(len(hit) > 0),
                    "delay": (int(hit[0]) + 1 - onset) if len(hit) and onset else "",
                }
            )  # fmt: skip
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(BASES))
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--chunk", type=int, default=10)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    a.workers = min(a.workers, 8)
    cells = {"pavenull": pavenull_cells, "null": null_cells, "alt": alt_cells}[a.stage]()
    n = a.n or N_DEFAULT[a.stage]
    base, stride = BASES[a.stage]
    out = Path(a.out or ROOT / "outputs/gaver/wp5" / a.stage)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "rows.csv"
    done = set()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            done = {(r["cell"], int(r["seed"]), r["arm"]) for r in csv.DictReader(f)}
    jobs = []
    for i, (cid, cell) in enumerate(cells):
        assert n <= stride
        s0 = base + i * stride
        assert WP5_LO <= s0 and s0 + n - 1 <= WP5_HI, "seed block overflow"
        arms = arms_for(a.stage, cell)
        for k in range(0, n, a.chunk):
            seeds = list(range(s0 + k, s0 + min(n, k + a.chunk)))
            todo = [m for m in arms if any((cid, sd, m) not in done for sd in seeds)]
            if todo:
                jobs.append((a.stage, cid, cell, seeds, todo))
    jobs.sort(key=lambda j: j[3][0] % stride)  # seed-chunk major: partial runs have equal n
    print(f"{a.stage}: {len(cells)} cells, {len(jobs)} jobs", flush=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f, Pool(a.workers) as pool:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for k, rows in enumerate(pool.imap_unordered(task, jobs), 1):
            w.writerows(rows)
            f.flush()
            if k % 20 == 0:
                print(f"{k}/{len(jobs)}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
