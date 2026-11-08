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


class NoVoI(pe.PaveEF):
    """pave_ef with the VoI rollout replaced by a deadline-truncated calendar (Amendment 2)."""

    def __init__(self):
        super().__init__()
        self.name = "pave_ef_novoi"

    def _init(self):
        super()._init()
        self.last_q = -(10**9)

    def _pave_query(self, t):
        import math

        c = self.cfg
        if self.burst_left > 0 and len(self.pending_events) < 2 and self.can_query(t):
            self.burst_left -= 1
            self.last_q = t
            return True
        if not self.can_query(t) or len(self.pending_events) >= self.pending_capacity(t):
            return False
        b_eff = self._b_eff()
        if b_eff <= 0:
            return False
        cap = max(1, math.ceil(self._p("acquisition", "burst_frac") * c.B)) + math.floor(
            2 * c.B * t / c.T
        )
        if self.used >= cap:
            return False
        g = max(1, math.ceil(max(1, c.T - c.d - t + 1) / b_eff))
        if t - self.last_q >= g:
            self.last_q = t
            return True
        return False


ARM_CLS = {"ef_dss": None, "pave_ef_novoi": NoVoI}


def task(job):
    cid, cell, seeds = job[:3]
    arm = job[3] if len(job) > 3 else "ef_dss"
    rows = []
    for sd in seeds:
        cfg, stream = cell.config(sd), pe.fa.make_stream(cell, sd)
        pol = EFDSS() if arm == "ef_dss" else ARM_CLS[arm]()
        r = pe.fa.run_for(cell, stream, pol, cfg)
        assert r.queries <= cfg.B
        rows.append(
            {
                "stage": "eval",
                "cell": cid,
                "seed": sd,
                "arm": arm,
                "cost": float(r.cost) / cell.T,
                "queries": int(r.queries),
            }
        )
    return rows


def run(workers, arm="ef_dss"):
    jobs = []
    for i, (_g, cid) in enumerate(pe.LONG_CELLS):
        cell = pe.cell_obj(cid)
        s0 = pe.EVAL_BASE + 100 * i
        for k in range(0, pe.N_EVAL, pe.CHUNK):
            jobs.append((cid, cell, list(range(s0 + k, s0 + min(pe.N_EVAL, k + pe.CHUNK))), arm))
    fn = "rows_eval_efdss.jsonl" if arm == "ef_dss" else f"rows_eval_{arm}.jsonl"
    with open(OUT / fn, "w") as f, Pool(workers) as pool:
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
    arm = sys.argv[sys.argv.index("--arm") + 1] if "--arm" in sys.argv else "ef_dss"
    run(w, arm) if sys.argv[1] == "run" else analyse()
