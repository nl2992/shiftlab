"""Paired J differences (candidate - comparator) on alternatives, regime-equal weights.

Usage: paired.py DIR[,DIR2...] CANDIDATE COMP1,COMP2,... [--regimes a,b,c] [--boot 4000]
Pairs by (regime, seed, ep). Percentile bootstrap over seeds, stratified by regime.
"""

import argparse
import collections
import json
from pathlib import Path

import numpy as np

ALTS = ["F0_better", "F5_dep_better_r8", "S_dep_better_r95", "WP2_o2_better", "WP2_sm_better",
        "WP2_hs_better"]  # fmt: skip


def load(dirs, field="net"):
    D = collections.defaultdict(dict)
    for d in dirs.split(","):
        for line in Path(d, "records.jsonl").read_text().splitlines():
            r = json.loads(line)
            D[r["policy"]][(r["regime"], r["seed"], r.get("ep", 0))] = r[field]
    return D


def paired(D, cand, comp, regimes, nboot=4000, seed=0):
    rng = np.random.default_rng(seed)
    per = []
    for g in regimes:
        keys = sorted(k for k in D[cand] if k[0] == g and k in D[comp])
        per.append(np.array([D[cand][k] - D[comp][k] for k in keys]))
    est = np.mean([x.mean() for x in per])
    bs = np.mean([x[rng.integers(0, len(x), (nboot, len(x)))].mean(1) for x in per], axis=0)
    base = np.mean([np.mean([D[comp][k] for k in D[comp] if k[0] == g]) for g in regimes])
    return est, np.percentile(bs, [2.5, 97.5]), base, sum(len(x) for x in per)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs")
    ap.add_argument("cand")
    ap.add_argument("comps")
    ap.add_argument("--regimes", default=",".join(ALTS))
    ap.add_argument("--field", default="net")
    a = ap.parse_args()
    D = load(a.dirs, a.field)
    regs = [g.replace("@", "@") for g in a.regimes.split(",")]
    for c in a.comps.split(","):
        est, ci, base, n = paired(D, a.cand, c, regs)
        print(
            f"{a.cand} - {c:28s} {est:+7.2f} [{ci[0]:+7.2f},{ci[1]:+7.2f}]  ({100 * est / base:+5.1f}% of {base:6.1f}; n={n})"
        )
