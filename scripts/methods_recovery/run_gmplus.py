"""Gap-Mix+ runner (methods-recovery C3): tuning, target/neighbour evaluation, null grid.

Reuses the GAVE-R harness (failure_atlas cells, ``run_for``, GaverMethod shell) and the row schema of
``scripts/gaver/run_gaver_factorial.py``.  Resumable: rows are appended to ``<out>/rows.csv``.

  python scripts/methods_recovery/run_gmplus.py --stage tune|alt|null --workers 10 [--out DIR]

Seeds come from the blocks registered in configs/seed_registry.yaml (gapmix_plus_tuning / _eval).
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

import numpy as np
from run_atlas_cycle6_validity_v1 import build_null_cell
from run_atlas_cycle7_validation_v1 import make_method

from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver.gapmix_plus import GapMixPlusMethod, GMParams, QSGMethod
from shiftlab.gaver.integrated import GaverMethod, pave_active

FROZEN = ROOT / "configs/methods_recovery/gapmix_plus_frozen.json"
# Amendment A1: Arm-5 pacing for neighbour families (d=50, B/T=.5), tuned on tuning seeds only
FROZEN_NB = ROOT / "configs/methods_recovery/gapmix_plus_frozen_nb.json"
TUNE_NB_BASE = (
    101306000  # inside the registered tuning block 101300000-101309999, unused by stage tune
)
TUNE_BASE, EVAL_BASE = 101300000, 101400000  # registry: gapmix_plus_tuning / gapmix_plus_eval
NULL_OFF = 20000  # eval null streams start at EVAL_BASE + NULL_OFF
FIELDS = [
    "stage", "cell", "seed", "arm", "cost", "loss", "query_cost", "switch_cost", "queries",
    "switches", "fp", "promoted", "detect", "delay",
]  # fmt: skip

RHOS, BS, DS = (0.5, 0.8), (0.05, 0.1, 0.25), (1, 10)
ONSETS, EFFECTS = (0.3, 0.6), ("strong", "medium")


def f3(rho, onset, effect, d, b):
    return fa.Family3CellSpec(
        rho=rho, onset=onset, duration=1.0, effect=effect, off_type="harmful", d=d, budget_frac=b
    )


def target_cells():
    return [f3(r, o, e, d, b) for r, o, e, d, b in itertools.product(RHOS, ONSETS, EFFECTS, DS, BS)]


def neighbour_cells():
    out = {"rho0": [], "d50": [], "b0.5": []}
    for o, e, d, b in itertools.product(ONSETS, EFFECTS, DS, BS):
        out["rho0"].append(f3(0.0, o, e, d, b))
    for r, o, e, b in itertools.product(RHOS, ONSETS, EFFECTS, BS):
        out["d50"].append(f3(r, o, e, 50, b))
    for r, o, e, d in itertools.product(RHOS, ONSETS, EFFECTS, DS):
        out["b0.5"].append(f3(r, o, e, d, 0.5))
    return out


def null_cells():
    return [
        (
            f"dep_rho{r:g}_bt{b:g}_d{d}",
            build_null_cell("dep", {"rho": r, "bt": b, "d": d}, 1000),
        )
        for r, b, d in itertools.product((0.0, 0.5, 0.8), BS, DS)
    ]


def fam_key(cell) -> str:
    return f"b{cell.budget_frac:g}_d{cell.d}"


def parse_key(key: str) -> GMParams:
    if key.startswith("G"):
        return GMParams(gap=int(key[1:]))
    if key.startswith("f"):
        return GMParams(frac=float(key[1:]))
    k, p, w = key.split("_")
    return GMParams(kappa=float(k[1:]), phi=float(p[1:]), omega=float(w[1:]))


ARM4_GRID = [
    f"k{k:g}_p{p:g}_w{w:g}" for k, p, w in itertools.product((1, 2, 4), (1, 1.5, 2.5), (0, 0.5, 1))
]  # 27 configs
ARM5_GRID = [f"G{g}" for g in (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 70)] + [
    f"f{f:g}" for f in (0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.2, 1.5, 2, 3)
]  # 32 configs


def make(arm: str, cfg, cell_fam: str):
    if arm.startswith("gmp:"):
        parts = arm.split(":")
        _, ev, mode = parts[:3]
        if ev == "qsg":
            return QSGMethod()
        if len(parts) == 4:  # explicit key (tuning)
            return GapMixPlusMethod(ev, mode, parse_key(parts[3]))
        fz = json.loads(FROZEN.read_text("utf-8"))
        if mode == "pace" and cell_fam not in fz["arm5"]:
            fz["arm5"].update(json.loads(FROZEN_NB.read_text("utf-8"))["arm5"])
        key = fz["arm5"][cell_fam] if mode == "pace" else fz["arm4"]
        return GapMixPlusMethod(ev, mode, parse_key(key))
    if arm.startswith("gaver:"):
        _, e, a = arm.split(":")
        return GaverMethod(e, a)
    return make_method(arm, cfg, None)


MAIN_ARMS = [
    "gaver:mlr:dss", "gaver:gapmix:dss", "gaver:gapmix:pave", "gmp:gapmix:plus",
    "gmp:gapmix:pace", "gmp:gapmix:frozen", "gmp:mlr:plus", "gmp:qsg:dss",
    "thinned_hedged_gate", "episode_front", "uniform",
]  # fmt: skip


def arms_for(stage: str, cell) -> list[str]:
    if stage == "tune_nb":
        return [f"gmp:gapmix:pace:{k}" for k in ARM5_GRID]
    if stage == "tune":
        return (
            [f"gmp:gapmix:plus:{k}" for k in ARM4_GRID]
            + [f"gmp:gapmix:pace:{k}" for k in ARM5_GRID]
            + ["gaver:gapmix:dss"]
        )
    arms = list(MAIN_ARMS)
    if not pave_active(cell.config(0)):
        arms.remove("gaver:gapmix:pave")  # identical to gaver:gapmix:dss by construction
    if stage == "null":
        arms.remove("gmp:mlr:plus")
    return arms


def task(job):
    stage, cid, cell, seeds, arms = job
    rows = []
    fam = fam_key(cell) if hasattr(cell, "budget_frac") else f"b{cell.B / cell.T:g}_d{cell.d}"
    for sd in seeds:
        cfg, stream = cell.config(sd), fa.make_stream(cell, sd)
        reg = stream.truth.regime
        onset = int(np.argmax(reg)) + 1 if reg.any() else None
        for arm in arms:
            r = fa.run_for(cell, stream, make(arm, cfg, fam), cfg)
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


def build_cells(stage):
    if stage == "tune":
        return [(c.cell_id, c) for c in target_cells()], TUNE_BASE, 100, 8
    if stage == "tune_nb":
        nb = neighbour_cells()
        return [(c.cell_id, c) for c in nb["d50"] + nb["b0.5"]], TUNE_NB_BASE, 100, 8
    if stage == "alt":
        cs = list(target_cells())
        for v in neighbour_cells().values():
            cs += v
        return [(c.cell_id, c) for c in cs], EVAL_BASE, 100, 60
    return null_cells(), EVAL_BASE + NULL_OFF, 500, 500


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=["tune", "tune_nb", "alt", "null"])
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--chunk", type=int, default=4)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    a.workers = min(a.workers, 10)
    if a.stage not in ("tune", "tune_nb") and not FROZEN.exists():
        sys.exit("frozen config missing: tune first")
    cells, base, stride, n = build_cells(a.stage)
    n = a.n or n
    out = Path(a.out or ROOT / "outputs/methods_recovery" / a.stage)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "rows.csv"
    done = set()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            done = {(r["cell"], int(r["seed"]), r["arm"]) for r in csv.DictReader(f)}
    jobs = []
    for i, (cid, cell) in enumerate(cells):
        s0 = base + i * stride
        arms = arms_for(a.stage, cell)
        for k in range(0, n, a.chunk):
            seeds = list(range(s0 + k, s0 + min(n, k + a.chunk)))
            todo = [m for m in arms if any((cid, sd, m) not in done for sd in seeds)]
            if todo:
                jobs.append((a.stage, cid, cell, seeds, todo))
    jobs.sort(key=lambda j: j[3][0] % stride)
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
