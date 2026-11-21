"""Figure 3: real streams. (a) worst adaptive risk / alpha per dataset on the 35-chain panel;
(b) pooled realised cost of safe policies in the held-out replay.

Sources:
 (a) docs/paper4_continuation/rbdp/real_data/results/phase7_baselines_T16_32/settings.jsonl
     (35 chains x 12 settings, T in {16,32}, B in {2,3,4}, alpha in {0.05,0.1}); per chain the max over settings.
 (b) docs/paper4_continuation/rbdp/real_data/results/phase9_replay.jsonl (100 datasets, 9,525 windows,
     T = 32, B = 4, alpha = 0.1, c = 0.01); window bootstrap, 2,000 resamples, seed 20261119.
Asserted: 31 of 35 chains violated by P3/P4/P5; maxima 4, 4, 8; pooled means equal Table 4 to 1e-3.
"""
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from style import PALETTE as P, REAL, WIDTH, apply_style, panel_label, read_jsonl, save

# ---- (a) panel risk ratios
NAMES = {"P1_fixed_sample": "P1", "P2_count_sprt": "P2", "P6_eprocess_gate": "P6", "P7_rbdp_causal": "P7",
         "P3_hmm_filter": "P3", "P4_myopic_voi": "P4", "P5_iid_optimal_pomdp": "P5"}
worst = defaultdict(lambda: defaultdict(float))
for r in read_jsonl(REAL / "phase7_baselines_T16_32/settings.jsonl"):
    p = NAMES[r["policy"]]
    worst[p][r["chain_id"]] = max(worst[p][r["chain_id"]], r["ratio_causal_over_alpha"])
chains = sorted(worst["P7"])
assert len(chains) == 35
viol = {c for c in chains if any(worst[p][c] > 1 + 1e-9 for p in ("P3", "P4", "P5"))}
assert len(viol) == 31, len(viol)
assert [round(max(worst[p].values()), 6) for p in ("P3", "P4", "P5")] == [4.0, 4.0, 8.0]
assert max(max(worst[p].values()) for p in ("P1", "P2", "P6", "P7")) <= 1 + 1e-9

# ---- (b) replay pooled cost
rep = [r for r in read_jsonl(REAL / "phase9_replay.jsonl") if r["status"] == "replayed"]
SAFE = ["P7", "P5r", "P2", "P3c", "P1", "P6"]
LAB = {"P7": "RB-DP", "P5r": "P5r i.i.d.-opt., repaired", "P2": "P2 count SPRT", "P3c": "P3c filter, recal.",
       "P1": "P1 fixed-sample", "P6": "P6 e-process gate"}
cost = {p: np.concatenate([np.asarray(r["cost"][p], float) for r in rep]) for p in SAFE + ["P4c"]}
n = len(cost["P7"]); assert n == 9525, n
TABLE4 = {"P7": 13.799, "P5r": 13.799, "P2": 13.838, "P3c": 13.850, "P1": 13.918, "P6": 14.173, "P4c": 15.834}
for p, v in TABLE4.items():
    assert abs(cost[p].mean() - v) < 1e-3, (p, cost[p].mean(), v)
rng = np.random.default_rng(20261119)
idx = rng.integers(0, n, size=(2000, n))
ci = {p: np.percentile(cost[p][idx].mean(axis=1), [2.5, 97.5]) for p in SAFE}

apply_style(8.5)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(WIDTH, 2.9), gridspec_kw=dict(width_ratios=[1.0, 1.15], wspace=0.55))
pols = ["P7", "P1", "P2", "P6", "P3", "P4", "P5"]
rng_j = np.random.default_rng(0)
for i, p in enumerate(pols):
    y = np.array([worst[p][c] for c in chains])
    col = P["blue_main"] if p == "P7" else (P["grey"] if p in ("P1", "P2", "P6") else P["red_strong"])
    a1.scatter(i + rng_j.uniform(-0.18, 0.18, len(y)), y, s=9, color=col, alpha=0.7, linewidths=0)
a1.axhline(1, color=P["dark"], lw=0.8, ls=":")
a1.text(6.6, 1.08, "budget $\\alpha$", fontsize=7, ha="right", va="bottom")
a1.set_yscale("log", base=2); a1.set_yticks([0.5, 1, 2, 4, 8]); a1.set_yticklabels(["1/2", "1", "2", "4", "8"])
a1.set_xticks(range(len(pols))); a1.set_xticklabels(pols)
a1.set_ylabel("worst adaptive risk / $\\alpha$ per dataset")
a1.set_title("35 fitted chains, 12 settings each", loc="left", fontsize=8.5)
a1.text(5, 0.42, "i.i.d.-calibrated", fontsize=7, color=P["red_strong"], ha="center")
a1.text(1.5, 0.42, "causal-safe", fontsize=7, color=P["grey"], ha="center")
a1.set_ylim(0.38, 10)

for j, p in enumerate(SAFE):
    m = cost[p].mean(); lo, hi = ci[p]
    col = P["blue_main"] if p == "P7" else P["red_strong"]
    a2.errorbar(m, j, xerr=[[m - lo], [hi - m]], fmt="o", color=col, ms=4.5, capsize=2.5, lw=1.1,
                mfc=col if p == "P7" else "white")
a2.axvline(cost["P7"].mean(), color=P["blue_main"], lw=0.7, ls=":")
a2.set_yticks(range(len(SAFE))); a2.set_yticklabels([LAB[p] for p in SAFE]); a2.invert_yaxis()
a2.set_xlabel("mean realised cost per window (95% bootstrap CI)")
a2.set_title("held-out replay, 9,525 windows", loc="left", fontsize=8.5)
panel_label(a1, "a", dx=-0.3, dy=1.1); panel_label(a2, "b", dx=-0.06, dy=1.1)
save(fig, "real")
print("wrote fig_real; CI:", {p: [round(x, 3) for x in ci[p]] for p in SAFE})
