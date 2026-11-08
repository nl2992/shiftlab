# ruff: noqa: B023,F841,PLC3002  (closures used within the same loop iteration; analysis script)
"""PAVE+ feasibility (Track C): does a SIMPLE acquisition rule capture delay-gated PAVE's long-delay gain?

Evidence is fixed to the frozen DSS shell evidence (same as GAVE-R WP5); only the request rule differs.
Stages: tune (simple-rule single parameters, per delay) -> eval (all arms, fresh seeds) -> analyse.
Rows are appended to outputs/methods_recovery/pave_plus/rows_<stage>.jsonl (resumable by job key).

  python scripts/methods_recovery/pave_plus_feasibility.py tune --workers 6
  python scripts/methods_recovery/pave_plus_feasibility.py eval --workers 6
  python scripts/methods_recovery/pave_plus_feasibility.py analyse

Seeds (configs/seed_registry.yaml): pave_plus_tuning 101500000+100*cell_index (20 used),
pave_plus_eval 101600000+100*cell_index (60 used). No re-tuning after eval.
"""

from __future__ import annotations

import dataclasses
import json
import math
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

import numpy as np
from run_atlas_cycle7_validation_v1 import make_method
from run_atlas_dss_tuning_v1 import build_cell

from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver.integrated import GaverMethod, pave_active

OUT = ROOT / "outputs/methods_recovery/pave_plus"
TUNE_BASE, EVAL_BASE = 101500000, 101600000
N_TUNE, N_EVAL, CHUNK = 20, 60, 10

GATE_ON_50 = [
    "on0.3_L1_strong_harmful_d50_b0.05_s0.1",
    "on0.6_L0.6_strong_harmful_d50_b0.05_s0.1",
    "on0.6_L1_medium_harmful_d50_b0.05_s0.1",
    "on0.6_L1_strong_harmful_d50_b0.05_s0.05",
    "on0.6_L1_strong_harmful_d50_b0.05_s0.1",
    "on0.6_L1_strong_harmful_d50_b0.05_s0.5",
    "on0.6_L1_strong_harmful_d50_b0.1_s0.1",
    "on0.6_L1_strong_neutral_d50_b0.05_s0.1",
    "on0.8_L1_strong_harmful_d50_b0.05_s0.1",
]
CTRL_10 = [
    f"on{o}_L{L}_{e}_harmful_d10_b{b}_s0.1"
    for (o, L, e) in (("0.6", "1", "strong"), ("0.3", "0.6", "strong"), ("0.6", "1", "medium"))
    for b in ("0.05", "0.1")
]


def to_d(cid: str, d: int) -> str:
    return cid.replace("_d50_", f"_d{d}_")


# (group, cell_id) with a fixed global index for seed assignment
CELLS = (
    [("d50", c) for c in GATE_ON_50]
    + [("d100", to_d(c, 100)) for c in GATE_ON_50]
    + [("ctl10", c) for c in CTRL_10]
)
CELL_INDEX = {cid: i for i, (_, cid) in enumerate(CELLS)}
GROUP = {cid: g for g, cid in CELLS}

GRID = {
    "S1": [("m", m) for m in (0, 25, 50, 100)],
    "S2": [("cap", c) for c in (1, 2, 3, 5, 8)],
    "S3": [("f", f) for f in (0.5, 0.6, 0.7, 0.8, 0.9)],
}


def arm_name(rule: str, **kw) -> str:
    return rule + "".join(f"_{k}{v:g}" for k, v in kw.items())


class SimpleAcq(GaverMethod):
    """DSS shell + DSS evidence with a simple, paced, data-independent-or-pending-only request rule.

    The request at t depends on t, config, own request count and the pending count only (all in F_t).
    Rules: S1 deadline cutoff (pace over [1, T-d-m], none after), S2 pending cap, S3 front-loading
    (fraction f of B in the first half of [1, T-d]), S4 = S1 + S2. ``can_query`` still enforces
    ``used < B`` and ``t + d <= T``.
    """

    def __init__(self, rule: str, m: int = 0, cap: int | None = None, f: float = 0.5):
        super().__init__("dss", "dss")
        self.rule, self.mm, self.capn, self.ff = rule, m, cap, f
        self.name = "simple:" + arm_name(rule, m=m) if rule == "S1" else "simple:" + rule

    def _target(self, t: int) -> int:
        c = self.cfg
        if self.rule in ("S1", "S4"):
            H = c.T - c.d - self.mm
            if t > H or H <= 0:
                return 0
            return min(c.B, math.floor(c.B * t / H + 1e-9))
        H = c.T - c.d
        if self.rule == "S3":
            half = H / 2.0
            n = (
                c.B * self.ff * t / half
                if t <= half
                else c.B * self.ff + c.B * (1.0 - self.ff) * (t - half) / half
            )
            return min(c.B, math.floor(n + 1e-9))
        return min(c.B, math.floor(c.B * t / H + 1e-9))  # S2 (and uniform pacing)

    def _query(self, t: int) -> bool:
        if self.burst_left > 0 and len(self.pending_events) < 2 and self.can_query(t):
            self.burst_left -= 1
            return True
        if not self.can_query(t):
            return False
        if self.rule in ("S2", "S4") and len(self.pending_events) >= self.capn:
            return False
        return self.used < self._target(t)


def make_arm(arm: str, cfg, sp):
    if arm in ("dss", "uniform", "episode_front"):
        return make_method(arm, cfg, sp)
    if arm == "pave":
        return GaverMethod("dss", "pave")
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


def specs():
    from run_atlas_cycle7_validation_v1 import specs as _s

    return _s()


def cell_obj(cid: str):
    if "_d100_" in cid:
        return dataclasses.replace(build_cell(cid.replace("_d100_", "_d50_")), d=100)
    return build_cell(cid)


def inventory(mask: np.ndarray, d: int, T: int):
    q = np.nonzero(mask)[0] + 1
    if len(q) == 0:
        return 0.0, float("nan")
    t = np.arange(1, T + 1)
    pend = np.searchsorted(q, t, side="left") - np.searchsorted(q + d, t, side="right")
    return float(pend.mean()), float(np.mean(T - (q + d)))


def task(job):
    stage, cid, seeds, arms = job
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


def all_simple_arms():
    return [arm_name(r, **{k: v}) for r, g in GRID.items() for k, v in g]


def jobs_for(stage):
    jobs = []
    if stage == "tune":
        arms = ["uniform"] + all_simple_arms()
        for g, cid in CELLS:
            if g == "ctl10":
                continue
            base = TUNE_BASE + 100 * CELL_INDEX[cid]
            jobs.append((stage, cid, list(range(base, base + N_TUNE)), arms))
        return jobs
    picks = json.loads((OUT / "picks.json").read_text())
    for g, cid in CELLS:
        base = EVAL_BASE + 100 * CELL_INDEX[cid]
        if g == "ctl10":
            arms = ["dss", "uniform", "episode_front"] + sorted(set(picks["d50"].values()))
        else:
            p = picks[g]
            arms = ["dss" if False else "uniform", "episode_front", "pave"] + list(p.values())
        for k in range(0, N_EVAL, CHUNK):
            jobs.append(
                (stage, cid, list(range(base + k, base + k + CHUNK)), list(dict.fromkeys(arms)))
            )
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
            print(f"  {i}/{len(jobs)} {time.time() - t0:.0f}s", flush=True)
    if stage == "tune":
        select_picks()


def load(stage):
    rows = [json.loads(x) for x in (OUT / f"rows_{stage}.jsonl").read_text().splitlines()]
    return rows


def cellmeans(rows):
    acc = {}
    for r in rows:
        acc.setdefault((r["cell"], r["arm"]), []).append(r["cost"])
    return {k: float(np.mean(v)) for k, v in acc.items()}


def select_picks():
    cm = cellmeans(load("tune"))
    picks, table = {}, {}
    for g in ("d50", "d100"):
        cids = [cid for gg, cid in CELLS if gg == g]
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
            picks[g][rule] = min(scored)[1]  # ties -> first in sort order (lexicographic arm name)
        # S4: best m with best cap, not separately tuned
        m = picks[g]["S1"].split("_m")[1]
        cap = picks[g]["S2"].split("_cap")[1]
        picks[g]["S4"] = f"S4_m{m}_cap{cap}"
        table[f"{g}:uniform"] = float(np.mean([cm[(c, "uniform")] for c in cids]))
    (OUT / "picks.json").write_text(json.dumps(picks, indent=1))
    (OUT / "tuning_table.json").write_text(json.dumps(table, indent=1))
    print(json.dumps(picks, indent=1))


def boot_rel(a, b, ref, n=4000, seed=7):
    """a, b, ref: dict cell -> per-seed arrays (aligned). Return rel diff of mean(a-b)/mean(ref)
    pooled with equal cell weights; percentile CI from resampling seeds within cells."""
    rng = np.random.default_rng(seed)
    cells = list(a)
    idx = {c: rng.integers(0, len(a[c]), size=(n, len(a[c]))) for c in cells}
    d = np.zeros(n)
    r = np.zeros(n)
    for c in cells:
        d += (a[c][idx[c]] - b[c][idx[c]]).mean(1)
        r += ref[c][idx[c]].mean(1)
    rel = d / r  # ratio of cell sums == ratio of equal-weight means
    pt = sum((a[c] - b[c]).mean() for c in cells) / sum(ref[c].mean() for c in cells)
    return 100 * pt, 100 * np.quantile(rel, 0.025), 100 * np.quantile(rel, 0.975)


def analyse():
    picks = json.loads((OUT / "picks.json").read_text())
    rows = load("eval")
    per = {}
    for r in rows:
        per.setdefault((r["cell"], r["arm"]), {})[r["seed"]] = r

    def arr(cid, arm, key="cost"):
        d = per[(cid, arm)]
        return np.array([d[s][key] for s in sorted(d)])

    out = {"cells": {}, "pooled": {}, "picks": picks}
    groups = {
        "d50": [c for g, c in CELLS if g == "d50"],
        "d100": [c for g, c in CELLS if g == "d100"],
    }
    groups["gate_on_all18"] = groups["d50"] + groups["d100"]
    # per-cell table
    for g, cid in CELLS:
        arms = sorted({a for (c, a) in per if c == cid})
        out["cells"][cid] = {
            a: {
                "n": len(per[(cid, a)]),
                "cost": float(arr(cid, a).mean()),
                "queries": float(arr(cid, a, "queries").mean()),
                "arrive_before_T": float(np.nanmean(arr(cid, a, "arrive_before_T"))),
                "pending_mean": float(arr(cid, a, "pending_mean").mean()),
            }
            for a in arms
        }
    for gname, cids in groups.items():
        gd = "d100" if gname == "d100" else "d50"
        sets = {"d50": picks["d50"], "d100": picks["d100"]}

        def armof(rule, c):
            return sets["d100" if "_d100_" in c else "d50"][rule]

        res = {}

        def stack(armfun):
            return {c: arr(c, armfun(c)) for c in cids}

        ref = stack(lambda c: "uniform")
        armsets = {
            "uniform": lambda c: "uniform",
            "episode_front": lambda c: "episode_front",
            "pave": lambda c: "pave",
        }
        for rule in ("S1", "S2", "S3", "S4"):
            armsets[rule] = (lambda rr: lambda c: armof(rr, c))(rule)
        means = {}
        for k, f in armsets.items():
            s = stack(f)
            means[k] = float(np.mean([s[c].mean() for c in cids]))
            ex = {
                key: float(np.mean([np.nanmean(arr(c, f(c), key)) for c in cids]))
                for key in ("queries", "arrive_before_T", "pending_mean")
            }
            res[k] = {"mean_JT": means[k], **ex}
        best = min(("S1", "S2", "S3", "S4"), key=lambda k: means[k])
        best_s = stack(armsets[best])
        pave_s = stack(armsets["pave"])
        uni_s = ref
        res["best_simple"] = best
        res["pave_minus_best_simple_pct_of_uniform"] = boot_rel(pave_s, best_s, ref)
        res["best_simple_minus_uniform_pct_of_uniform"] = boot_rel(best_s, uni_s, ref)
        res["pave_minus_uniform_pct_of_uniform"] = boot_rel(pave_s, uni_s, ref)
        for k in ("S1", "S2", "S3", "S4"):
            res[f"{k}_minus_uniform_pct"] = boot_rel(stack(armsets[k]), uni_s, ref)
            res[f"pave_minus_{k}_pct"] = boot_rel(pave_s, stack(armsets[k]), ref)
        res["pave_minus_episode_front_pct"] = boot_rel(pave_s, stack(armsets["episode_front"]), ref)
        out["pooled"][gname] = res
    # control cells (report only)
    ctl = [c for g, c in CELLS if g == "ctl10"]
    cres = {}
    for a in sorted({a for (c, a) in per if c in ctl}):
        cres[a] = float(np.mean([arr(c, a).mean() for c in ctl]))
    out["control_pooled_JT"] = cres
    ref = {c: arr(c, "dss") for c in ctl}
    out["control_vs_dss_pct"] = {
        a: boot_rel({c: arr(c, a) for c in ctl}, ref, ref) for a in cres if a != "dss"
    }
    (OUT / "analysis.json").write_text(json.dumps(out, indent=1))
    print(
        json.dumps(
            {k: out[k] for k in ("pooled", "control_pooled_JT", "control_vs_dss_pct")}, indent=1
        )
    )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "eval", "analyse", "smoke"])
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    assert a.workers <= 6
    if a.stage == "analyse":
        analyse()
    elif a.stage == "smoke":
        cid = GATE_ON_50[4]
        arms = [
            "uniform",
            "pave",
            "S1_m0",
            "S1_m50",
            "S2_cap2",
            "S3_f0.5",
            "S3_f0.8",
            "S4_m25_cap3",
        ]
        t0 = time.time()
        rows = task(("smoke", cid, list(range(TUNE_BASE + 9900, TUNE_BASE + 9903)), arms))
        cm = cellmeans(rows)
        for a_ in arms:
            rr = [r for r in rows if r["arm"] == a_]
            print(
                a_,
                round(cm[(cid, a_)], 4),
                np.mean([r["queries"] for r in rr]),
                round(np.mean([r["pending_mean"] for r in rr]), 2),
            )
        print(f"{time.time() - t0:.1f}s")
    else:
        run_stage(a.stage, a.workers)
