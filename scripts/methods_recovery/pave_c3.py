"""PAVE-EF C3 confirmation runner (docs/methods_recovery/70_PAVE_C3_PROTOCOL.md).

python scripts/methods_recovery/pave_c3.py eval --workers 6
python scripts/methods_recovery/pave_c3.py null --workers 3
python scripts/methods_recovery/pave_c3.py analyse
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts/methods_recovery")]
import numpy as np
import pave_ef as pe
from pave_ef_matched import NoVoI
from pave_matched import GATE_ON_50, build_cell
from scipy.stats import beta

OUT = ROOT / "outputs/methods_recovery/pave_c3"
EVAL_BASE, NULL_BASE, N_EVAL, N_NULL, CHUNK = 102300000, 102400000, 100, 500, 10
IN_D, UNSEEN_D = (50, 100, 200), (75, 150, 300)
ARMS = ("episode_front", "pave_ef", "pave_ef_novoi")


def cell_id(c50: str, d: int) -> str:
    return re.sub(r"_d50_", f"_d{d}_", c50)


CELLS = [(d, cell_id(c, d)) for d in IN_D + UNSEEN_D for c in GATE_ON_50]


def cell_obj(cid: str):
    d = int(re.search(r"_d(\d+)_", cid).group(1))
    return dataclasses.replace(build_cell(re.sub(r"_d\d+_", "_d50_", cid)), d=d)


def make(arm, cfg):
    if arm == "pave_ef_novoi":
        return NoVoI()
    return pe.make_arm(arm, cfg)


def task(job):
    stage, cid, cell, seeds, arms = job
    rows = []
    for sd in seeds:
        cfg, stream = cell.config(sd), pe.fa.make_stream(cell, sd)
        assert stage == "null" or pe.pave_active(cfg), f"gate off in {cid}"
        for arm in arms:
            r = pe.fa.run_for(cell, stream, make(arm, cfg), cfg)
            assert r.queries <= cfg.B
            rows.append(
                {
                    "stage": stage,
                    "cell": cid,
                    "seed": sd,
                    "arm": arm,
                    "cost": float(r.cost) / cell.T,
                    "queries": int(r.queries),
                    "fp": int((r.fp_regime or 0) > 0),
                }
            )
    return rows


def run(stage, workers):
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []
    if stage == "eval":
        for i, (_d, cid) in enumerate(CELLS):
            cell, s0 = cell_obj(cid), EVAL_BASE + 1000 * i
            jobs += [
                ("eval", cid, cell, list(range(s0 + k, s0 + min(N_EVAL, k + CHUNK))), ARMS)
                for k in range(0, N_EVAL, CHUNK)
            ]
    else:
        for i, (cid, cell) in enumerate(pe.null_cells()):
            s0 = NULL_BASE + 1000 * i
            jobs += [
                (
                    "null",
                    cid,
                    cell,
                    list(range(s0 + k, s0 + min(N_NULL, k + CHUNK))),
                    ("episode_front", "pave_ef"),
                )
                for k in range(0, N_NULL, CHUNK)
            ]
    with open(OUT / f"rows_{stage}.jsonl", "w") as f, Pool(workers) as pool:
        for k, rows in enumerate(pool.imap_unordered(task, jobs), 1):
            f.writelines(json.dumps(r) + "\n" for r in rows)
            f.flush()
            if k % 20 == 0:
                print(f"{k}/{len(jobs)}", flush=True)
    print("done", len(jobs), flush=True)


def contrast(piv, cells, a, b, rng, nb=10000):
    diffs = [(piv.loc[c][a] - piv.loc[c][b]).to_numpy() for c in cells]
    ref = np.mean([piv.loc[c][b].mean() for c in cells])
    point = np.mean([x.mean() for x in diffs]) / ref * 100
    bs = (
        np.array(
            [np.mean([x[rng.integers(0, len(x), len(x))].mean() for x in diffs]) for _ in range(nb)]
        )
        / ref
        * 100
    )
    p = 2 * min((bs >= 0).mean(), (bs <= 0).mean())
    return point, *np.percentile(bs, [2.5, 97.5]), max(p, 1 / nb)


def analyse():
    import pandas as pd

    d = pd.read_json(OUT / "rows_eval.jsonl", lines=True).drop_duplicates(["cell", "seed", "arm"])
    piv = d.pivot_table(index=["cell", "seed"], columns="arm", values="cost")
    rng = np.random.default_rng(20261109)
    allc = [c for _, c in CELLS]
    p1 = contrast(piv, allc, "pave_ef", "episode_front", rng)
    p2 = contrast(piv, allc, "pave_ef", "pave_ef_novoi", rng)
    ps = sorted([(p1[3], "P1"), (p2[3], "P2")])
    holm = {ps[0][1]: min(1, 2 * ps[0][0]), ps[1][1]: min(1, max(2 * ps[0][0], ps[1][0]))}
    print(
        f"P1 pave_ef - episode_front: {p1[0]:+.2f}% [{p1[1]:+.2f}, {p1[2]:+.2f}] p_holm={holm['P1']:.2g}"
    )
    print(
        f"P2 pave_ef - pave_ef_novoi: {p2[0]:+.2f}% [{p2[1]:+.2f}, {p2[2]:+.2f}] p_holm={holm['P2']:.2g}"
    )
    for label, ds in (
        ("in-family", IN_D),
        ("unseen", UNSEEN_D),
        *((f"d{x}", (x,)) for x in IN_D + UNSEEN_D),
    ):
        cs = [c for dd, c in CELLS if dd in ds]
        r = contrast(piv, cs, "pave_ef", "episode_front", rng, 2000)
        print(f"  {label:9s} pave_ef - episode_front: {r[0]:+.2f}% [{r[1]:+.2f}, {r[2]:+.2f}]")
    pc = piv.groupby(level=0).mean()
    lose = (pc["pave_ef"] > pc["episode_front"]).sum()
    print(f"cells where pave_ef loses: {lose}/{len(pc)}; pooled J/T", pc.mean().round(4).to_dict())
    print("labels:", d.groupby("arm").queries.mean().round(1).to_dict())
    guard = True
    if (OUT / "rows_null.jsonl").exists():
        n = pd.read_json(OUT / "rows_null.jsonl", lines=True).drop_duplicates(
            ["cell", "seed", "arm"]
        )
        for (cid, arm), g in n.groupby(["cell", "arm"]):
            k, m = int(g.fp.sum()), len(g)
            ucb = 1.0 if k >= m else float(beta.ppf(0.95, k + 1, m - k))
            indep = "rho0_" in cid or "f1null" in cid
            if arm == "pave_ef" and indep and ucb > 0.10:
                guard = False
            print(
                f"  null {cid:28s} {arm:14s} fp {k}/{m} UCB {ucb:.3f}{'  (guard)' if indep else ''}"
            )
    else:
        guard = None
    ok = p1[0] <= -2 and holm["P1"] < 0.05 and p2[0] < 0 and holm["P2"] < 0.05 and guard is True
    print("C3 VERDICT:", "PASS" if ok else ("PENDING-NULL" if guard is None else "FAIL"))


if __name__ == "__main__":
    w = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 6
    run(sys.argv[1], w) if sys.argv[1] in ("eval", "null") else analyse()
