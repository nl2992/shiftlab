"""Funnel-1 smoke: all regimes x seeds x baselines. NOT a claim; descriptive plumbing check.

Run: PYTHONPATH=src python scripts/paper3/core/smoke.py [--seeds 5] [--T 300]
Writes outputs/paper3/smoke/{per_run,summary_J}.csv and appends one record to
papers/paper3_cost_aware_adaptation/2026_programme/ledger/core.jsonl.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.paper3.baselines import LABELS, default_baselines
from shiftlab.paper3.simulation import (
    CONFIG_DIR,
    SimulationEvaluator,
    generate_tape,
    load_regimes,
    make_spec,
    run_policy,
    seeds_for,
)

ROOT = Path(__file__).resolve().parents[3]
LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/core.jsonl"


def git(*a):
    try:
        return subprocess.run(
            ["git", *a], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()
    except OSError:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--T", type=int, default=300)
    ap.add_argument("--out", default=str(ROOT / "outputs/paper3/smoke"))
    args = ap.parse_args()
    t0 = time.time()
    regimes, seeds = load_regimes(), seeds_for("smoke", args.seeds)
    rows = []
    for rid, reg in regimes.items():
        spec = make_spec(reg, args.T)
        for s in seeds:
            tape, truth = generate_tape(reg, s, args.T)
            ev = SimulationEvaluator(tape, truth, spec.costs)
            for i, pol in enumerate(default_baselines(args.T)):
                rec = run_policy(pol, tape, spec, policy_seed=s * 100 + i)
                rows.append({"regime": rid, "seed": s, "policy": pol.name, **ev.evaluate(rec)})
    df = pd.DataFrame(rows)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "per_run.csv", index=False)
    piv = df.pivot_table(index="regime", columns="policy", values="J", aggfunc="mean")
    piv.to_csv(out / "summary_J.csv")
    cfg_hash = hashlib.sha256((CONFIG_DIR / "regimes_v1.json").read_bytes()).hexdigest()[:16]
    rec = {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_sha": git("rev-parse", "HEAD"),
        "git_dirty": bool(
            git("status", "--porcelain", "--", "src/shiftlab/paper3", "configs/paper3")
        ),
        "stage": "funnel1_smoke",
        "config": {
            "regimes_sha256_16": cfg_hash,
            "T": args.T,
            "n_regimes": len(regimes),
            "policies": [p.name for p in default_baselines(args.T)],
            "labels": LABELS,
        },
        "seed_range": ["smoke", seeds[0], seeds[-1]],
        "metrics": {
            "mean_J_over_regimes": piv.mean().round(4).to_dict(),
            "mean_J_never": float(df[df.policy == "never"].J.mean()),
            "n_runs": len(df),
        },
        "wall_clock_s": round(time.time() - t0, 1),
        "status": "smoke_only_not_a_claim",
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    pd.set_option("display.width", 250)
    show = [
        "stationary_null",
        "stationary_better",
        "abrupt_beneficial",
        "abrupt_harmful",
        "multiple_reversals",
        "label_scarcity",
        "expensive_switch",
    ]
    print(piv.loc[show].round(1).to_string())
    print("mean over regimes:\n", piv.mean().round(2).to_string())
    print(f"runs={len(df)} wall={rec['wall_clock_s']}s")
    np.seterr()


if __name__ == "__main__":
    main()
