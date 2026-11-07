"""Failure Atlas v1, Amendment 5 items 1-2: straddle mechanism map and H-TK2 (development; not confirmatory).

Protocol: docs/failure_atlas_v1_protocol.md, Amendment 5 (predictions locked there). Seeds: development
range, first ``--n-seeds`` seeds ([100000, 100040) by default). Resumable: one jsonl line per task in
``<out>/checkpoint.jsonl``.

    .venv/Scripts/python scripts/run_atlas_cycle4_map_v1.py
    .venv/Scripts/python scripts/run_atlas_cycle4_map_v1.py --T 100 --n-seeds 3 --n-f1 6 --n-f2 4 --out <dir>
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import paired_ci, run

SOURCES = (
    "src/shiftlab/dive/failure_atlas.py",
    "src/shiftlab/dive/atlas_components.py",
    "src/shiftlab/dive/switching_explore.py",
    "scripts/run_atlas_cycle4_map_v1.py",
)
STRADDLE_ID = "b1a17927d9ad"
KELLY_ID = "8ac25a41d4a8"
AXES_SEARCHED = ["onset", "duration", "s", "d", "budget_frac", "effect", "rate", "unknown"]
SAMPLE_SEED = 4040
HARM_THRESHOLD = -0.01


def find_spec(spec_id: str):
    for ax in AXES_SEARCHED:
        for sp in comp.propose_candidates(ax, max_n=60):
            if sp.spec_id == spec_id:
                return sp
    raise LookupError(f"spec {spec_id} not found")


def first_promo(r) -> int:
    a = np.asarray(r.actions)
    prev = np.concatenate(([0], a[:-1]))
    idx = np.flatnonzero((a == 1) & (prev == 0))
    return int(idx[0]) + 1 if len(idx) else -1


def task(args: tuple) -> dict:
    """One cell (or null twin) x all seeds: candidate and ablation, paired by seed."""
    key, cell, seed_list, cand, abl = args
    out = {
        k: []
        for k in ("cost_c", "cost_a", "prom_c", "prom_a", "first_c", "first_a", "fp_c", "fp_a")
    }
    for sd in seed_list:
        stream = fa.make_stream(cell, sd)
        cfg = cell.config(sd)
        rc = run(stream, comp.build_candidate(cand), cfg)
        ra = run(stream, comp.build_candidate(abl), cfg)
        out["cost_c"].append(rc.cost / cell.T)
        out["cost_a"].append(ra.cost / cell.T)
        out["prom_c"].append(rc.promotions)
        out["prom_a"].append(ra.promotions)
        out["first_c"].append(first_promo(rc))
        out["first_a"].append(first_promo(ra))
        out["fp_c"].append(int((rc.fp_regime or 0) > 0))
        out["fp_a"].append(int((ra.fp_regime or 0) > 0))
    return {"key": key, **out}


def git_info() -> dict:
    def g(*a):
        return subprocess.run(
            ["git", *a], check=False, cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()

    return {
        "head": g("rev-parse", "HEAD"),
        "dirty": bool(g("status", "--porcelain")),
        "src_sha256": {
            Path(f).name: hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
            for f in SOURCES
            if (ROOT / f).exists()
        },
    }


def ci(x) -> list[float]:
    m, lo, hi = paired_ci(np.asarray(x, dtype=float))
    return [m, lo, hi]


def welch(a, b, level: float = 0.95) -> list[float]:
    """Mean(a)-mean(b) with Welch interval (independent cell samples)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return [float(a.mean() - b.mean()), float("nan"), float("nan")]
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = math.sqrt(va + vb)
    dfree = (
        (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1))
        if se > 0
        else len(a) + len(b) - 2
    )
    h = float(stats.t.ppf(0.5 + level / 2, dfree)) * se
    m = float(a.mean() - b.mean())
    return [m, m - h, m + h]


def fmt(c) -> str:
    return f"{c[0]:+.4f} [{c[1]:+.4f}, {c[2]:+.4f}]"


def P(b) -> str:
    return "PASS" if b else "FAIL"


def _sortkey(k: str):
    try:
        return (0, float(k), "")
    except ValueError:
        return (1, 0.0, k)


def axis_levels(cell) -> dict:
    return {ax: getattr(cell, ax) for ax in cell.axes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--T", type=int, default=fa.T_DEFAULT)
    ap.add_argument("--n-seeds", type=int, default=40)
    ap.add_argument("--n-f1", type=int, default=400)
    ap.add_argument("--n-f2", type=int, default=200)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default=str(ROOT / "outputs" / "failure_atlas_v1_cycle4_map"))
    a = ap.parse_args()
    workers = min(a.workers, 6)
    t0 = time.time()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt = out_dir / "checkpoint.jsonl"
    logf = open(out_dir / "run.log", "a", encoding="utf-8")  # noqa: SIM115 - Shared run-scoped log handle.

    def log(msg: str) -> None:
        line = f"[{time.time() - t0:7.0f}s] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    sd = fa.seeds("development", a.n_seeds)
    assert sd[0] == 100000 and sd[-1] < 200000

    straddle, kelly = find_spec(STRADDLE_ID), find_spec(KELLY_ID)
    st_abl = comp.ablation_of(straddle, straddle.focus)
    ke_abl = comp.ablation_of(kelly, "evidence")
    for sp in (st_abl, ke_abl):
        ok, why = comp.validate_spec(sp)
        assert ok, why

    # cell samples (fixed rng 4040; family 2 drawn the same way)
    c1_all, c2_all = fa.all_cells(a.T), fa.all_cells2(a.T)
    rng1 = np.random.default_rng(SAMPLE_SEED)
    f1 = [
        c1_all[i]
        for i in sorted(rng1.choice(len(c1_all), size=min(a.n_f1, len(c1_all)), replace=False))
    ]
    rng2 = np.random.default_rng(SAMPLE_SEED)
    f2 = [
        c2_all[i]
        for i in sorted(rng2.choice(len(c2_all), size=min(a.n_f2, len(c2_all)), replace=False))
    ]
    # H-TK2 cells
    tk = [
        fa.CellSpec(on, L, "strong", "neutral", d, b, 0.1, T=a.T)
        for on in fa.ONSETS
        for L in (0.6, 1.0)
        for d in (1, 10)
        for b in (0.05, 0.1)
    ]
    assert len(tk) == 32

    jobs: dict[str, tuple] = {}
    for fam, cells in ((1, f1), (2, f2)):
        for c in cells:
            jobs[f"S|{c.cell_id}"] = (c, straddle, st_abl)
            tw = c.null_twin()
            jobs.setdefault(f"SN|{tw.cell_id}", (tw, straddle, st_abl))
    for c in tk:
        jobs[f"K|{c.cell_id}"] = (c, kelly, ke_abl)

    done: dict[str, dict] = {}
    if ckpt.exists():
        for line in ckpt.read_text("utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("n_seeds") == len(sd) and r.get("seed0") == sd[0]:
                    done[r["key"]] = r
    todo = [k for k in jobs if k not in done]
    log(
        f"jobs={len(jobs)} done={len(done)} todo={len(todo)} workers={workers} T={a.T} n_seeds={len(sd)}"
    )
    if todo:
        with (
            ProcessPoolExecutor(max_workers=workers) as pool,
            open(ckpt, "a", encoding="utf-8") as cf,
        ):
            futs = {}
            for k in todo:
                c, cand, abl = jobs[k]
                futs[pool.submit(task, (k, c, tuple(sd), cand, abl))] = k
            for n, f in enumerate(as_completed(futs), 1):
                r = f.result()
                r["n_seeds"], r["seed0"] = len(sd), sd[0]
                cf.write(json.dumps(r) + "\n")
                cf.flush()
                done[r["key"]] = r
                if n % 20 == 0 or n == len(todo):
                    log(f"{n}/{len(todo)} tasks")

    # ------------------------------------------------------------ analysis
    def gain(k):
        r = done[k]
        return np.asarray(r["cost_a"]) - np.asarray(r["cost_c"])

    fam_res = {}
    for fam, cells in ((1, f1), (2, f2)):
        rows = []
        for c in cells:
            g = gain(f"S|{c.cell_id}")
            cg = ci(g)
            tw = done[f"SN|{c.null_twin().cell_id}"]
            rows.append(
                {
                    "cell": c.cell_id,
                    "levels": axis_levels(c),
                    "gain": cg,
                    "harm": bool(cg[2] < HARM_THRESHOLD),
                    "null_fp_c": float(np.mean(tw["fp_c"])),
                    "null_fp_a": float(np.mean(tw["fp_a"])),
                }
            )
        by_level = {}
        for ax in cells[0].axes:
            lv = defaultdict(list)
            hv = defaultdict(int)
            for r in rows:
                lv[str(r["levels"][ax])].append(r["gain"][0])
                hv[str(r["levels"][ax])] += int(r["harm"])
            by_level[ax] = {
                k: {"n": len(v), "mean_gain": ci(v), "n_harm": hv[k]}
                for k, v in sorted(lv.items(), key=lambda kv: _sortkey(kv[0]))
            }
        pooled = {
            "candidate": float(np.mean([r["null_fp_c"] for r in rows])),
            "ablation": float(np.mean([r["null_fp_a"] for r in rows])),
        }
        fam_res[fam] = {
            "n_cells": len(rows),
            "overall_mean_gain": ci([r["gain"][0] for r in rows]),
            "by_level": by_level,
            "null_fp_pooled": pooled,
            "n_harm_cells": sum(r["harm"] for r in rows),
            "harm_cells": [r["cell"] for r in rows if r["harm"]],
            "cells": rows,
        }

    # P1
    r1 = fam_res[1]["cells"]
    gd = {d: [r["gain"][0] for r in r1 if r["levels"]["d"] == d] for d in fa.DELAYS}
    d1_d50 = welch(gd[1], gd[50]) if gd[1] and gd[50] else [float("nan")] * 3
    p1 = {
        "gain_by_d": {
            str(d): ci(v) if len(v) > 1 else [float(np.mean(v)) if v else float("nan")] * 3
            for d, v in gd.items()
        },
        "n_cells_by_d": {str(d): len(v) for d, v in gd.items()},
        "d1_minus_d50_welch_by_cell": d1_d50,
        "pass": bool(d1_d50[0] > 0 and d1_d50[1] > 0),
    }
    # matched-pair secondary: d=1 and d=50 cells identical on all other axes, both in the sample
    key_of = lambda r: tuple((k, v) for k, v in sorted(r["levels"].items()) if k != "d")
    g1 = {key_of(r): r["gain"][0] for r in r1 if r["levels"]["d"] == 1}
    g50 = {key_of(r): r["gain"][0] for r in r1 if r["levels"]["d"] == 50}
    pairs = [g1[k] - g50[k] for k in g1 if k in g50]
    p1["matched_pairs_n"] = len(pairs)
    p1["matched_pairs_diff"] = ci(pairs) if len(pairs) > 1 else None

    # P2
    alpha = f1[0].alpha
    allc = fam_res[1]["cells"] + fam_res[2]["cells"]
    p2 = {
        "alpha": alpha,
        "straddle_pooled_all": float(np.mean([r["null_fp_c"] for r in allc])),
        "ablation_pooled_all": float(np.mean([r["null_fp_a"] for r in allc])),
        "straddle_family1": fam_res[1]["null_fp_pooled"]["candidate"],
        "straddle_family2": fam_res[2]["null_fp_pooled"]["candidate"],
        "ablation_family1": fam_res[1]["null_fp_pooled"]["ablation"],
        "ablation_family2": fam_res[2]["null_fp_pooled"]["ablation"],
    }
    p2["pass"] = bool(p2["straddle_pooled_all"] <= alpha)

    # P3
    p3 = {
        f"family{f}": {
            "n_harm_cells": fam_res[f]["n_harm_cells"],
            "n_cells": fam_res[f]["n_cells"],
            "by_level": {
                ax: {k: f"{v['n_harm']}/{v['n']}" for k, v in lv.items()}
                for ax, lv in fam_res[f]["by_level"].items()
            },
            "harm_cells": fam_res[f]["harm_cells"],
        }
        for f in (1, 2)
    }

    # H-TK2
    def tk_stats(tag):
        by_on = {}
        for on in fa.ONSETS:
            ks = [f"K|{c.cell_id}" for c in tk if c.onset == on]
            seedgain = np.mean([gain(k) for k in ks], axis=0)  # per-seed mean over the 8 cells
            by_on[str(on)] = {
                "gain": ci(seedgain),
                "seedgain": seedgain,
                "first_c": float(
                    np.mean(
                        [np.mean([x for x in done[k]["first_c"] if x > 0] or [np.nan]) for k in ks]
                    )
                ),
                "first_a": float(
                    np.mean(
                        [np.mean([x for x in done[k]["first_a"] if x > 0] or [np.nan]) for k in ks]
                    )
                ),
                "frac_promoted_c": float(
                    np.mean([np.mean(np.asarray(done[k]["first_c"]) > 0) for k in ks])
                ),
                "frac_promoted_a": float(
                    np.mean([np.mean(np.asarray(done[k]["first_a"]) > 0) for k in ks])
                ),
                "promotions_c": float(np.mean([np.mean(done[k]["prom_c"]) for k in ks])),
                "promotions_a": float(np.mean([np.mean(done[k]["prom_a"]) for k in ks])),
            }
        return by_on

    tkr = tk_stats("K")
    dpool = tkr["0.1"]["seedgain"] - tkr["0.8"]["seedgain"]
    pair8 = []
    for c in tk:
        if c.onset == 0.1:
            m = next(
                x
                for x in tk
                if x.onset == 0.8
                and (x.duration, x.d, x.budget_frac) == (c.duration, c.d, c.budget_frac)
            )
            pair8.append(float(gain(f"K|{c.cell_id}").mean() - gain(f"K|{m.cell_id}").mean()))
    htk = {
        "by_onset": {
            k: {kk: vv for kk, vv in v.items() if kk != "seedgain"} for k, v in tkr.items()
        },
        "onset0.1_minus_onset0.8_per_seed_pooled": ci(dpool),
        "onset0.1_minus_onset0.8_matched_8_cells": ci(pair8),
        "pass": bool(ci(dpool)[0] > 0 and ci(dpool)[1] > 0),
        "first_promotion_note": "mean first-promotion round among runs that promoted (-1 runs excluded); frac_promoted = share of runs with any promotion",
    }

    g = git_info()
    results = {
        "protocol": "docs/failure_atlas_v1_protocol.md Amendment 5 items 1-2",
        "git": g,
        "T": a.T,
        "seeds": [sd[0], sd[-1] + 1],
        "n_seeds": len(sd),
        "sample_seed": SAMPLE_SEED,
        "specs": {
            "straddle": STRADDLE_ID,
            "straddle_ablation": st_abl.spec_id,
            "straddle_ablation_slot": straddle.focus,
            "kelly": KELLY_ID,
            "kelly_ablation": ke_abl.spec_id,
        },
        "P1": p1,
        "P2": p2,
        "P3": p3,
        "family": {str(f): {k: v for k, v in fam_res[f].items()} for f in (1, 2)},
        "H_TK2": htk,
        "elapsed_s": time.time() - t0,
        "evidence_status": "development-grade, descriptive; not confirmatory",
    }
    (out_dir / "results.json").write_text(json.dumps(results, indent=1, default=float), "utf-8")

    # ------------------------------------------------------------ summary
    L = [
        "# Failure Atlas v1 Amendment 5 items 1-2: straddle map and H-TK2 (development; NOT confirmatory)",
        "",
    ]
    L.append(
        f"git head `{g['head'][:10]}` dirty={g['dirty']}; seeds [{sd[0]}, {sd[-1] + 1}) n={len(sd)}; T={a.T}; "
        f"cells: {len(f1)} family-1 + {len(f2)} family-2 (rng seed {SAMPLE_SEED}); sources: "
        + ", ".join(f"{k} `{v[:10]}`" for k, v in g["src_sha256"].items())
    )
    L += [
        "",
        (
            f"Straddle `{STRADDLE_ID}`; ablation `{st_abl.spec_id}` (slot `{straddle.focus}`). "
            f"triggered_kelly `{KELLY_ID}`; ablation `{ke_abl.spec_id}` (slot `evidence`). Gain = ablation cost - candidate cost per round (positive = candidate better)."
        ),
        "",
    ]
    L += ["## Verdicts", ""]
    L.append(
        f"- P1 (family 1, gain(d=1) > gain(d=50), CI excludes 0): **{P(p1['pass'])}** ({fmt(p1['d1_minus_d50_welch_by_cell'])})"
    )
    L.append(
        f"- P2 (pooled null FP <= alpha={alpha}): **{P(p2['pass'])}** (straddle {p2['straddle_pooled_all']:.4f}, "
        f"ablation {p2['ablation_pooled_all']:.4f})"
    )
    L.append(
        f"- P3 (descriptive): harm cells family 1 {fam_res[1]['n_harm_cells']}/{len(f1)}, family 2 {fam_res[2]['n_harm_cells']}/{len(f2)}"
    )
    L.append(
        f"- H-TK2: **{P(htk['pass'])}** (onset0.1 - onset0.8 = {fmt(htk['onset0.1_minus_onset0.8_per_seed_pooled'])})"
    )
    L += [
        "",
        "## P1: family-1 mean gain by d (CI across cells)",
        "",
        "| d | n cells | mean gain [95% CI] |",
        "|---|---|---|",
    ]
    for d, v in p1["gain_by_d"].items():
        L.append(f"| {d} | {p1['n_cells_by_d'][d]} | {fmt(v)} |")
    L.append(
        f"\nd=1 minus d=50, Welch across cells (primary): {fmt(p1['d1_minus_d50_welch_by_cell'])} -> {P(p1['pass'])}"
    )
    if p1["matched_pairs_diff"]:
        L.append(
            f"\nSecondary: exact matched pairs (same other-axis levels, both sampled) n={p1['matched_pairs_n']}: {fmt(p1['matched_pairs_diff'])}"
        )
    else:
        L.append(
            f"\nSecondary: exact matched d=1/d=50 pairs in the sample: n={p1['matched_pairs_n']} (too few for a CI)"
        )
    L += [
        "",
        "## P2: pooled null-twin false-promotion rate",
        "",
        "| | family 1 | family 2 | all |",
        "|---|---|---|---|",
    ]
    L.append(
        f"| straddle | {p2['straddle_family1']:.4f} | {p2['straddle_family2']:.4f} | {p2['straddle_pooled_all']:.4f} |"
    )
    L.append(
        f"| ablation | {p2['ablation_family1']:.4f} | {p2['ablation_family2']:.4f} | {p2['ablation_pooled_all']:.4f} |"
    )
    L.append(
        f"\nalpha = {alpha}. Pooled = mean over sampled cells' twins (twin repeated per cell) and seeds."
    )
    L += [
        "",
        "## P3: harm region (gain CI upper bound < -0.01), harm cells / cells by axis level",
        "",
    ]
    for f in (1, 2):
        L.append(
            f"Family {f}: {p3[f'family{f}']['n_harm_cells']}/{p3[f'family{f}']['n_cells']} cells"
        )
        L.append("")
        L += ["| axis | level: harm/n |", "|---|---|"]
        for ax, lv in p3[f"family{f}"]["by_level"].items():
            L.append(f"| {ax} | " + "; ".join(f"{k}: {v}" for k, v in lv.items()) + " |")
        L.append("")
    for f in (1, 2):
        L += [
            f"## Mean gain by axis level, family {f} (overall {fmt(fam_res[f]['overall_mean_gain'])}; CI across cells)",
            "",
        ]
        L += [
            "| axis | level | n cells | mean gain [95% CI] | harm cells |",
            "|---|---|---|---|---|",
        ]
        for ax, lv in fam_res[f]["by_level"].items():
            for k, v in lv.items():
                cc = v["mean_gain"] if v["n"] > 1 else [v["mean_gain"][0]] * 3
                L.append(f"| {ax} | {k} | {v['n']} | {fmt(cc)} | {v['n_harm']} |")
        L.append("")
    L += [
        "## H-TK2: triggered_kelly neutral-off gain by onset (strong, s=0.1; L {0.6,1} x d {1,10} x B {0.05,0.1}; 8 cells per onset)",
        "",
    ]
    L += [
        "| onset | gain [95% CI, per-seed mean of 8 cells] | first promo cand | first promo abl | frac runs promoted cand | abl | promotions/run cand | abl |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for k, v in htk["by_onset"].items():
        L.append(
            f"| {k} | {fmt(v['gain'])} | {v['first_c']:.1f} | {v['first_a']:.1f} | {v['frac_promoted_c']:.3f} | "
            f"{v['frac_promoted_a']:.3f} | {v['promotions_c']:.3f} | {v['promotions_a']:.3f} |"
        )
    L.append(
        f"\nonset 0.1 - onset 0.8 (per-seed pooled over 8 cells): {fmt(htk['onset0.1_minus_onset0.8_per_seed_pooled'])} -> {P(htk['pass'])}"
    )
    L.append(
        f"\nSecondary, matched 8 cell pairs: {fmt(htk['onset0.1_minus_onset0.8_matched_8_cells'])}"
    )
    L += [
        "",
        "## Notes and choices",
        "",
        "- P1 contrast: cells are a random sample, so d=1 and d=50 cells are generally not matched; the primary CI is Welch across cell-level mean gains. Exact matched pairs are reported when any exist.",
        "- Per-cell gain CI is paired-t over seeds; level means and their CIs are across cells (each cell's seed-mean gain).",
        "- Null twins are canonicalised (family 1: first onset/duration; family 2: first rate), so many cells share a twin; the pooled FP weights each sampled cell once.",
        "- H-TK2 difference uses per-seed means over the 8 cells at each onset (streams differ across cells, so seeds are independent draws); the matched-cell version is secondary.",
        "- First-promotion time excludes runs with no promotion; see frac promoted.",
        "- Family-2 adapter = same CandidateSpec through build_candidate on family-2 streams.",
        f"- Elapsed {results['elapsed_s']:.0f}s.",
    ]
    (out_dir / "summary.md").write_text("\n".join(L) + "\n", "utf-8")
    log("done")
    print("\n".join(L[:12]))


if __name__ == "__main__":
    main()
