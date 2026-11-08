"""Track C matched-acquisition comparison: PAVE vs simple schedules vs ef_sched, same DSS-shell evidence.

Only the request rule differs between arms (frozen DSS-shell evidence/decision rule everywhere).
  ef_sched        = episode_front's acquisition schedule: ``t in uniform_calendar(T, B, d)``
                    (data-independent, parameter-free; see docs/methods_recovery/41_PAVE_MATCHED.md).
  pave            = GaverMethod("dss", "pave") (delay-gated PAVE, reserve off, kappa .1, q .03).
  pave_nopend     = PAVE with ``pending=False`` (posterior ignores pending labels; fixed pending cap
                    instead of ceil(d*B_rem/H_rem)).
  pave_nodeadline = PAVE with ``deadline=False`` (value horizon R = T-t+1, no post-arrival offset).
  S1/S2/S3/S4     = simple rules of pave_plus_feasibility.SimpleAcq (tuned per delay on tuning seeds).
  episode_front   = native Atlas baseline (own evidence), descriptive reference only.

  python scripts/methods_recovery/pave_matched.py gate
  python scripts/methods_recovery/pave_matched.py tune --workers 6     # S1/S2/S3 grids, then S4, then best-matched
  python scripts/methods_recovery/pave_matched.py eval --workers 6
  python scripts/methods_recovery/pave_matched.py analyse

Seeds (configs/seed_registry.yaml): pave_c_tuning 101700000+100*cell_index (20 used),
pave_c_eval 101800000+100*cell_index (60 used). No re-tuning after eval.
"""

from __future__ import annotations

import dataclasses
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts"), str(ROOT / "scripts/methods_recovery")]

import numpy as np
from pave_plus_feasibility import GATE_ON_50, SimpleAcq, arm_name, boot_rel, inventory, to_d
from run_atlas_cycle7_validation_v1 import make_method
from run_atlas_dss_tuning_v1 import build_cell

from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import uniform_calendar
from shiftlab.gaver.integrated import PAVE_TUNED, GaverMethod, pave_active

OUT = ROOT / "outputs/methods_recovery/pave_matched"
TUNE_BASE, EVAL_BASE = 101700000, 101800000
N_TUNE, N_EVAL, CHUNK = 20, 60, 10
LONG = ("d50", "d100", "d200")

CTRL_10 = [
    f"on{o}_L{L}_{e}_harmful_d10_b{b}_s0.1"
    for (o, L, e) in (("0.6", "1", "strong"), ("0.3", "0.6", "strong"), ("0.6", "1", "medium"))
    for b in ("0.05", "0.1")
]
CELLS = [(f"d{d}", to_d(c, d)) for d in (50, 100, 200) for c in GATE_ON_50] + [
    ("ctl10", c) for c in CTRL_10
]
CELL_INDEX = {cid: i for i, (_, cid) in enumerate(CELLS)}
GROUP = {cid: g for g, cid in CELLS}
GROUPS = {g: [c for gg, c in CELLS if gg == g] for g in ("d50", "d100", "d200", "ctl10")}
GRID = {
    "S1": [("m", m) for m in (0, 25, 50, 100, 200)],
    "S2": [("cap", c) for c in (1, 2, 3, 5, 8)],
    "S3": [("f", f) for f in (0.5, 0.6, 0.7, 0.8, 0.9)],
}


class EfSched(GaverMethod):
    """DSS shell + DSS evidence; request rule = episode_front's calendar, nothing else.

    episode_front (``EpisodeComposition("front")``) returns ``t in uniform_calendar(T, B, d)`` from
    ``decide``: a fixed, data-independent, parameter-free calendar of up to B nearly equally spaced
    rounds in [1, T-d]. ``front`` names its alpha spending (all alpha on episode 0), not the schedule.
    No restart bursts. ``can_query`` still enforces ``used < B`` and ``t + d <= T``.
    """

    def __init__(self):
        super().__init__("dss", "dss")
        self.name = "ef_sched"

    def _init(self) -> None:
        super()._init()
        self.efcal = uniform_calendar(self.cfg.T, self.cfg.B, self.cfg.d)

    def _query(self, t: int) -> bool:
        return t in self.efcal and self.can_query(t)


class PaveNoPendInfo(GaverMethod):
    """PAVE with pending labels hidden from the value-of-label rollout only.

    ``pending=True`` is kept, so the adaptive pending capacity ceil(d*B_rem/H_rem) stays; but inside
    ``_rollout`` the pending set is empty (no pending term in the posterior sample size or in the
    last-update time), isolating the rollout's pending-label-aware term from the capacity rule.
    """

    def _rollout(self, *a, **k):
        saved = self.pending_events
        self.pending_events = set()
        try:
            return super()._rollout(*a, **k)
        finally:
            self.pending_events = saved


def make_arm(arm: str, cfg, sp):
    if arm in ("dss", "uniform", "episode_front"):
        return make_method(arm, cfg, sp)
    if arm == "ef_sched":
        return EfSched()
    if arm == "pave":
        return GaverMethod("dss", "pave")
    if arm == "pave_nopend":
        return GaverMethod("dss", "pave", pave=dataclasses.replace(PAVE_TUNED, pending=False))
    if arm == "pave_nopendinfo":
        return PaveNoPendInfo("dss", "pave")
    if arm == "pave_nodeadline":
        return GaverMethod("dss", "pave", pave=dataclasses.replace(PAVE_TUNED, deadline=False))
    rule, *rest = arm.split("_")
    kw = {}
    for tok in rest:
        key = tok.rstrip("0123456789.")
        kw[key] = float(tok[len(key) :])
    return SimpleAcq(
        rule,
        m=int(kw.get("m", 0)),
        cap=int(kw["cap"]) if "cap" in kw else None,
        f=kw.get("f", 0.5),
    )


def cell_obj(cid: str):
    for d in (100, 200):
        if f"_d{d}_" in cid:
            return dataclasses.replace(build_cell(cid.replace(f"_d{d}_", "_d50_")), d=d)
    return build_cell(cid)


def task(job):
    stage, cid, seeds, arms = job
    from run_atlas_cycle7_validation_v1 import specs

    cell, sp = cell_obj(cid), specs()
    rows = []
    for sd in seeds:
        cfg, stream = cell.config(sd), fa.make_stream(cell, sd)
        for arm in arms:
            r = fa.run_for(cell, stream, make_arm(arm, cfg, sp), cfg)
            assert r.queries <= cfg.B, "hard budget violated"
            pend, arr = inventory(np.asarray(r.query_mask), cfg.d, cell.T)
            rows.append(
                {
                    "stage": stage, "cell": cid, "seed": sd, "arm": arm, "gate": bool(pave_active(cfg)),
                    "cost": float(r.cost) / cell.T, "loss": float(r.decision_loss) / cell.T,
                    "queries": int(r.queries), "switches": int(r.switches),
                    "pending_mean": pend, "arrive_before_T": arr,
                }
            )  # fmt: skip
    return rows


def simple_arms():
    return [arm_name(r, **{k: v}) for r, g in GRID.items() for k, v in g]


def picks_path():
    return OUT / "picks.json"


def jobs_for(stage):
    jobs = []
    if stage == "tune":
        arms = ["ef_sched"] + simple_arms()
        for g, cid in CELLS:
            if g != "ctl10":
                base = TUNE_BASE + 100 * CELL_INDEX[cid]
                jobs.append((stage, cid, list(range(base, base + N_TUNE)), arms))
        return jobs
    pk = json.loads(picks_path().read_text())
    if stage == "tune_s4":
        for g, cid in CELLS:
            if g != "ctl10":
                base = TUNE_BASE + 100 * CELL_INDEX[cid]
                jobs.append((stage, cid, list(range(base, base + N_TUNE)), [pk[g]["S4"]]))
        return jobs
    for g, cid in CELLS:
        base = EVAL_BASE + 100 * CELL_INDEX[cid]
        if g == "ctl10":
            arms = ["dss", "ef_sched", "episode_front", pk["d50"]["S1"], pk["d50"]["S4"]]
        else:
            arms = [
                "ef_sched", "episode_front", "pave", "pave_nopend", "pave_nopendinfo", "pave_nodeadline",
                *[pk[g][r] for r in ("S1", "S2", "S3", "S4")],
            ]  # fmt: skip
        for k in range(0, N_EVAL, CHUNK):
            seeds = list(range(base + k, base + k + CHUNK))
            jobs.append((stage, cid, seeds, list(dict.fromkeys(arms))))
    return jobs


def run_stage(stage, workers):
    OUT.mkdir(parents=True, exist_ok=True)
    fstage = "tune" if stage == "tune_s4" else stage
    path = OUT / f"rows_{fstage}.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            done.add((r["cell"], r["seed"], r["arm"]))
    jobs = []
    for st, cid, seeds, arms in jobs_for(stage):
        todo = [a for a in arms if not all((cid, s, a) in done for s in seeds)]
        if todo:
            jobs.append((st, cid, seeds, todo))
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


def cellmeans(rows):
    acc = {}
    for r in rows:
        acc.setdefault((r["cell"], r["arm"]), []).append(r["cost"])
    return {k: float(np.mean(v)) for k, v in acc.items()}


def select_s123():
    cm = cellmeans(load("tune"))
    picks, table = {}, {}
    for g in LONG:
        cids = GROUPS[g]
        picks[g] = {}
        for rule, grid in GRID.items():
            scored = [
                (
                    float(np.mean([cm[(c, arm_name(rule, **{k: v}))] for c in cids])),
                    arm_name(rule, **{k: v}),
                )
                for k, v in grid
            ]
            table[f"{g}:{rule}"] = sorted(scored)
            picks[g][rule] = min(scored)[1]
        m = picks[g]["S1"].split("_m")[1]
        cap = picks[g]["S2"].split("_cap")[1]
        picks[g]["S4"] = f"S4_m{m}_cap{cap}"
        table[f"{g}:ef_sched"] = float(np.mean([cm[(c, "ef_sched")] for c in cids]))
    picks_path().write_text(json.dumps(picks, indent=1))
    (OUT / "tuning_table.json").write_text(json.dumps(table, indent=1))
    print(json.dumps(picks, indent=1))


def select_best_matched():
    """Per delay: argmin pooled tuning J/T over {S1, S3, ef_sched, S4} (tuning seeds only)."""
    cm = cellmeans(load("tune"))
    pk = json.loads(picks_path().read_text())
    for g in LONG:
        cids = GROUPS[g]
        cand = {"S1": pk[g]["S1"], "S3": pk[g]["S3"], "S4": pk[g]["S4"], "ef_sched": "ef_sched"}
        score = {k: float(np.mean([cm[(c, a)] for c in cids])) for k, a in cand.items()}
        order = ["ef_sched", "S1", "S3", "S4"]  # ties -> earlier in this order
        best = min(order, key=lambda k: (round(score[k], 12), order.index(k)))
        pk[g].update(best_matched_rule=best, best_matched_arm=cand[best], tuning_scores=score)
    picks_path().write_text(json.dumps(pk, indent=1))
    print(
        json.dumps(
            {g: [pk[g]["best_matched_rule"], pk[g]["tuning_scores"]] for g in LONG}, indent=1
        )
    )


def analyse():
    pk = json.loads(picks_path().read_text())
    per = {}
    for r in load("eval"):
        per.setdefault((r["cell"], r["arm"]), {})[r["seed"]] = r

    def arr(cid, arm, key="cost"):
        d = per[(cid, arm)]
        return np.array([d[s][key] for s in sorted(d)])

    out = {"picks": pk, "cells": {}, "pooled": {}, "gate": {}}
    for g, cid in CELLS:
        out["cells"][cid] = {
            a: {
                "n": len(per[(cid, a)]), "cost": float(arr(cid, a).mean()),
                "queries": float(arr(cid, a, "queries").mean()),
                "arrive_before_T": float(np.nanmean(arr(cid, a, "arrive_before_T"))),
                "pending_mean": float(arr(cid, a, "pending_mean").mean()),
                "switches": float(arr(cid, a, "switches").mean()),
            }
            for a in sorted({a for (c, a) in per if c == cid})
        }  # fmt: skip
        if g != "ctl10":
            out["gate"][cid] = sorted(
                {bool(r["gate"]) for (c, a), d in per.items() if c == cid for r in d.values()}
            )
    assert all(v == [True] for v in out["gate"].values()), "gate off in some long-delay cell"
    pools = {g: GROUPS[g] for g in LONG}
    pools["all27"] = GROUPS["d50"] + GROUPS["d100"] + GROUPS["d200"]

    def armof(role, c):
        g = GROUP[c]
        if role in (
            "ef_sched",
            "episode_front",
            "pave",
            "pave_nopend",
            "pave_nopendinfo",
            "pave_nodeadline",
        ):
            return role
        return pk[g]["best_matched_arm"] if role == "best" else pk[g][role]

    roles = ["ef_sched", "episode_front", "pave", "pave_nopend", "pave_nopendinfo", "pave_nodeadline",
             "S1", "S2", "S3", "S4", "best"]  # fmt: skip
    con = {
        "pave_minus_best_matched": ("pave", "best"),
        "pave_minus_ef_sched": ("pave", "ef_sched"),
        "pave_minus_pave_nopend": ("pave", "pave_nopend"),
        "pave_minus_pave_nopendinfo": ("pave", "pave_nopendinfo"),
        "pave_minus_pave_nodeadline": ("pave", "pave_nodeadline"),
        "pave_minus_episode_front_native": ("pave", "episode_front"),
        "pave_minus_S1": ("pave", "S1"), "pave_minus_S3": ("pave", "S3"), "pave_minus_S4": ("pave", "S4"),
        "best_matched_minus_ef_sched": ("best", "ef_sched"),
        "ef_sched_minus_episode_front_native": ("ef_sched", "episode_front"),
    }  # fmt: skip
    for pname, cids in pools.items():
        S = {r: {c: arr(c, armof(r, c)) for c in cids} for r in roles}
        ref = S["ef_sched"]
        res = {"arms": {}}
        for r in roles:
            res["arms"][r] = {
                "mean_JT": float(np.mean([S[r][c].mean() for c in cids])),
                **{
                    k: float(np.mean([np.nanmean(arr(c, armof(r, c), k)) for c in cids]))
                    for k in ("queries", "arrive_before_T", "pending_mean", "switches")
                },
            }
        res["contrasts_pct_of_ef_sched"] = {
            k: boot_rel(S[a], S[b], ref) for k, (a, b) in con.items()
        }
        out["pooled"][pname] = res
    c = out["pooled"]["all27"]["contrasts_pct_of_ef_sched"]
    pt, lo, hi = c["pave_minus_best_matched"]  # negative = PAVE cheaper
    gap, glo, ghi = -pt, -hi, -lo  # PAVE advantage and its CI
    ef, npd = c["pave_minus_ef_sched"], c["pave_minus_pave_nopend"]
    stop = gap < 1.0
    adv = (not stop) and gap >= 2.0 and glo > 0 and ef[2] < 0 and npd[2] < 0
    out["verdict"] = {
        "pave_advantage_over_best_matched_pct": gap, "ci_adv": [glo, ghi],
        "pave_minus_ef_sched": ef, "pave_minus_nopend": npd,
        "label": "STOP" if stop else ("ADVANCE" if adv else "WEAK"),
    }  # fmt: skip
    ctl = GROUPS["ctl10"]
    out["control_pooled_JT"] = {
        a: float(np.mean([arr(c, a).mean() for c in ctl]))
        for a in sorted({a for (c, a) in per if c in ctl})
    }
    refc = {c: arr(c, "dss") for c in ctl}
    out["control_vs_dss_pct"] = {
        a: boot_rel({c: arr(c, a) for c in ctl}, refc, refc)
        for a in out["control_pooled_JT"]
        if a != "dss"
    }
    (OUT / "analysis.json").write_text(json.dumps(out, indent=1))
    print(
        json.dumps(
            {k: out[k] for k in ("verdict", "control_pooled_JT", "control_vs_dss_pct")}, indent=1
        )
    )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "eval", "analyse", "smoke", "gate"])
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    assert a.workers <= 6
    OUT.mkdir(parents=True, exist_ok=True)
    if a.stage == "analyse":
        analyse()
    elif a.stage == "gate":
        rows = []
        for g, cid in CELLS:
            cfg = cell_obj(cid).config(TUNE_BASE)
            thr = 2 * cfg.T / (cfg.B + 2)
            rows.append({"cell": cid, "d": cfg.d, "T": cfg.T, "B": cfg.B, "threshold": thr,
                         "gate": bool(pave_active(cfg))})  # fmt: skip
        (OUT / "gate_check.json").write_text(json.dumps(rows, indent=1))
        bad = [r for r in rows if not r["gate"] and r["d"] != 10]
        print(f"{len(rows)} cells; gate-off long-delay cells: {bad}")
    elif a.stage == "smoke":
        cid = to_d(GATE_ON_50[4], 200)
        arms = ["uniform", "ef_sched", "episode_front", "pave", "pave_nopend", "pave_nopendinfo", "pave_nodeadline",
                "S1_m0", "S1_m50", "S4_m50_cap5"]  # fmt: skip
        t0 = time.time()
        rows = task(("smoke", cid, list(range(TUNE_BASE + 9900, TUNE_BASE + 9903)), arms))
        cm = cellmeans(rows)
        for a_ in arms:
            rr = [r for r in rows if r["arm"] == a_]
            print(a_, round(cm[(cid, a_)], 4), np.mean([r["queries"] for r in rr]),
                  round(np.mean([r["pending_mean"] for r in rr]), 2))  # fmt: skip
        print(f"{time.time() - t0:.1f}s")
    elif a.stage == "tune":
        run_stage("tune", a.workers)
        select_s123()
        run_stage("tune_s4", a.workers)
        select_best_matched()
    else:
        run_stage(a.stage, a.workers)
