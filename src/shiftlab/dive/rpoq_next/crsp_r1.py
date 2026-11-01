"""R1: exploratory CRSP allocation replay on the size context (docs/rpoq_next/REAL_DATA_PROTOCOL.md).

Per-cohort bin estimates come from the validation and calibration splits (pre-test). The test
split is exposed, so results are descriptive. Imposed clock, costs and null; no validity claim.
"""

import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

from shiftlab.dive.rpoq_crsp_replay import BOUND, COHORT_SIZE, COLUMNS, N_COHORTS, SEED, _load_rows
from shiftlab.dive.rpoq_crsp_replay_b import build_cohort_b
from shiftlab.dive.rpoq_next.growth_alloc import allocate, neyman

NB, ALPHA, BUDGET_FRACTIONS, SEEDS = 8, 0.05, (0.05, 0.20), 20
ARMS, BETS = ("uniform", "neyman", "growth", "random_conc"), ("ctx", "common")


def bin_estimates(cohorts):
    """Per-bin benefit mean, mean proxy, residual second moment and event share, from pre-test splits."""
    n = np.zeros(NB)
    s_y, s_h, s_r = np.zeros(NB), np.zeros(NB), np.zeros(NB)
    for c in cohorts:
        y, h = -c["z"], -c["h"]
        for b in range(NB):
            m = c["ctx_size"] == b
            n[b] += m.sum()
            s_y[b] += y[m].sum()
            s_h[b] += h[m].sum()
            s_r[b] += ((y - h)[m] ** 2).sum()
    ok = (
        n >= 50
    )  # shortcut: sparse bins fall back to the pooled value; upgrade to shrinkage if bins get thin
    pooled_r = s_r.sum() / max(n.sum(), 1)
    mu = np.where(ok, s_y / np.maximum(n, 1), 0.0)
    h = np.where(ok, s_h / np.maximum(n, 1), 0.0)
    r = np.where(ok, s_r / np.maximum(n, 1), pooled_r)
    return mu, h, np.maximum(r, 1e-8), n / n.sum()


def normalize(q, p, frac):
    """Rescale so the expected label rate sum(p*q) equals ``frac`` within [0.1*frac, 1]."""
    for _ in range(8):
        q = np.clip(q * frac / float(p @ q), 0.1 * frac, 1.0)
    return q


def bin_propensities(arm, mu, h, r, p, frac, chosen=0):
    floor = 0.1 * frac
    if arm == "uniform":
        return np.full(NB, frac)
    if arm == "neyman":
        return normalize(neyman(r, NB * frac, floor), p, frac)
    if arm == "growth":
        return normalize(allocate(mu, h, r, NB * frac, BOUND, floor), p, frac)
    q = np.full(NB, floor)  # random_conc: placebo with the same concentration but no information
    q[chosen] = min(1.0, (frac - floor * (1 - p[chosen])) / max(p[chosen], 1e-9))
    return q


def run_monitor_ctx(c, q_bin, frac, u, bet):
    """Date-batched prediction-powered e-process with per-bin or pooled plug-in Kelly bets."""
    y, h, ctx, di, n = -c["z"], -c["h"], c["ctx_size"], c["date_index"], c["n_events"]
    q = q_bin[ctx]
    bounds = BOUND * (2.0 / q - 1.0)
    q_raw = u < q
    cap = round(frac * n)
    starts = np.r_[0, np.flatnonzero(np.diff(di)) + 1, n]
    m1, m2, cnt = np.zeros(NB), np.zeros(NB), np.zeros(NB)
    spent, log_w, first, thr = 0, 0.0, None, np.log(1 / ALPHA)
    for k in range(len(starts) - 1):
        a, b = starts[k], starts[k + 1]
        qr = q_raw[a:b]
        active = (spent + np.cumsum(qr) - qr) < cap
        queried = qr & active
        x = np.where(active, h[a:b] + queried * (y[a:b] - h[a:b]) / q[a:b], 0.0)
        cx = ctx[a:b]
        if bet == "ctx":
            mean, second = m1[cx] / (cnt[cx] + 1), m2[cx] / (cnt[cx] + 1)
        else:
            mean, second = m1.sum() / (cnt.sum() + 1), m2.sum() / (cnt.sum() + 1)
        lam = np.where(
            (second > 0) & (mean > 0),
            np.minimum(mean / np.maximum(second, 1e-12), 0.5 / bounds[a:b]),
            0.0,
        )
        log_w += float(np.log1p(lam * x).sum())
        spent += int(queried.sum())
        np.add.at(m1, cx[active], x[active])
        np.add.at(m2, cx[active], x[active] ** 2)
        np.add.at(cnt, cx[active], 1.0)
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
        cp = chosen[ci * COHORT_SIZE : (ci + 1) * COHORT_SIZE]
        pre = [build_cohort_b(table, cp, eval_split=s) for s in ("validation", "calibration")]
        test = build_cohort_b(table, cp, eval_split="test")
        if test is None or any(x is None for x in pre):
            continue
        mu, h, r, _ = bin_estimates(pre)
        p = np.bincount(pre[1]["ctx_size"], minlength=NB) / len(pre[1]["ctx_size"])
        for frac in BUDGET_FRACTIONS:
            for arm in ARMS:
                for s in range(SEEDS):
                    pick = int(np.random.default_rng(SEED + 777 + 1000 * ci + s).integers(NB))
                    q_bin = bin_propensities(arm, mu, h, r, p, frac, pick)
                    u = np.random.default_rng(SEED + 1000 * ci + s).random(test["n_events"])
                    for bet in BETS:
                        res = run_monitor_ctx(test, q_bin, frac, u, bet)
                        runs.append(
                            {
                                "cohort": ci,
                                "budget_fraction": frac,
                                "arm": arm,
                                "bet": bet,
                                "seed": s,
                                **res,
                            }
                        )
        print(f"cohort {ci} done ({time.time() - t0:.0f}s)", flush=True)
    out = Path("outputs/rpoq_next/r1")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "runs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(runs[0]))
        w.writeheader()
        w.writerows(runs)
    (out / "meta.json").write_text(
        json.dumps(
            {
                "protocol": "docs/rpoq_next/REAL_DATA_PROTOCOL.md (R1)",
                "n_runs": len(runs),
                "seconds": time.time() - t0,
            }
        )
    )


if __name__ == "__main__":
    main()
