"""PAVE-EF comparator panel (docs/methods_recovery/71_PAVE_SOTA_PANEL_PROTOCOL.md).

python scripts/methods_recovery/pave_panel.py eval --workers 5
python scripts/methods_recovery/pave_panel.py analyse
"""

from __future__ import annotations

import json
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts/methods_recovery"), str(ROOT / "scripts"), str(ROOT / "src")]
import numpy as np
import pave_c3 as c3
import pave_ef as pe

OUT = ROOT / "outputs/methods_recovery/pave_panel"
BASE, N, CHUNK = 102500000, 30, 10
PARTS = ("pave", "episode_front")
GATED = (
    "episode_geo",
    "episode_equal",
    "allonset_edetector",
    "c2_rho0.75",
    "c1_hmm_cs",
    "markov_lr_gate",
    "thinned_hedged_gate",
    "dss",
)
UNGATED = ("periodic_mean", "dal_restart", "pacing_bernoulli", "uniform")
ARMS = ("pave_ef", *PARTS, *GATED, *UNGATED, "no_switch")
CLAIM = (*PARTS, *GATED)


def make(arm, cfg, sp):
    from run_atlas_cycle7_validation_v1 import make_method

    from shiftlab.gaver.integrated import GaverMethod

    if arm == "pave_ef":
        return pe.PaveEF()
    if arm == "pave":
        return GaverMethod("dss", "pave")
    return make_method(arm, cfg, sp)


def task(job):
    from run_atlas_cycle7_validation_v1 import specs

    cid, cell, seeds = job
    sp, rows = specs(), []
    for sd in seeds:
        cfg, stream = cell.config(sd), pe.fa.make_stream(cell, sd)
        for arm in ARMS:
            r = pe.fa.run_for(cell, stream, make(arm, cfg, sp), cfg)
            assert r.queries <= cfg.B
            rows.append(
                {
                    "cell": cid,
                    "seed": sd,
                    "arm": arm,
                    "cost": float(r.cost) / cell.T,
                    "queries": int(r.queries),
                    "switches": int(r.switches),
                }
            )
    return rows


def run(workers):
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []
    for i, (_d, cid) in enumerate(c3.CELLS):
        cell, s0 = c3.cell_obj(cid), BASE + 1000 * i
        jobs += [
            (cid, cell, list(range(s0 + k, s0 + min(N, k + CHUNK)))) for k in range(0, N, CHUNK)
        ]
    with open(OUT / "rows.jsonl", "w") as f, Pool(workers) as pool:
        for k, rows in enumerate(pool.imap_unordered(task, jobs), 1):
            f.writelines(json.dumps(r) + "\n" for r in rows)
            f.flush()
            if k % 10 == 0:
                print(f"{k}/{len(jobs)}", flush=True)
    print("done", len(jobs), flush=True)


def analyse():
    import pandas as pd

    d = pd.read_json(OUT / "rows.jsonl", lines=True).drop_duplicates(["cell", "seed", "arm"])
    piv = d.pivot_table(index=["cell", "seed"], columns="arm", values="cost")
    cells = [c for _, c in c3.CELLS]
    rng = np.random.default_rng(20261110)
    res = {x: c3.contrast(piv, cells, "pave_ef", x, rng) for x in ARMS if x != "pave_ef"}
    order = sorted(CLAIM, key=lambda x: res[x][3])
    holm, run_max = {}, 0.0
    for r, x in enumerate(order):
        run_max = max(run_max, min(1.0, (len(order) - r) * res[x][3]))
        holm[x] = run_max
    pc = piv.groupby(level=0).mean().mean()
    print(f"pooled J/T pave_ef {pc['pave_ef']:.4f}")
    for x in ARMS[1:]:
        tag = "claim" if x in CLAIM else ("UNGATED: no FP control" if x in UNGATED else "floor")
        h = f"p_holm={holm[x]:.2g}" if x in holm else ""
        print(
            f"pave_ef - {x:20s} {res[x][0]:+.2f}% [{res[x][1]:+.2f}, {res[x][2]:+.2f}] "
            f"J/T {pc[x]:.4f} {h} ({tag})"
        )
    beats = [x for x in CLAIM if res[x][0] < 0 and holm[x] < 0.05]
    print(f"beats {len(beats)}/{len(CLAIM)} claim-bearing comparators: {beats}")
    print("SOTA PANEL:", "BEATS PANEL" if len(beats) == len(CLAIM) else "PARTIAL")
    print("CONTRAPTION (beats original parts):", all(x in beats for x in PARTS))


if __name__ == "__main__":
    w = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 5
    run(w) if sys.argv[1] == "eval" else analyse()
