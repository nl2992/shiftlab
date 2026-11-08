"""Matched comparator for doc 42 (amendment): ef_dss = PaveEF engine/spec with PAVE off (uniform calendar).

Runs ef_dss on the same pave_ef_eval seeds/cells, then analyses pave_ef vs ef_dss, pave_ef vs
pave_ef_nopendinfo and pave_ef vs native episode_front (pooled over the 27 long-delay cells,
% of the reference J/T, paired bootstrap over seeds within cells, 4000 resamples).
usage: python scripts/methods_recovery/pave_ef_matched.py run|analyse [--workers 6]
"""

import json
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts/methods_recovery")]
import numpy as np
import pave_ef as pe

OUT = pe.OUT


class EFDSS(pe.PaveEF):
    def _init(self):
        super()._init()
        self.pave_on = False  # engine's own uniform calendar, same DSS spec

    def __init__(self):
        super().__init__()
        self.name = "ef_dss"


def task(job):
    cid, cell, seeds = job
    rows = []
    for sd in seeds:
        cfg, stream = cell.config(sd), pe.fa.make_stream(cell, sd)
        r = pe.fa.run_for(cell, stream, EFDSS(), cfg)
        assert r.queries <= cfg.B
        rows.append(
            {
                "stage": "eval",
                "cell": cid,
                "seed": sd,
                "arm": "ef_dss",
                "cost": float(r.cost) / cell.T,
                "queries": int(r.queries),
            }
        )
    return rows


def run(workers):
    jobs = []
    for i, (_g, cid) in enumerate(pe.LONG_CELLS):
        cell = pe.cell_obj(cid)
        s0 = pe.EVAL_BASE + 100 * i
        for k in range(0, pe.N_EVAL, pe.CHUNK):
            jobs.append((cid, cell, list(range(s0 + k, s0 + min(pe.N_EVAL, k + pe.CHUNK)))))
    with open(OUT / "rows_eval_efdss.jsonl", "w") as f, Pool(workers) as pool:
        for rows in pool.imap_unordered(task, jobs):
            f.writelines(json.dumps(r) + "\n" for r in rows)
    print("done", len(jobs))


def analyse():
    import pandas as pd

    rows = [
        json.loads(x)
        for p in ("rows_eval.jsonl", "rows_eval_efdss.jsonl")
        for x in (OUT / p).read_text().splitlines()
    ]
    d = pd.DataFrame(rows)
    d = d[d.cell.isin([c for _, c in pe.LONG_CELLS])]
    piv = d.pivot_table(index=["cell", "seed"], columns="arm", values="cost")
    rng = np.random.default_rng(20261108)
    res = {}
    for a, b in (
        ("pave_ef", "ef_dss"),
        ("pave_ef", "pave_ef_nopendinfo"),
        ("pave_ef", "episode_front"),
        ("ef_dss", "episode_front"),
    ):
        cells = piv.index.get_level_values(0).unique()
        diffs = [(piv.loc[c][a] - piv.loc[c][b]).to_numpy() for c in cells]
        ref = np.mean([piv.loc[c][b].mean() for c in cells])
        point = np.mean([x.mean() for x in diffs]) / ref * 100
        bs = [
            np.mean([x[rng.integers(0, len(x), len(x))].mean() for x in diffs]) / ref * 100
            for _ in range(4000)
        ]
        res[f"{a}-{b}"] = (point, *np.percentile(bs, [2.5, 97.5]))
        print(f"{a} - {b}: {point:+.2f}% [{res[f'{a}-{b}'][1]:+.2f}, {res[f'{a}-{b}'][2]:+.2f}]")
    print("pooled J/T:", piv.mean().round(4).to_dict())
    (OUT / "analysis_matched.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    w = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 6
    run(w) if sys.argv[1] == "run" else analyse()
