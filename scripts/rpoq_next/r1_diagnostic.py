"""Post-hoc diagnostic for R1 (not part of the registered rule): did the pre-test favourite bin keep its signal?"""

import sys
from pathlib import Path

import numpy as np

from shiftlab.dive.rpoq_crsp_replay import COHORT_SIZE, COLUMNS, N_COHORTS, SEED, _load_rows
from shiftlab.dive.rpoq_crsp_replay_b import build_cohort_b
from shiftlab.dive.rpoq_next.crsp_r1 import NB, bin_estimates, bin_propensities

panel = Path(sys.argv[1])
base = _load_rows(panel, None, ["permno", "split"])
pa, sa = base["permno"].to_numpy(), np.asarray(base["split"].to_pylist(), dtype=object)
chosen = np.random.default_rng(SEED).permutation(np.unique(pa[sa == "train"]))[
    : N_COHORTS * COHORT_SIZE
]
table = _load_rows(panel, chosen, COLUMNS)
pre_mu, test_mu, q05, q20, share = (np.zeros(NB) for _ in range(5))
n_ok = 0
test_n, test_s = np.zeros(NB), np.zeros(NB)
for ci in range(N_COHORTS):
    cp = chosen[ci * COHORT_SIZE : (ci + 1) * COHORT_SIZE]
    pre = [build_cohort_b(table, cp, eval_split=s) for s in ("validation", "calibration")]
    te = build_cohort_b(table, cp, eval_split="test")
    mu, h, r, _ = bin_estimates(pre)
    p = np.bincount(pre[1]["ctx_size"], minlength=NB) / len(pre[1]["ctx_size"])
    pre_mu += mu
    q05 += bin_propensities("growth", mu, h, r, p, 0.05)
    q20 += bin_propensities("growth", mu, h, r, p, 0.20)
    share += np.bincount(te["ctx_size"], minlength=NB) / te["n_events"]
    for b in range(NB):
        m = te["ctx_size"] == b
        test_n[b] += m.sum()
        test_s[b] += (-te["z"])[m].sum()
    n_ok += 1
print("bin                  ", list(range(NB)))
print("pre-test mu (bps)    ", np.round(pre_mu / n_ok * 1e4, 1))
print("test mu (bps)        ", np.round(test_s / np.maximum(test_n, 1) * 1e4, 1))
print("growth q (5%, avg)   ", np.round(q05 / n_ok, 3))
print("growth q (20%, avg)  ", np.round(q20 / n_ok, 3))
print("test event share     ", np.round(share / n_ok, 3))
