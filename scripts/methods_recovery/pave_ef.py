"""PAVE's acquisition driving episode_front's OWN engine (Track C decisive test). See docs/methods_recovery/42_PAVE_ON_EF.md.

  python scripts/methods_recovery/pave_ef.py smoke
  python scripts/methods_recovery/pave_ef.py eval --workers 6
  python scripts/methods_recovery/pave_ef.py null --workers 6
  python scripts/methods_recovery/pave_ef.py analyse

Seeds: pave_ef_eval 102100000 + 100*cell_index (60 used); pave_ef_null 102200000 + 500*cell_index (500 used).
"""

from __future__ import annotations

import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts"), str(ROOT / "scripts/methods_recovery"),
                str(ROOT / "scripts/gaver")]  # fmt: skip

import numpy as np
from pave_matched import CELLS, GROUPS, LONG, cell_obj
from pave_plus_feasibility import boot_rel, inventory
from scipy.stats import beta

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import EpisodeComposition
from shiftlab.gaver.integrated import PAVE_TUNED, pave_active
from shiftlab.gaver.pave import PaveMethod

OUT = ROOT / "outputs/methods_recovery/pave_ef"
EVAL_BASE, NULL_BASE = 102100000, 102200000
N_EVAL, N_NULL, CHUNK = 60, 500, 10
LONG_CELLS = [(g, c) for g, c in CELLS if g != "ctl10"]
LCI = {c: i for i, (_, c) in enumerate(LONG_CELLS)}
_DSS = comp.dss_spec(4, True)


class PaveEF(EpisodeComposition):
    """EpisodeComposition("front") engine; request rule = PAVE governor (unchanged), delay-gated."""

    hide_pending = False

    def __init__(self, hide_pending: bool = False):
        super().__init__("front")
        self.pp = PAVE_TUNED
        self.hide_pending = hide_pending
        self.name = "pave_ef_nopendinfo" if hide_pending else "pave_ef"
        self.keep_audit = False
        self.audit = []
        self._in_roll = False

    def _init(self) -> None:
        super()._init()
        self.reserve_n = 0
        self.burst_left = 0
        self.pave_on = pave_active(self.cfg)

    def _p(self, slot: str, name: str):
        return _DSS.get(slot, name)

    def _ben(self, xs, n):
        return None if not xs else -float(np.mean(xs[-n:]))

    def _alpha_j(self, j: int) -> float:
        a = super()._alpha_j(j)
        return (
            a if (a > 0 or not self._in_roll) else 1e-300
        )  # reachability -> 0 once no e-process exists

    def _logE(self) -> float:
        try:
            return max(0.0, float(self.ep.log_e_value))
        except Exception:  # noqa: BLE001 - heuristic input only
            return 0.0

    _b_eff = PaveMethod._b_eff
    pending_capacity = PaveMethod.pending_capacity
    _posterior = PaveMethod._posterior
    _pave_query = PaveMethod._query

    def _rollout(self, *a, **k):
        self._in_roll = True
        saved = self.pending_events
        if self.hide_pending:
            self.pending_events = set()
        try:
            return PaveMethod._rollout(self, *a, **k)
        finally:
            self._in_roll = False
            self.pending_events = saved

    def decide(self, t, released):
        act, cal = super().decide(t, released)
        if not self.pave_on:
            return act, cal
        return act, self._pave_query(t)


def make_arm(arm: str, cfg, sp=None):
    if arm == "pave_ef":
        return PaveEF()
    if arm == "pave_ef_nopendinfo":
        return PaveEF(hide_pending=True)
    if arm == "episode_front":
        return fa.make_method("episode_front", fa.bernoulli_grid_spec(), cfg)
    raise ValueError(arm)


def task(job):
    stage, cid, cell, seeds, arms = job
    rows = []
    for sd in seeds:
        cfg, stream = cell.config(sd), fa.make_stream(cell, sd)
        for arm in arms:
            r = fa.run_for(cell, stream, make_arm(arm, cfg), cfg)
            assert r.queries <= cfg.B, "hard budget violated"
            pend, arr = inventory(np.asarray(r.query_mask), cfg.d, cell.T)
            rows.append(
                {
                    "stage": stage, "cell": cid, "seed": sd, "arm": arm, "gate": bool(pave_active(cfg)),
                    "cost": float(r.cost) / cell.T, "loss": float(r.decision_loss) / cell.T,
                    "queries": int(r.queries), "switches": int(r.switches),
                    "fp": int((r.fp_regime or 0) > 0), "promoted": int(r.promotions > 0),
                    "pending_mean": pend, "arrive_before_T": arr,
                }
            )  # fmt: skip
    return rows


ARMS = ["episode_front", "pave_ef", "pave_ef_nopendinfo"]


def null_cells():
    from run_gaver_factorial import null_cells as nc

    return [(cid, c) for cid, c in nc() if "_d50" in cid]


def jobs_for(stage):
    jobs = []
    if stage == "eval":
        for g, cid in LONG_CELLS:
            base = EVAL_BASE + 100 * LCI[cid]
            cell = cell_obj(cid)
            for k in range(0, N_EVAL, CHUNK):
                jobs.append((stage, cid, cell, list(range(base + k, base + k + CHUNK)), ARMS))
    else:
        for i, (cid, cell) in enumerate(null_cells()):
            base = NULL_BASE + 500 * i
            for k in range(0, N_NULL, 25):
                jobs.append((stage, cid, cell, list(range(base + k, base + k + 25)),
                             ["episode_front", "pave_ef"]))  # fmt: skip
    return jobs


def run_stage(stage, workers):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"rows_{stage}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            done.add((r["cell"], r["seed"], r["arm"]))
    jobs = []
    for st, cid, cell, seeds, arms in jobs_for(stage):
        todo = [a for a in arms if not all((cid, s, a) in done for s in seeds)]
        if todo:
            jobs.append((st, cid, cell, seeds, todo))
    print(f"{stage}: {len(jobs)} jobs", flush=True)
    t0 = time.time()
    with Pool(workers) as pool, path.open("a") as fh:
        for i, rows in enumerate(pool.imap_unordered(task, jobs), 1):
            for r in rows:
                fh.write(json.dumps(r) + "\n")
            fh.flush()
            if i % 10 == 0 or i == len(jobs):
                print(f"  {i}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)


def load(stage):
    return [json.loads(x) for x in (OUT / f"rows_{stage}.jsonl").read_text().splitlines()]


def cp_upper(k, n, level=0.95):
    return 1.0 if k == n else float(beta.ppf(level, k + 1, n - k))


def analyse():
    per = {}
    for r in load("eval"):
        per.setdefault((r["cell"], r["arm"]), {})[r["seed"]] = r

    def arr(cid, arm, key="cost"):
        d = per[(cid, arm)]
        return np.array([d[s][key] for s in sorted(d)])

    assert all(r["gate"] for d in per.values() for r in d.values()), "gate off"
    pools = {g: GROUPS[g] for g in LONG}
    pools["all27"] = sum((GROUPS[g] for g in LONG), [])  # noqa: RUF017
    con = {
        "pave_ef_minus_episode_front": ("pave_ef", "episode_front"),
        "pave_ef_minus_pave_ef_nopendinfo": ("pave_ef", "pave_ef_nopendinfo"),
        "pave_ef_nopendinfo_minus_episode_front": ("pave_ef_nopendinfo", "episode_front"),
    }
    out = {"pooled": {}, "cells": {}}
    for pname, cids in pools.items():
        S = {a: {c: arr(c, a) for c in cids} for a in ARMS}
        res = {"arms": {}}
        for a in ARMS:
            res["arms"][a] = {
                "mean_JT": float(np.mean([S[a][c].mean() for c in cids])),
                **{k: float(np.mean([np.nanmean(arr(c, a, k)) for c in cids]))
                   for k in ("queries", "arrive_before_T", "pending_mean", "switches", "promoted")},
            }  # fmt: skip
        res["contrasts_pct_of_episode_front"] = {
            k: boot_rel(S[a], S[b], S["episode_front"]) for k, (a, b) in con.items()
        }
        out["pooled"][pname] = res
    for g, cid in LONG_CELLS:
        out["cells"][cid] = {a: float(arr(cid, a).mean()) for a in ARMS}
    c = out["pooled"]["all27"]["contrasts_pct_of_episode_front"]
    pt, lo, hi = c["pave_ef_minus_episode_front"]
    npt, nlo, nhi = c["pave_ef_minus_pave_ef_nopendinfo"]
    adv = -pt
    stop = adv < 1.0
    go = (not stop) and pt <= -2.0 and hi < 0 and npt < 0 and nhi < 0
    out["verdict"] = {"advantage_pct": adv, "ci": [lo, hi], "pend_attr": [npt, nlo, nhi],
                      "label": "STOP" if stop else ("ADVANCE" if go else "WEAK")}  # fmt: skip
    wins = sum(out["cells"][c]["pave_ef"] < out["cells"][c]["episode_front"] for _, c in LONG_CELLS)
    out["cell_wins_vs_episode_front"] = wins
    if (OUT / "rows_null.jsonl").exists():
        acc = {}
        for r in load("null"):
            a = acc.setdefault((r["cell"], r["arm"]), [0, 0, 0])
            a[0] += r["fp"]
            a[1] += r["promoted"]
            a[2] += 1
        out["null"] = {
            f"{cid}|{arm}": {
                "n": n,
                "fp": k,
                "promoted": p,
                "fp_rate": k / n,
                "cp_ucb95": cp_upper(k, n),
            }
            for (cid, arm), (k, p, n) in sorted(acc.items())
        }
    (OUT / "analysis.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("verdict", "cell_wins_vs_episode_front")}, indent=1))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["smoke", "eval", "null", "analyse"])
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    assert a.workers <= 6
    OUT.mkdir(parents=True, exist_ok=True)
    if a.stage == "analyse":
        analyse()
    elif a.stage == "smoke":
        cid = LONG_CELLS[4][1]
        t0 = time.time()
        rows = task(
            ("smoke", cid, cell_obj(cid), list(range(EVAL_BASE + 9900, EVAL_BASE + 9903)), ARMS)
        )
        for arm in ARMS:
            rr = [r for r in rows if r["arm"] == arm]
            print(arm, round(np.mean([r["cost"] for r in rr]), 4), np.mean([r["queries"] for r in rr]),
                  np.mean([r["switches"] for r in rr]), np.mean([r["promoted"] for r in rr]))  # fmt: skip
        print(f"{time.time() - t0:.1f}s")
    else:
        run_stage(a.stage, a.workers)
