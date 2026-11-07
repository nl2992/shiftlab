"""CRSP replay S6c: calibration-tuned active/uniform mixture (ASI-MIX).

Implements ``docs/rpoq_s6c_calibration_tuned_mixture_protocol_v1.md``. Epsilon is chosen on
the calibration split; the test split is run once. Exploratory; imposed clock and null.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from shiftlab.dive.rpoq_crsp_replay import (
    BUDGET_FRACTIONS,
    COHORT_SIZE,
    COLUMNS,
    N_COHORTS,
    QUERY_SEEDS,
    SEED,
    _bootstrap,
    _load_rows,
    run_monitor,
)
from shiftlab.dive.rpoq_crsp_replay_b import _propensity_from_root, build_cohort_b

EPSILONS = (0.0, 0.25, 0.5, 0.75, 1.0)
DEV_SEEDS = 5


def _with_q(c: dict, frac: float, eps: float) -> dict:
    root, val_mean = c["root_by_budget"][frac]
    q_vs = _propensity_from_root(root, val_mean, frac)
    return {**c, "q_custom": eps * frac + (1.0 - eps) * q_vs}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", required=True)
    parser.add_argument("--s6-runs", required=True)
    parser.add_argument("--output-dir", default="outputs/rpoq_s6c_crsp_mix_v1")
    parser.add_argument("--cohorts", type=int, default=N_COHORTS)
    args = parser.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    base = _load_rows(Path(args.panel), None, ["permno", "split"])
    permno_all = base["permno"].to_numpy()
    split_all = np.asarray(base["split"].to_pylist(), dtype=object)
    universe = np.unique(permno_all[split_all == "train"])
    chosen = rng.permutation(universe)[: args.cohorts * COHORT_SIZE]
    cohorts = [chosen[i * COHORT_SIZE : (i + 1) * COHORT_SIZE] for i in range(args.cohorts)]
    table = _load_rows(Path(args.panel), chosen, COLUMNS)

    dev = {(f, e): [] for f in BUDGET_FRACTIONS for e in EPSILONS}
    built_dev = []
    for ci, cp in enumerate(cohorts):
        c = build_cohort_b(table, cp, eval_split="calibration")
        if c is None:
            continue
        for f in BUDGET_FRACTIONS:
            for e in EPSILONS:
                cc = _with_q(c, f, e)
                vals = [
                    run_monitor(
                        cc,
                        "custom",
                        -1.0,
                        f,
                        np.random.default_rng(SEED + 1000 * ci + 100 + s).random(c["n_events"]),
                    )["log_wealth"]
                    for s in range(DEV_SEEDS)
                ]
                dev[(f, e)].append(float(np.mean(vals)))
        built_dev.append(ci)
        print(f"dev cohort {ci} ({time.time() - t0:.0f}s)", flush=True)
    chosen_eps = {}
    for f in BUDGET_FRACTIONS:
        means = {e: float(np.mean(dev[(f, e)])) for e in EPSILONS}
        best = max(EPSILONS, key=lambda e: (round(means[e], 12), e))
        chosen_eps[f] = {"epsilon": best, "calibration_mean_log_wealth": means}
    print("chosen", {k: v["epsilon"] for k, v in chosen_eps.items()}, flush=True)

    runs = []
    for ci, cp in enumerate(cohorts):
        c = build_cohort_b(table, cp, eval_split="test")
        if c is None:
            continue
        for f in BUDGET_FRACTIONS:
            cc = _with_q(c, f, chosen_eps[f]["epsilon"])
            for s in range(QUERY_SEEDS):
                u = np.random.default_rng(SEED + 1000 * ci + s).random(c["n_events"])
                res = run_monitor(cc, "custom", -1.0, f, u)
                runs.append(
                    {
                        "cohort": ci,
                        "direction": "benefit",
                        "budget_fraction": f,
                        "rule": "asi_mix",
                        "seed": s,
                        **res,
                    }
                )
        print(f"test cohort {ci} ({time.time() - t0:.0f}s)", flush=True)

    s6: dict[tuple, dict[int, list[float]]] = {}
    with open(args.s6_runs) as fh:
        for r in csv.DictReader(fh):
            if (
                r["rule"] in ("uniform", "oracle")
                and r["budget_fraction"]
                and r["direction"] == "benefit"
            ):
                s6.setdefault((float(r["budget_fraction"]), r["rule"]), {}).setdefault(
                    int(r["cohort"]), []
                ).append(float(r["log_wealth"]))
    brng = np.random.default_rng(SEED + 13)
    summary = []
    for f in BUDGET_FRACTIONS:
        mine = {}
        for r in runs:
            if r["budget_fraction"] == f:
                mine.setdefault(r["cohort"], []).append(r["log_wealth"])
        ids = sorted(mine)
        row = {
            "budget_fraction": f,
            "epsilon": chosen_eps[f]["epsilon"],
            "asi_mix_mean_log_wealth": _bootstrap(np.array([np.mean(mine[k]) for k in ids]), brng),
        }
        for other in ("uniform", "oracle"):
            o = s6[(f, other)]
            row[f"diff_vs_{other}"] = _bootstrap(
                np.array([np.mean(mine[k]) - np.mean(o[k]) for k in ids if k in o]), brng
            )
        summary.append(row)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps(
            {
                "protocol": "docs/rpoq_s6c_calibration_tuned_mixture_protocol_v1.md",
                "chosen": {str(k): v for k, v in chosen_eps.items()},
                "summary": summary,
                "seconds": time.time() - t0,
            },
            indent=2,
        )
    )
    with (out / "runs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(runs[0]))
        w.writeheader()
        w.writerows(runs)
    (out / "checksums.sha256").write_text(
        "".join(
            f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
            for p in sorted(out.glob("*"))
            if p.name != "checksums.sha256"
        )
    )
    for row in summary:
        print(row)


if __name__ == "__main__":
    main()
