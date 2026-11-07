"""Failure Atlas v1, Amendment 4 mechanism-validation checks (development evidence; not confirmatory).

Protocol: docs/failure_atlas_v1_protocol.md, Amendment 4 (criteria locked there). Seeds: mechanism
range [280000, 280200) only. Reuses the evaluation, reference and classification definitions of
``scripts/run_failure_atlas_loop.py`` (stage 6) without modifying them.

    .venv/Scripts/python scripts/run_atlas_mechanism_check_v1.py            # full (T=1000, 200 seeds)
    .venv/Scripts/python scripts/run_atlas_mechanism_check_v1.py --T 120 --n-seeds 6 --out <dir>   # smoke
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import paired_ci

SOURCES = (
    "src/shiftlab/dive/failure_atlas.py",
    "src/shiftlab/dive/atlas_components.py",
    "src/shiftlab/dive/atlas_r6_baselines.py",
    "src/shiftlab/dive/switching_explore.py",
    "src/shiftlab/dive/eprocess.py",
    "scripts/run_failure_atlas_loop.py",
    "scripts/run_atlas_mechanism_check_v1.py",
)
STRADDLE_ID = "b1a17927d9ad"
KELLY_ID = "8ac25a41d4a8"
REPAIR_CELL = "on0.6_L0.6_strong_harmful_d1_b0.05_s0.1"
NEIGHBOURS = (
    "on0.3_L0.6_strong_harmful_d1_b0.05_s0.1",
    "on0.8_L0.6_strong_harmful_d1_b0.05_s0.1",
)
KELLY_CELLS = (  # cycle-3 family-1 survivors (harmful off state)
    "on0.3_L0.6_strong_harmful_d10_b0.05_s0.1",
    "on0.6_L0.6_strong_harmful_d1_b0.05_s0.1",
    "on0.6_L1_strong_harmful_d50_b0.05_s0.1",
    "on0.1_L0.6_strong_harmful_d1_b0.05_s0.1",
    "on0.1_L0.6_strong_harmful_d10_b0.05_s0.5",
)
AXES_SEARCHED = ["onset", "duration", "s", "d", "budget_frac", "effect", "rate", "unknown"]
CHUNK = 10


def find_spec(spec_id: str):
    for ax in AXES_SEARCHED:
        for sp in comp.propose_candidates(ax, max_n=60):
            if sp.spec_id == spec_id:
                return sp
    raise LookupError(f"spec {spec_id} not found")


def task(args: tuple) -> dict:
    """One (cell, seed chunk): optional baselines/refs plus named candidate specs."""
    cell, seed_list, kappa, specs, baselines, with_null = args
    extra = {n: (lambda s=s: comp.build_candidate(s)) for n, s in specs.items()}
    kw = {} if baselines else {"methods": (), "refs": ()}
    return fa.evaluate_cell(
        cell, seed_list, kappa=kappa, with_null=with_null, extra_methods=extra, **kw
    )


def merge(parts: list[dict]) -> dict:
    out = {"methods": {}, "null": None}
    for p in parts:
        for m, rec in p["methods"].items():
            d = out["methods"].setdefault(m, {"cost": [], "fp": []})
            d["cost"] += list(rec["cost"])
            d["fp"] += list(rec["fp"])
        if p.get("null"):
            if out["null"] is None:
                out["null"] = {"methods": {}}
            for m, rec in p["null"]["methods"].items():
                d = out["null"]["methods"].setdefault(m, {"cost": [], "fp": []})
                d["cost"] += list(rec["cost"])
                d["fp"] += list(rec["fp"])
    return out


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


def fmt(c) -> str:
    return f"{c[0]:+.4f} [{c[1]:+.4f}, {c[2]:+.4f}]"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--T", type=int, default=fa.T_DEFAULT)
    ap.add_argument("--n-seeds", type=int, default=200)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=str(ROOT / "outputs" / "failure_atlas_v1_mechcheck"))
    ap.add_argument("--kappa", type=float, default=None)
    a = ap.parse_args()
    workers = min(a.workers, 12)
    t0 = time.time()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    sd = fa.seeds("mechanism", a.n_seeds, offset=80000)
    assert sd[0] == 280000 and (a.n_seeds != 200 or sd[-1] == 280199)
    kappa = a.kappa
    if kappa is None:
        st = json.loads(
            (ROOT / "outputs/failure_atlas_v1_cycle3/family1/state.json").read_text("utf-8")
        )
        kappa = float(st["kappa"])
    by_id = {c.cell_id.replace(f"_T{a.T}", ""): c for c in fa.all_cells(a.T)}

    straddle, kelly = find_spec(STRADDLE_ID), find_spec(KELLY_ID)
    st_abl = comp.ablation_of(straddle, straddle.focus)
    ke_abl = comp.ablation_of(kelly, "evidence")
    for sp in (st_abl, ke_abl):
        ok, why = comp.validate_spec(sp)
        assert ok, why
    sp_straddle = {"cand": straddle, "abl": st_abl}
    sp_kelly = {"cand": kelly, "abl": ke_abl}

    repair = by_id[REPAIR_CELL]
    jobs = {"repair": (repair, sp_straddle, True, True)}
    for i, n in enumerate(NEIGHBOURS):
        jobs[f"nb{i}"] = (by_id[n], {"cand": straddle}, True, False)
    for d in (10, 50):
        jobs[f"d{d}"] = (replace(repair, d=d), sp_straddle, False, False)
    for i, cid in enumerate(KELLY_CELLS):
        h = by_id[cid]
        jobs[f"kh{i}"] = (h, sp_kelly, False, False)
        jobs[f"kn{i}"] = (replace(h, off_type="neutral"), sp_kelly, False, False)

    work = []
    for lab, (cell, specs, base, wn) in jobs.items():
        for i in range(0, len(sd), CHUNK):
            work.append((lab, i, (cell, tuple(sd[i : i + CHUNK]), kappa, specs, base, wn)))
    parts: dict[str, dict[int, dict]] = {k: {} for k in jobs}
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(task, w[2]): w for w in work}
        for k, f in enumerate(as_completed(futs), 1):
            lab, i, _ = futs[f]
            parts[lab][i] = f.result()
            if k % 20 == 0 or k == len(work):
                print(f"  {k}/{len(work)} tasks, {time.time() - t0:.0f}s", flush=True)
    R = {lab: merge([p[i] for i in sorted(p)]) for lab, p in parts.items()}

    def cost(lab, name):
        return np.asarray(R[lab]["methods"][name]["cost"], dtype=float)

    def best_safe(lab):
        names = [k for k in (*fa.gated_methods(), fa.FLOOR) if k in R[lab]["methods"]]
        b = min(names, key=lambda k: float(cost(lab, k).mean()))
        return b, cost(lab, b)

    # ---------------------------------------------------------------- check 1
    alpha = repair.alpha
    bs, safe = best_safe("repair")
    fam, valid = cost("repair", "ref_family"), cost("repair", "ref_valid")
    cand, abl = cost("repair", "cand"), cost("repair", "abl")
    denom = float(safe.mean() - fam.mean())
    closure = (float(safe.mean()) - float(cand.mean())) / denom if denom > 0 else float("nan")
    nm = R["repair"]["null"]["methods"]
    null_fp = float(np.mean(nm["cand"]["fp"]))
    gain = float(safe.mean() - cand.mean())
    gain_abl = float(safe.mean() - abl.mean())
    abl_ok = bool(gain > 0 and gain_abl <= 0.5 * gain)
    nbs = []
    for i, n in enumerate(NEIGHBOURS):
        b, sc = best_safe(f"nb{i}")
        diff = cost(f"nb{i}", "cand") - sc
        nbs.append(
            {
                "cell": n,
                "best_safe": b,
                "cand_minus_best_safe": ci(diff),
                "cand_minus_R_family": ci(cost(f"nb{i}", "cand") - cost(f"nb{i}", "ref_family")),
                "ok": bool(ci(diff)[2] < fa.MATERIAL),
            }
        )
    c1 = {
        "cell": REPAIR_CELL,
        "best_safe": bs,
        "mean_cost": {
            "candidate": float(cand.mean()),
            "ablation": float(abl.mean()),
            "best_safe": float(safe.mean()),
            "R_family": float(fam.mean()),
            "R_valid": float(valid.mean()),
        },
        "gap_closure": closure,
        "cand_minus_best_safe": ci(cand - safe),
        "cand_minus_R_family": ci(cand - fam),
        "abl_minus_best_safe": ci(abl - safe),
        "cand_minus_abl": ci(cand - abl),
        "R_valid_minus_R_family": ci(valid - fam),
        "null_fp": {
            "candidate": null_fp,
            "ablation": float(np.mean(nm["abl"]["fp"])),
            "best_safe": float(np.mean(nm[bs]["fp"])),
            "R_family": float(np.mean(nm["ref_family"]["fp"])),
            "R_valid": float(np.mean(nm["ref_valid"]["fp"])),
        },
        "gain_vs_best_safe": gain,
        "ablation_gain_vs_best_safe": gain_abl,
        "neighbours": nbs,
        "criteria": {
            "closure_ge_0.5": bool(closure >= 0.5),
            "null_fp_le_alpha_plus_0.05": bool(null_fp <= alpha + fa.FP_SLACK),
            "ablation_removes_at_least_half_gain": abl_ok,
            "neighbours_ci_hi_below_0.01": bool(all(x["ok"] for x in nbs)),
        },
    }
    c1["pass"] = bool(all(c1["criteria"].values()))

    # ---------------------------------------------------------------- check 2
    lab_of = {1: "repair", 10: "d10", 50: "d50"}
    gains = {d: cost(lab, "abl") - cost(lab, "cand") for d, lab in lab_of.items()}
    diff = gains[1] - gains[50]
    c2 = {
        "grid": "onset 0.6, L 0.6, strong, harmful, b 0.05, s 0.1",
        "gain_by_d": {
            str(d): {
                "gain": ci(g),
                "cand_cost": float(cost(lab_of[d], "cand").mean()),
                "abl_cost": float(cost(lab_of[d], "abl").mean()),
            }
            for d, g in gains.items()
        },
        "gain_d1_minus_d50": ci(diff),
        "pass": bool(ci(diff)[1] > 0),
    }

    # ---------------------------------------------------------------- check 3
    n5 = range(len(KELLY_CELLS))
    kh = [cost(f"kh{i}", "abl") - cost(f"kh{i}", "cand") for i in n5]
    kn = [cost(f"kn{i}", "abl") - cost(f"kn{i}", "cand") for i in n5]
    gh, gn = np.mean(kh, axis=0), np.mean(kn, axis=0)
    ch, cn, cd = ci(gh), ci(gn), ci(gh - gn)
    harm_ok = bool(ch[0] > 0 and ch[1] > 0)
    neut_ok = bool(cn[2] < fa.MATERIAL)
    smaller = bool(cd[1] > 0)
    c3 = {
        "spec": KELLY_ID,
        "per_cell": [
            {"harmful_cell": KELLY_CELLS[i], "harmful_gain": ci(kh[i]), "neutral_gain": ci(kn[i])}
            for i in n5
        ],
        "harmful_mean_gain": ch,
        "neutral_mean_gain": cn,
        "harmful_minus_neutral": cd,
        "criteria": {
            "harmful_gain_gt0_ci_excludes0": harm_ok,
            "neutral_ci_hi_below_0.01": neut_ok,
            "neutral_significantly_smaller_than_harmful": smaller,
        },
        "pass": bool(harm_ok and (neut_ok or smaller)),
    }

    g = git_info()
    results = {
        "protocol": "docs/failure_atlas_v1_protocol.md Amendment 4",
        "git": g,
        "T": a.T,
        "kappa": kappa,
        "seeds": [sd[0], sd[-1] + 1],
        "n_seeds": len(sd),
        "workers": workers,
        "specs": {
            "straddle": STRADDLE_ID,
            "straddle_ablation": st_abl.spec_id,
            "straddle_ablation_slot": straddle.focus,
            "kelly": KELLY_ID,
            "kelly_ablation": ke_abl.spec_id,
        },
        "check1_straddle_repair": c1,
        "check2_straddle_delay_prediction": c2,
        "check3_triggered_kelly_neutral_arm": c3,
        "elapsed_s": time.time() - t0,
        "evidence_status": "mechanism-validation; not confirmatory",
    }
    (out_dir / "results.json").write_text(json.dumps(results, indent=1, default=float), "utf-8")

    def P(b):
        return "PASS" if b else "FAIL"

    cr = c1["criteria"]
    L = [
        "# Failure Atlas v1 Amendment 4 mechanism checks (mechanism-validation; NOT confirmatory)",
        "",
    ]
    L.append(
        f"git head `{g['head'][:10]}` dirty={g['dirty']}; seeds [{sd[0]}, {sd[-1] + 1}) n={len(sd)}; "
        f"T={a.T}; kappa={kappa}; sources: "
        + ", ".join(f"{k} `{v[:10]}`" for k, v in g["src_sha256"].items())
        + f"; elapsed={results['elapsed_s']:.0f}s"
    )
    L += ["", "## Verdicts", ""]
    L.append(
        f"- Check 1 straddle repair: **{P(c1['pass'])}** (closure {closure:.3f} >= 0.5: "
        f"{P(cr['closure_ge_0.5'])}; null FP {null_fp:.3f} <= {alpha + fa.FP_SLACK:.2f}: "
        f"{P(cr['null_fp_le_alpha_plus_0.05'])}; ablation removes >= half gain: {P(abl_ok)}; "
        f"neighbours CI hi < +0.01: {P(cr['neighbours_ci_hi_below_0.01'])})"
    )
    L.append(
        f"- Check 2 delay prediction: **{P(c2['pass'])}** "
        f"(gain(d=1) - gain(d=50) = {fmt(c2['gain_d1_minus_d50'])})"
    )
    L.append(
        f"- Check 3 triggered_kelly neutral arm: **{P(c3['pass'])}** (harmful gain {fmt(ch)}; "
        f"neutral gain {fmt(cn)}; harmful - neutral {fmt(cd)})"
    )
    L += [
        "",
        "## Check 1: straddle repair cell (cost per round; gain = comparator - candidate)",
        "",
    ]
    L.append("| quantity | value |\n|---|---|")
    for k, v in c1["mean_cost"].items():
        L.append(f"| mean cost {k}{' (' + bs + ')' if k == 'best_safe' else ''} | {v:.4f} |")
    L.append(f"| gap closure to R_family | {closure:.3f} |")
    L.append(f"| candidate - best_safe | {fmt(c1['cand_minus_best_safe'])} |")
    L.append(f"| candidate - R_family | {fmt(c1['cand_minus_R_family'])} |")
    L.append(f"| ablation - best_safe | {fmt(c1['abl_minus_best_safe'])} |")
    L.append(f"| candidate - ablation | {fmt(c1['cand_minus_abl'])} |")
    L.append(f"| R_valid - R_family | {fmt(c1['R_valid_minus_R_family'])} |")
    L.append(f"| ablation gain / candidate gain (vs best_safe) | {gain_abl:+.4f} / {gain:+.4f} |")
    L += ["", "Null twin false-promotion rates:", "", "| method | null FP |", "|---|---|"]
    for k, v in c1["null_fp"].items():
        L.append(f"| {k} | {v:.3f} |")
    L += [
        "",
        "Registered neighbours:",
        "",
        "| neighbour | best_safe | cand - best_safe | cand - R_family | CI hi < +0.01 |",
        "|---|---|---|---|---|",
    ]
    for x in nbs:
        L.append(
            f"| {x['cell']} | {x['best_safe']} | {fmt(x['cand_minus_best_safe'])} | "
            f"{fmt(x['cand_minus_R_family'])} | {P(x['ok'])} |"
        )
    L += [
        "",
        "## Check 2: ablation-minus-candidate gain vs delay (positive = candidate better)",
        "",
    ]
    L += ["| d | candidate cost | ablation cost | gain [95% CI] |", "|---|---|---|---|"]
    for d, v in c2["gain_by_d"].items():
        L.append(f"| {d} | {v['cand_cost']:.4f} | {v['abl_cost']:.4f} | {fmt(v['gain'])} |")
    L.append(f"\ngain(d=1) - gain(d=50): {fmt(c2['gain_d1_minus_d50'])} -> {P(c2['pass'])}")
    L += ["", f"## Check 3: `{KELLY_ID}` vs started-mixture ablation, harmful vs neutral off", ""]
    L += ["| harmful survivor cell | harmful gain | neutral gain |", "|---|---|---|"]
    for r in c3["per_cell"]:
        L.append(f"| {r['harmful_cell']} | {fmt(r['harmful_gain'])} | {fmt(r['neutral_gain'])} |")
    L.append(f"| **mean over 5 cells (per-seed)** | {fmt(ch)} | {fmt(cn)} |")
    L.append(f"\nharmful - neutral (paired by seed): {fmt(cd)}")
    L.append(
        f"\nCriteria: harmful gain > 0 with CI excluding 0: {P(harm_ok)}; neutral CI hi < 0.01: "
        f"{P(neut_ok)}; neutral significantly smaller than harmful: {P(smaller)} -> {P(c3['pass'])}"
    )
    L += [
        "",
        "## Notes",
        "",
        "- Mechanism-validation only; no confirmation seeds. Gains are per-round cost differences.",
        "- best_safe is re-selected on these seeds among gated baselines plus no_switch (as in stage 6).",
        "- Gap closure is a ratio of means; ablation criterion is gain_abl <= 0.5 * gain with gain > 0 (stage 6).",
        "- Check 2 passes if the lower 95% paired-t bound of gain(d=1) - gain(d=50) exceeds 0.",
        (
            "- Check 3 pools the five cells by averaging per-seed gains; the neutral arm passes if its CI "
            "upper bound is below 0.01 or harmful - neutral has lower CI bound above 0."
        ),
    ]
    (out_dir / "summary.md").write_text("\n".join(L) + "\n", "utf-8")
    print("\n".join(L[:10]))


if __name__ == "__main__":
    main()
