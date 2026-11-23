"""Figure 3: real streams. (a) worst adaptive risk / alpha per dataset on the 44-chain panel;
(b) pooled realised cost of safe policies in the held-out replay.

Sources:
 (a) docs/paper4_continuation/rbdp/real_data/results/phase7_baselines_T16_32/settings.jsonl
     + phase10_baselines/settings.jsonl (4 chains) + phase10c_baselines/settings.jsonl (5 chains) (44 chains x 12 settings, T in {16,32}, B in {2,3,4}, alpha in {0.05,0.1}); per chain the max over settings.
 (b) docs/paper4_continuation/rbdp/real_data/results/phase9_replay.jsonl + phase11_msprt_replay.jsonl (P8c) (100 datasets, 9,525 windows,
     T = 32, B = 4, alpha = 0.1, c = 0.01); window bootstrap, 2,000 resamples, seed 20261119.
Asserted against phase10c_baselines/tally.json (key new) and len(make_tables.ORDER): chains violated by P3/P4/P5 and their maxima; pooled means equal Table 4 to 1e-3.
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
for r in (read_jsonl(REAL / "phase7_baselines_T16_32/settings.jsonl") + read_jsonl(REAL / "phase10_baselines/settings.jsonl")
          + read_jsonl(REAL / "phase10c_baselines/settings.jsonl")):
    p = NAMES[r["policy"]]
    worst[p][r["chain_id"]] = max(worst[p][r["chain_id"]], r["ratio_causal_over_alpha"])
chains = sorted(worst["P7"])
import json
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import make_tables as MT
TAL = json.loads((REAL / "phase10c_baselines/tally.json").read_text())["new"]
N_CH = len(chains)
assert N_CH == TAL["chains"] == len(MT.ORDER), (N_CH, TAL["chains"], len(MT.ORDER))
viol = {c for c in chains if any(worst[p][c] > 1 + 1e-9 for p in ("P3", "P4", "P5"))}
assert len(viol) == TAL["iid_break_datasets"], len(viol)
assert [round(max(worst[p].values()), 6) for p in ("P3", "P4", "P5")] == [round(TAL["max_ratio"][p], 6) for p in ("P3", "P4", "P5")]
assert max(max(worst[p].values()) for p in ("P1", "P2", "P6", "P7")) <= 1 + 1e-9

# ---- (b) replay pooled cost
rep = [r for r in read_jsonl(REAL / "phase9_replay.jsonl") if r["status"] == "replayed"]
SAFE = ["P7", "P5r", "P8c", "P2", "P3c", "P1", "P6"]
LAB = {"P7": "RB-DP", "P5r": "P5r", "P8c": "P8c", "P2": "P2", "P3c": "P3c", "P1": "P1", "P6": "P6"}
# Phase 11 calibrated mSPRT, aligned window by window with Phase 9 (same datasets; P7 costs must coincide exactly)
m11 = {r["id"]: r for r in read_jsonl(REAL / "phase11_msprt_replay.jsonl") if r["status"] == "replayed"}
for r in rep:
    assert np.array_equal(np.asarray(m11[r["id"]]["cost"]["P7"], float), np.asarray(r["cost"]["P7"], float)), r["id"]
    r["cost"]["P8c"] = m11[r["id"]]["cost"]["P8c"]
cost = {p: np.concatenate([np.asarray(r["cost"][p], float) for r in rep]) for p in SAFE + ["P4c"]}
n = len(cost["P7"]); assert n == 9525, n
TABLE4 = {"P7": 13.799, "P5r": 13.799, "P8c": 13.838, "P2": 13.838, "P3c": 13.850, "P1": 13.918, "P6": 14.173, "P4c": 15.834}
for p, v in TABLE4.items():
    assert abs(cost[p].mean() - v) < 1e-3, (p, cost[p].mean(), v)
rng = np.random.default_rng(20261119)
idx = rng.integers(0, n, size=(2000, n))
ci = {p: np.percentile(cost[p][idx].mean(axis=1), [2.5, 97.5]) for p in SAFE}

apply_style(8.5)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(WIDTH, 2.9), gridspec_kw=dict(width_ratios=[1.5, 1.0], wspace=0.3))
pols = ["P7", "P1", "P2", "P6", "P3", "P4", "P5"]
for i, p in enumerate(pols):
    y = np.array([worst[p][c] for c in chains])
    col = P["blue_main"] if p == "P7" else (P["grey"] if p in ("P1", "P2", "P6") else P["red_strong"])
    # coincident observations (same value to 1e-3 in log2) form a centred horizontal row; y stays exact
    key = np.round(np.log2(y) / 0.03).astype(int)
    xs = np.zeros(len(y)); dense = []
    for kk in np.unique(key):
        m = np.where(key == kk)[0]
        dx = min(0.07, 0.6 / max(len(m) - 1, 1))  # stack spans <= 60% of the spacing between methods
        xs[m] = (np.arange(len(m)) - (len(m) - 1) / 2) * dx
        if len(m) >= 4:
            dense.append((i, y[m].mean(), len(m)))
    a1.scatter(i + xs, y, s=6, color=col, alpha=0.85, linewidths=0, zorder=3)
    for x0, y0, cnt in dense:
        # centred above its own row (baseline 6 pt above the dot tops), unless other dots of the same column sit just
        # above the row; then the count goes to the right of the row so it cannot cover them
        crowded = np.any((y > y0 * 1.02) & (y < y0 * 2 ** 0.45))
        if crowded:
            half = (cnt - 1) / 2 * min(0.07, 0.6 / max(cnt - 1, 1))
            a1.annotate(f"{cnt}", (x0 + half, y0), xytext=(5, 0), textcoords="offset points", fontsize=7, color=col,
                        ha="left", va="center", zorder=5, bbox=dict(boxstyle="square,pad=0.14", fc="white", ec="none"))
        else:
            a1.annotate(f"{cnt}", (x0, y0), xytext=(0, 6 + 1.2), textcoords="offset points", fontsize=7, color=col,
                        ha="center", va="baseline", zorder=5,
                        bbox=dict(boxstyle="square,pad=0.14", fc="white", ec="none"))
a1.axhline(1, color=P["dark"], lw=0.8, ls=":")
a1.text(-1.7, 1.04, "budget $\\alpha$", fontsize=7, ha="left", va="bottom")
a1.set_yscale("log", base=2); a1.set_yticks([0.5, 1, 2, 4, 8]); a1.set_yticklabels(["1/2", "1", "2", "4", "8"])
a1.set_xticks(range(len(pols))); a1.set_xticklabels(pols)
a1.set_ylabel("worst adaptive risk / $\\alpha$")
a1.set_title("%d fitted chains, 12 settings each" % N_CH, loc="left", fontsize=8.5)
a1.text(5, 0.42, "i.i.d.-calibrated", fontsize=7, color=P["red_strong"], ha="center")
a1.text(1.4, 0.42, "causal-safe", fontsize=7, color=P["grey"], ha="center")
a1.set_ylim(0.38, 10); a1.set_xlim(-1.8, 6.7)

for j, p in enumerate(SAFE):
    m = cost[p].mean(); lo, hi = ci[p]
    col = P["blue_main"] if p == "P7" else P["grey"]
    a2.errorbar(m, j, xerr=[[m - lo], [hi - m]], fmt="o", color=col, ms=4.5, capsize=2.5, lw=2.0,
                mfc=col if p == "P7" else "white")
a2.axvline(cost["P7"].mean(), color=P["blue_main"], lw=1.0, ls=":")
a2.set_yticks(range(len(SAFE))); a2.set_yticklabels([LAB[p] for p in SAFE]); a2.invert_yaxis()
a2.set_xlabel("mean realised cost per window (95% bootstrap CI)")
a2.set_title("held-out replay, 9,525 windows", loc="left", fontsize=8.5)
panel_label(a1, "a", dx=-0.3, dy=1.1); panel_label(a2, "b", dx=-0.06, dy=1.1)
save(fig, "real")
print("wrote fig_real; CI:", {p: [round(x, 3) for x in ci[p]] for p in SAFE})
