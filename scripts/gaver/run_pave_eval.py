"""GAVE-R WP2 runner: PAVE vs frozen DSS / uniform / undecided-only on Atlas cells.

Stages (each resumable; rows are appended to ``<out>/rows.csv`` as jobs finish):
  tune    dev tuning grid on a few cells (seeds 101080010..)
  eval    regression + neighbours + primary cells, 60 paired seeds (101090000..)
  ablate  2x2x2 factorial on regression + a few primary cells (same eval seeds)
  null    Atlas dependence-null cells, 500 streams each (101100000..)

Usage (repo root, PYTHONPATH=src):  python scripts/gaver/run_pave_eval.py --stage eval --workers 8
"""

from __future__ import annotations

import argparse
import csv
import itertools
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from run_atlas_cycle6_validity_v1 import build_null_cell, config_list
from run_atlas_cycle7_validation_v1 import F1_CELLS, f3_failure_ids, make_method, specs
from run_atlas_dss_tuning_v1 import build_cell

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver.pave import PaveMethod, PaveParams

REGRESSION = (
    "on0.6_L1_strong_harmful_d50_b0.05_s0.1",
    "f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1",
)
SEEDS = {
    "tune": 101080010,
    "eval": 101090000,
    "ablate": 101090000,
    "null": 101100000,
    "eval2": 101110000,  # fresh seeds for the post-hoc no-reserve variant
    "null2": 101100000,
}
FIELDS = [
    "stage",
    "cell",
    "seed",
    "method",
    "cost",
    "loss",
    "query_cost",
    "switch_cost",
    "queries",
    "switches",
    "fp",
    "promoted",
    "correct",
]
CHUNK = 10


def pave_name(p: PaveParams) -> str:
    return f"pave:p{int(p.pending)}d{int(p.deadline)}r{int(p.reserve)}:k{p.kappa:g}:q{p.q:g}"


def parse_pave(name: str) -> PaveParams:
    _, flags, k, q = name.split(":")
    return PaveParams(
        pending=flags[1] == "1",
        deadline=flags[3] == "1",
        reserve=flags[5] == "1",
        kappa=float(k[1:]),
        q=float(q[1:]),
    )


def make(name, cfg, sp):
    if name.startswith("pave:"):
        return PaveMethod(parse_pave(name))
    if name == "undecided_only":
        return comp.build_candidate(sp["undecided_only"])
    return make_method(name, cfg, sp)


def all_specs():
    sp = specs()
    base = next(
        s
        for ax in ("onset", "duration", "s", "d", "budget_frac", "effect", "rate", "unknown")
        for s in comp.propose_candidates(ax, max_n=60)
        if s.spec_id == comp.DSS_SOURCE_ID
    )
    sp["undecided_only"] = base
    return sp


def cells_for(stage: str):
    f1, f3 = list(F1_CELLS), f3_failure_ids()
    primary = [build_cell(i) for i in (*f1, *f3)]
    if stage == "tune":
        ids = [*REGRESSION, f1[0], f1[1], f3[0], f3[3], f3[5]]
        return [build_cell(i) for i in ids]
    if stage in ("eval", "eval2"):
        out = {c.cell_id: c for c in primary}
        for r in REGRESSION:
            for n in fa.neighbours(build_cell(r)):
                out.setdefault(n.cell_id, n)
        return list(out.values())
    if stage == "ablate":
        ids = [*REGRESSION, f1[0], f1[1], f3[0], f3[3], f3[5], f3[9]]
        return [build_cell(i) for i in ids]
    if stage in ("null", "null2"):
        # compute-limited subset of the 32 Atlas dependence-null configs: B/T <= 0.1 (the cells the
        # cycle-7 acceptance criterion A3 binds on); B/T in {.25,.5} are not run here.
        return [
            build_null_cell("dep", p, 1000)
            for p in config_list(1000)
            if p["kind"] == "dep" and p["bt"] <= 0.1
        ]
    raise ValueError(stage)


def methods_for(stage: str, a):
    ref = ["dss", "uniform", "undecided_only"]
    full = PaveParams(kappa=a.kappa, q=a.q)
    if stage == "tune":
        grid = [PaveParams(kappa=k, q=q) for k in (0.02, 0.1, 0.3) for q in (0.01, 0.03)]
        return ref + [pave_name(p) for p in grid]
    if stage == "eval2":
        nr = PaveParams(reserve=False, kappa=a.kappa, q=a.q)
        return [*ref, "episode_front", pave_name(nr)]
    if stage == "null2":
        return [pave_name(PaveParams(reserve=False, kappa=a.kappa, q=a.q))]
    if stage == "eval":
        return [*ref, "episode_front", "markov_lr_gate", pave_name(full)]
    if stage == "ablate":
        fl = itertools.product((True, False), repeat=3)
        return ["dss", "uniform"] + [
            pave_name(PaveParams(pending=p, deadline=d, reserve=r, kappa=a.kappa, q=a.q))
            for p, d, r in fl
        ]
    if stage == "null":
        return ["dss", "uniform", pave_name(full)]


def task(args):
    stage, cell_id, cell_json, seeds, methods = args
    cell = build_cell(cell_id) if cell_json is None else cell_json
    sp = all_specs()
    rows = []
    for sd in seeds:
        cfg, stream = cell.config(sd), fa.make_stream(cell, sd)
        for m in methods:
            r = fa.run_for(cell, stream, make(m, cfg, sp), cfg)
            assert r.queries <= cfg.B, "hard budget violated"
            rows.append(
                {
                    "stage": stage,
                    "cell": cell_id,
                    "seed": sd,
                    "method": m,
                    "cost": r.cost / cell.T,
                    "loss": r.decision_loss / cell.T,
                    "query_cost": r.query_cost / cell.T,
                    "switch_cost": r.switch_cost / cell.T,
                    "queries": r.queries,
                    "switches": r.switches,
                    "fp": int((r.fp_regime or 0) > 0),
                    "promoted": int(r.promotions > 0),
                    "correct": int(r.promotions > (r.fp_regime or 0)),
                }
            )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=list(SEEDS))
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--n", type=int, default=None, help="seeds per cell")
    ap.add_argument("--kappa", type=float, default=0.05)
    ap.add_argument("--q", type=float, default=0.01)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    n = (
        a.n
        or {"tune": 20, "eval": 60, "ablate": 60, "null": 500, "eval2": 60, "null2": 500}[a.stage]
    )
    out = Path(a.out or ROOT / "outputs/gaver/wp2" / a.stage)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "rows.csv"
    methods = methods_for(a.stage, a)
    done = set()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            done = {(r["cell"], int(r["seed"]), r["method"]) for r in csv.DictReader(f)}
    jobs = []
    s0 = SEEDS[a.stage]
    for cell in cells_for(a.stage):
        for i in range(0, n, CHUNK):
            seeds = list(range(s0 + i, s0 + min(n, i + CHUNK)))
            todo = [m for m in methods if any((cell.cell_id, sd, m) not in done for sd in seeds)]
            if todo:
                jobs.append(
                    (
                        a.stage,
                        cell.cell_id,
                        cell if cell.cell_id.endswith("_NULL") else None,
                        seeds,
                        todo,
                    )
                )
    jobs.sort(key=lambda j: j[3][0])  # seed-chunk major: partial runs give equal n per cell
    print(f"{a.stage}: {len(jobs)} jobs, methods={methods}", flush=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f, Pool(a.workers) as pool:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        for k, rows in enumerate(pool.imap_unordered(task, jobs), 1):
            w.writerows(rows)
            f.flush()
            if k % 10 == 0:
                print(f"{k}/{len(jobs)}", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
