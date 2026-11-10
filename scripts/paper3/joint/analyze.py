"""Summaries from dev_eval / dev_ablate / dev_matched checkpoints -> JSON + markdown tables."""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import OUT, log
from dev_eval import BASE, MINE, load_rows

from shiftlab.paper3.joint import harness as H

rids, sl = H.regime_ids(), H.seeds(H.EVAL_SEEDS)
NULL = ["stationary_null", "dep_null_rho_0.95"]
HARM = ["stationary_worse"]


def arr(rows, names, key):
    return H.to_array(rows, len(names), rids, sl, key)


def load(tag):
    first = json.loads((OUT / tag / f"{rids[0]}.json").read_text())
    names = first["names"]
    return names, load_rows(tag, rids)


def strongest_baseline(names):
    best, bs = None, 9e9
    for m in BASE:
        p = OUT / "tuning" / f"{m}.json"
        if m in names and p.exists():
            sc = json.loads(p.read_text())["best_spec"] and json.loads(p.read_text())
            s = sc["scores"][sc["best"]]
            if s < bs:
                best, bs = m, s
    return best


def fmt(r):
    return f"{r['delta']:+.2f} [{r['lo']:+.2f},{r['hi']:+.2f}] ({r['rel_pct']:+.1f}%)"


def main():
    names, rows = load("dev_eval")
    J = arr(rows, names, "J")
    NQ, NS = arr(rows, names, "n_queries"), arr(rows, names, "n_switches")
    FP = arr(rows, names, "global_null_false_promotion")
    arr(rows, names, "global_null")
    FPA = arr(rows, names, "false_promotions")
    REG = arr(rows, names, "J_hindsight_oracle_UNATTAINABLE")
    ref = strongest_baseline(names)
    i_ref = names.index(ref)
    out = {
        "strongest_baseline_by_tuning": ref,
        "methods": names,
        "pooled_J": {},
        "vs_ref": {},
        "vs_each": {},
    }
    log(f"strongest tuned deployable baseline (by tuning score): {ref}")
    log(
        f"{'method':14s} {'pooled J':>9s} {'vs ref (dJ, CI, rel)':>38s} {'labels':>7s} {'sw':>5s} {'nullFP':>7s} {'regret*':>8s}"
    )
    for i, m in enumerate(names):
        r = H.paired_delta(J[i], J[i_ref], seed=1)
        nullfp = float(FP[i][[rids.index(x) for x in NULL]].mean())
        out["pooled_J"][m] = float(J[i].mean())
        out["vs_ref"][m] = r
        out.setdefault("secondary", {})[m] = {
            "labels": float(NQ[i].mean()),
            "switches": float(NS[i].mean()),
            "null_false_promotion": nullfp,
            "null_fp_by_regime": {
                x: float(FP[i][rids.index(x)].mean()) for x in NULL + HARM if x in rids
            },
            "false_promotions_all": float(FPA[i].mean()),
            "regret_hindsight_UNATTAINABLE": float((J[i] - REG[i]).mean()),
        }
        log(
            f"{m:14s} {J[i].mean():9.3f} {fmt(r):>38s} {NQ[i].mean():7.1f} {NS[i].mean():5.2f} {nullfp:7.3f} {(J[i] - REG[i]).mean():8.2f}"
        )
    # each A method against each baseline (pooled only)
    for m in MINE:
        if m not in names:
            continue
        out["vs_each"][m] = {
            b: H.paired_delta(J[names.index(m)], J[names.index(b)], 1000, seed=2)
            for b in ["never"] + BASE
            if b in names
        }
    # per-regime for the best A method vs ref
    mine = [m for m in MINE if m in names]
    best_m = min(mine, key=lambda m: out["pooled_J"][m]) if mine else None
    out["best_A"] = best_m
    for m in mine:
        r = out["vs_ref"][m]
        log(f"\nper-regime {m} vs {ref}  (dJ, rel%) *=CI excludes 0")
        row = []
        for j, rid in enumerate(rids):
            d, lo, hi, rel = r["per_regime"][j]
            row.append(f"{rid}:{d:+.2f}({rel:+.0f}%){'*' if lo > 0 or hi < 0 else ''}")
        log("  " + " | ".join(row))
    H.dump(OUT / "dev_summary.json", out)
    # ablations
    p = OUT / "dev_ablate"
    if (p / f"{rids[-1]}.json").exists():
        an, ar = load("dev_ablate")
        JA = arr(ar, an, "J")
        NA = arr(ar, an, "n_queries")
        res = {}
        for par, kids in (
            ("A1", [n for n in an if n.startswith("A1_")]),
            ("A3", [n for n in an if n.startswith("A3_")]),
        ):
            log(f"\nablations vs parent {par} (dJ = ablated - parent; positive = ablation worse)")
            for kid in kids:
                r = H.paired_delta(JA[an.index(kid)], JA[an.index(par)], seed=3)
                res[kid] = dict(
                    r,
                    labels=float(NA[an.index(kid)].mean()),
                    parent_labels=float(NA[an.index(par)].mean()),
                )
                log(
                    f"  {kid:20s} {fmt(r)} labels {NA[an.index(kid)].mean():.1f} (parent {NA[an.index(par)].mean():.1f})"
                )
        H.dump(OUT / "dev_ablate_summary.json", res)
    # matched labels
    for d in sorted(OUT.glob("dev_matched_*_vs_*")):
        if not (d / f"{rids[-1]}.json").exists():
            continue
        _, mr = load(d.name)
        JM = H.to_array(mr, 1, rids, sl, "J")[0]
        refm = d.name.split("_")[2]
        r = H.paired_delta(J[names.index(refm)], JM, seed=4)
        log(
            f"\nmatched labels: {refm} vs {d.name.split('_vs_')[1]} with B=mean queries of {refm}: {fmt(r)}"
        )
        H.dump(OUT / f"{d.name}_summary.json", r)


if __name__ == "__main__":
    main()
