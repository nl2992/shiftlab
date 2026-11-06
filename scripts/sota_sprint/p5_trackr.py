"""Separate K=3/4 empirical risk/cost calibration for P5.

Risk is the episode-level ever-nonbetter deployment rate on K3/K4 designated nulls.
Alpha is selected from development seeds and evaluated on separate deterministic seeds.
This is an empirical P5-specific curve, not the two-model family risk grid or a guarantee.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))
sys.path.insert(1, str(ROOT / "scripts/failure_atlas_v2"))
import fam_p
from bench2 import ALPHA_GRID
from simulator import policy_rng, run_episode
from suite import stream_from_losses

NULLS = ["K3_null", "K4_null"]
ALTS = ["K3_best1", "K4_mixed", "K3_near", "K4_late"]


def mean_ci(values):
    values = np.asarray(values, dtype=float)
    m = float(values.mean())
    half = float(1.96 * values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.0
    return [m - half, m + half]


def block_values(rows, regimes, key):
    return np.asarray(
        [
            np.mean([x[key] for x in rows if x["seed"] == seed and x["regime"] in regimes])
            for seed in sorted({x["seed"] for x in rows if x["regime"] in regimes})
        ]
    )


def risk_ci(values):
    lo, hi = mean_ci(values)
    return [max(0.0, lo), min(1.0, hi)]


def one(job):
    phase, name, seed, alpha = job
    reg = fam_p.K_REGIMES[name]
    losses = reg.sample(
        np.random.default_rng([2026110701 if phase == "dev" else 2026110711, fam_p._h(name), seed])
    )
    K = reg.K
    T = len(losses)
    B = 200
    r = lambda nm: policy_rng(
        (2026110701 if phase == "dev" else 2026110711) + fam_p._h(name) % 1000,
        seed,
        f"{nm}:{alpha}",
    )
    pol = fam_p.k_policies(K, T, B, alpha, r)["K_D2"]
    preds, labels = stream_from_losses(losses, np.random.default_rng([seed, fam_p._h(name), 7]))
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=reg.delay,
        budget=B,
        label_price=0.05,
        switch_cost=5.0,
        trace=True,
    )
    dep = np.fromiter((x["deployed_model"] for x in res.records), int, T)
    gain = reg.truth_gain(T)
    risk = int(((gain[np.arange(T), dep] <= 0) & (dep != 0)).any()) if name in NULLS else None
    return {
        "phase": phase,
        "regime": name,
        "seed": seed,
        "alpha": alpha,
        "risk": risk,
        "net": float(res.net_cost),
        "labels": int(res.requested_labels),
        "switches": int(res.deployment_switches),
    }


def batch(job):
    phase, name, alpha, base, seeds, outdir = job
    rows = [one((phase, name, base + i, alpha)) for i in range(seeds)]
    path = Path(outdir) / f"{phase}_{name}_a{alpha}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows))
    os.replace(tmp, path)
    return str(path)


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", default="outputs/sprint2/P/trackR_K")
    a = ap.parse_args()
    jobs = []
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ck = out / "checkpoints"
    ck.mkdir(exist_ok=True)
    for phase, base in [("dev", 2026110701), ("eval", 2026110711)]:
        for nm in NULLS + ALTS:
            for alpha in ALPHA_GRID:
                path = ck / f"{phase}_{nm}_a{alpha}.json"
                if path.exists():
                    try:
                        cached = json.loads(path.read_text())
                    except (json.JSONDecodeError, OSError):
                        cached = []
                    if len(cached) == a.seeds:
                        continue
                    path.unlink()
                jobs.append((phase, nm, alpha, base, a.seeds, str(ck)))
    # The repo's dynamic module loader shadows the top-level `regimes` module under spawn on macOS.
    # Fork here preserves the already resolved family imports and each batch writes a checkpoint.
    with mp.get_context("fork").Pool(a.workers) as pool:
        list(pool.imap_unordered(batch, jobs, chunksize=1))
    rows = []
    for p in sorted(ck.glob("*.json")):
        rows.extend(json.loads(p.read_text()))
    curves = {}
    for target, pct in [
        ("R5", 0.05),
        ("R10", 0.1),
        ("R15", 0.15),
        ("R20", 0.2),
        ("R25", 0.25),
        ("R30", 0.3),
    ]:
        cand = []
        for alpha in ALPHA_GRID:
            d = [
                x
                for x in rows
                if x["phase"] == "dev" and x["regime"] in NULLS and x["alpha"] == alpha
            ]
            risk = float(np.mean([x["risk"] for x in d]))
            if risk <= pct:
                e = [
                    x
                    for x in rows
                    if x["phase"] == "eval" and x["regime"] in NULLS and x["alpha"] == alpha
                ]
                arows = [
                    x
                    for x in rows
                    if x["phase"] == "eval" and x["regime"] in ALTS and x["alpha"] == alpha
                ]
                d_alt = [
                    x
                    for x in rows
                    if x["phase"] == "dev" and x["regime"] in ALTS and x["alpha"] == alpha
                ]
                dev_cost_blocks = block_values(d_alt, ALTS, "net")
                eval_risk_blocks = block_values(e, NULLS, "risk")
                eval_cost_blocks = block_values(arows, ALTS, "net")
                cand.append(
                    {
                        "alpha": alpha,
                        "dev_risk": risk,
                        "dev_alt_net": float(dev_cost_blocks.mean()),
                        "eval_risk": float(eval_risk_blocks.mean()),
                        "eval_risk_ci": risk_ci(eval_risk_blocks),
                        "eval_risk_n": len(e),
                        "eval_risk_seed_blocks": len(eval_risk_blocks),
                        "alt_net": float(eval_cost_blocks.mean()),
                        "alt_net_ci": mean_ci(eval_cost_blocks),
                        "alt_net_n": len(arows),
                        "alt_cost_seed_blocks": len(eval_cost_blocks),
                    }
                )
        curves[target] = {"K_D2": min(cand, key=lambda z: z["dev_alt_net"])} if cand else {}
    (out / "records.json").write_text(json.dumps({"rows": rows}, indent=2) + "\n")
    result = {
        "family": "P5",
        "risk_estimand": "episode ever-deployment to a nonbetter model; designated K3/K4 nulls, pooled equally by episode",
        "alpha_grid": ALPHA_GRID,
        "seeds_per_regime_alpha": a.seeds,
        "development_seed_base": 2026110701,
        "evaluation_seed_base": 2026110711,
        "curves": curves,
    }
    (out / "risk_curves.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
