"""Exploratory CRSP replay of the frozen parent vs DK e-processes (docs/sota_synthetic_search/15_*)."""

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

from shiftlab.dive.rpoq_crsp_replay import BOUND, COHORT_SIZE, COLUMNS, N_COHORTS, SEED, _load_rows
from shiftlab.dive.rpoq_crsp_replay_b import build_cohort_b

ALPHA, FRACS, SEEDS, GAMMA = 0.05, (0.05, 0.20), 20, 0.995


def run(z, h, di, frac, u, gamma):
    """Date-batched tight-capped PP e-process; moments discounted per date when gamma < 1."""
    n = len(z)
    starts = np.r_[0, np.flatnonzero(np.diff(di)) + 1, n]
    m1 = m2 = cnt = 0.0
    log_w, first = 0.0, None
    thr = np.log(1 / ALPHA)
    for k in range(len(starts) - 1):
        a, b = starts[k], starts[k + 1]
        q = (u[a:b] < frac).astype(float)
        x = h[a:b] + q / frac * (z[a:b] - h[a:b])
        bound = np.maximum(BOUND, (BOUND + h[a:b]) / frac - h[a:b])
        mean, second = m1 / (cnt + 1), m2 / (cnt + 1)
        lam = min(mean / second, 0.5 / bound.max()) if second > 0 and mean > 0 else 0.0
        log_w += float(np.log1p(lam * x).sum())
        m1, m2, cnt = gamma * m1 + x.sum(), gamma * m2 + (x**2).sum(), gamma * cnt + len(x)
        if first is None and log_w >= thr:
            first = k
    return log_w, first is not None


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
        for direction, sg in (("harm", 1.0), ("benefit", -1.0)):
            z, h = sg * c["z"], sg * np.clip(c["h"], -BOUND, BOUND)
            for frac in FRACS:
                for s in range(SEEDS):
                    u = np.random.default_rng(SEED + 1000 * ci + s).random(c["n_events"])
                    for arm, gm in (("parent", 1.0), ("DK", GAMMA)):
                        lw, cr = run(z, h, c["date_index"], frac, u, gm)
                        runs.append(
                            {
                                "cohort": ci,
                                "direction": direction,
                                "frac": frac,
                                "seed": s,
                                "arm": arm,
                                "log_wealth": lw,
                                "crossed": cr,
                            }
                        )
        print(f"cohort {ci} ({time.time() - t0:.0f}s)", flush=True)
    out = Path("outputs/sota_search/crsp_replay")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "runs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(runs[0]))
        w.writeheader()
        w.writerows(runs)
    rng = np.random.default_rng(31)
    summ = {}
    for d in ("harm", "benefit"):
        for f in FRACS:
            per = {}
            for r in runs:
                if r["direction"] == d and r["frac"] == f:
                    per.setdefault((r["arm"], r["cohort"]), []).append(
                        (r["log_wealth"], r["crossed"])
                    )
            ids = sorted({k[1] for k in per})
            m = {
                a: np.array([np.mean([x[0] for x in per[(a, i)]]) for i in ids])
                for a in ("parent", "DK")
            }
            cr = {a: float(np.mean([np.mean([x[1] for x in per[(a, i)]]) for i in ids])) for a in m}
            diff = m["DK"] - m["parent"]
            boot = diff[rng.integers(0, len(diff), (4000, len(diff)))].mean(1)
            summ[f"{d}/{f}"] = {
                "parent_lw": float(m["parent"].mean()),
                "DK_lw": float(m["DK"].mean()),
                "diff": [
                    float(diff.mean()),
                    float(np.quantile(boot, 0.025)),
                    float(np.quantile(boot, 0.975)),
                ],
                "crossing": cr,
                "n_cohorts": len(ids),
            }
            print(d, f, summ[f"{d}/{f}"], flush=True)
    (out / "summary.json").write_text(json.dumps(summ, indent=2))


if __name__ == "__main__":
    main()
