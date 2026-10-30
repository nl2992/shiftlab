"""B1: repo evidence-directed query rule vs uniform on the CRSP stream (docs/rpoq_next/REAL_DATA_PROTOCOL.md)."""

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

from shiftlab.dive.query import EvidenceDirectedQueryPolicy
from shiftlab.dive.rpoq_crsp_replay import BOUND, COHORT_SIZE, COLUMNS, N_COHORTS, SEED, _load_rows
from shiftlab.dive.rpoq_crsp_replay_b import build_cohort_b

ALPHA, FRACS, SEEDS = 0.05, (0.05, 0.20), 20


def run(c, frac, u, policy):
    """Date-batched PPI e-process, pooled plug-in Kelly bet, propensity from ``policy`` (None = uniform)."""
    y, h, di, n = -c["z"], -c["h"], c["date_index"], c["n_events"]
    cap = round(frac * n)
    starts = np.r_[0, np.flatnonzero(np.diff(di)) + 1, n]
    m1 = m2 = cnt = 0.0
    spent, log_w, first, thr = 0, 0.0, None, np.log(1 / ALPHA)
    for k in range(len(starts) - 1):
        a, b = starts[k], starts[k + 1]
        q = (
            frac
            if policy is None
            else policy.propensity(log_e_value=log_w, remaining_fraction=max(0.0, 1 - spent / cap))
        )
        qr = u[a:b] < q
        active = (spent + np.cumsum(qr) - qr) < cap
        queried = qr & active
        x = np.where(active, h[a:b] + queried * (y[a:b] - h[a:b]) / q, 0.0)
        mean, second = m1 / (cnt + 1), m2 / (cnt + 1)
        lam = (
            min(mean / second, 0.5 / (BOUND * (2.0 / q - 1.0))) if second > 0 and mean > 0 else 0.0
        )
        log_w += float(np.log1p(lam * x).sum())
        spent += int(queried.sum())
        m1, m2, cnt = m1 + x[active].sum(), m2 + (x[active] ** 2).sum(), cnt + active.sum()
        if first is None and log_w >= thr:
            first = k
    return {"log_wealth": log_w, "crossed": first is not None, "spent": spent}


def main():
    panel = Path(sys.argv[1])
    t0 = time.time()
    base = _load_rows(panel, None, ["permno", "split"])
    permno_all, split_all = (
        base["permno"].to_numpy(),
        np.asarray(base["split"].to_pylist(), dtype=object),
    )
    chosen = np.random.default_rng(SEED).permutation(np.unique(permno_all[split_all == "train"]))[
        : N_COHORTS * COHORT_SIZE
    ]
    table = _load_rows(panel, chosen, COLUMNS)
    runs = []
    for ci in range(N_COHORTS):
        c = build_cohort_b(
            table, chosen[ci * COHORT_SIZE : (ci + 1) * COHORT_SIZE], eval_split="test"
        )
        if c is None:
            continue
        for frac in FRACS:
            ed = EvidenceDirectedQueryPolicy(
                q_min=0.25 * frac, q_max=min(1.0, 2.5 * frac), alpha=ALPHA
            )
            for arm, pol in (("uniform", None), ("evidence_directed", ed)):
                for s in range(SEEDS):
                    u = np.random.default_rng(SEED + 1000 * ci + s).random(c["n_events"])
                    runs.append(
                        {
                            "cohort": ci,
                            "budget_fraction": frac,
                            "arm": arm,
                            "seed": s,
                            **run(c, frac, u, pol),
                        }
                    )
        print(f"cohort {ci} done ({time.time() - t0:.0f}s)", flush=True)
    out = Path("outputs/rpoq_next/b1")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "runs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(runs[0]))
        w.writeheader()
        w.writerows(runs)
    rng = np.random.default_rng(31)
    summary = {}
    for frac in FRACS:
        m = {a: {} for a in ("uniform", "evidence_directed")}
        sp = {a: [] for a in m}
        cr = {a: [] for a in m}
        for r in runs:
            if r["budget_fraction"] == frac:
                m[r["arm"]].setdefault(r["cohort"], []).append(r["log_wealth"])
                sp[r["arm"]].append(r["spent"])
                cr[r["arm"]].append(r["crossed"])
        ids = sorted(m["uniform"])
        diff = np.array(
            [np.mean(m["evidence_directed"][k]) - np.mean(m["uniform"][k]) for k in ids]
        )
        boot = diff[rng.integers(0, len(diff), (2000, len(diff)))].mean(1)
        summary[str(frac)] = {
            "uniform_lw": float(np.mean([np.mean(v) for v in m["uniform"].values()])),
            "evidence_directed_lw": float(
                np.mean([np.mean(v) for v in m["evidence_directed"].values()])
            ),
            "diff": [
                float(diff.mean()),
                float(np.quantile(boot, 0.025)),
                float(np.quantile(boot, 0.975)),
            ],
            "mean_spent": {a: float(np.mean(v)) for a, v in sp.items()},
            "crossing": {a: float(np.mean(v)) for a, v in cr.items()},
        }
        print(frac, summary[str(frac)], flush=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
