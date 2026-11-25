"""Figure 2: relative premium rho_Gamma(T) by label budget B, three anti-persistent chains.

Source: docs/paper4_continuation/rbdp/results/e2e3_fast_cells.jsonl (lattice solver, n_beta = 401,
alpha = 1/10, e = 1/10, c = k = 0, d = 1). Values asserted against Table 2 of the paper.
"""
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from style import PALETTE as P, RBDP, WIDTH, apply_style, panel_label, read_jsonl, save

rows = [r for r in read_jsonl(RBDP / "results/e2e3_fast_cells.jsonl")
        if r.get("kind") == "E3" and r.get("e") == "1/10" and r.get("n_beta") == 401]
curves = defaultdict(dict)
for r in rows:
    curves[(r["t"], r["B"])][r["T"]] = r["rho_Gamma"]

# Check against the paper's Table 2 (largest horizon run).
TABLE2 = {("2/3", 1): 0.3333, ("2/3", 6): 0.1404, ("3/4", 3): 0.1000, ("3/4", 6): 0.3034,
          ("9/10", 2): 0.0526, ("9/10", 6): 0.2762, ("3/4", 7): 0.3680}
for key, val in TABLE2.items():
    T_last = 200 if key[0] == "3/4" and key[1] <= 5 else 100
    T_last = max(T for T in curves[key] if T <= T_last)
    assert abs(curves[key][T_last] - val) < 6e-5, (key, T_last, curves[key][T_last], val)

cmap = LinearSegmentedColormap.from_list("b", [P["blue_secondary"], P["blue_main"], P["dark"]])
apply_style(8.5)
fig, axes = plt.subplots(2, 3, figsize=(WIDTH, 4.3), sharex=True, sharey=True, gridspec_kw=dict(wspace=0.08, hspace=0.12))
XMAX = 3.5 * (200 / 3.5) ** (1 / 0.72)  # data end (T=200) at 72% of the axis; right 16%+ holds labels
XL = 3.5 * (XMAX / 3.5) ** 0.86
SEP = 0.062  # > one 7 pt text line in data units
for i, t in enumerate(("2/3", "3/4", "9/10")):
    allB = sorted(B for (tt, B) in curves if tt == t)
    for row, Bs in enumerate(([B for B in allB if B <= 4], [B for B in allB if B >= 5])):
        ax = axes[row, i]
        ends = []
        for B in Bs:
            T = sorted(curves[(t, B)]); y = [curves[(t, B)][x] for x in T]
            col = cmap((B - 1) / 7)
            ax.plot(T, y, color=col, lw=2.2, marker="o", ms=3.5)
            ends.append([y[-1], T[-1], B, col])
        ends.sort()
        ly = [e[0] for e in ends]  # label heights: spread so each endpoint keeps its own label
        for j in range(1, len(ly)):
            ly[j] = max(ly[j], ly[j - 1] + SEP)
        for (yv, Tl, B, col), yl in zip(ends, ly):
            ax.plot([Tl * 1.1, XL / 1.1], [yv, yl], color=col, lw=0.8, clip_on=False)
            ax.text(XL, yl, f"$B={B}$", fontsize=7, color=col, va="center")
        ax.set_xscale("log"); ax.set_xlim(3.5, XMAX); ax.set_ylim(0, 0.66)
        ax.set_xticks([4, 16, 64, 256]); ax.set_xticklabels(["4", "16", "64", "256"])
        if row == 0:
            r = 2 * eval(t) - 1
            ax.set_title(f"$\\eta={t}$  ($r={r:.2g}$)", loc="left", fontsize=8.5)
            panel_label(ax, "abc"[i], dx=-0.2 if i == 0 else -0.1, dy=1.14)
        if row == 1:
            ax.set_xlabel("horizon $T$ (log scale)")
        if i:
            ax.tick_params(axis="y", left=False); ax.spines["left"].set_visible(False)
        if i == 2:
            ax.text(0.98, 0.97, "$B\\leq4$" if row == 0 else "$B\\geq5$", transform=ax.transAxes, ha="right", va="top",
                    fontsize=7.5, color=P["grey"])
fig.supylabel("relative premium $\\rho_\\Gamma$", fontsize=8.5, x=0.02)
save(fig, "premium")
print("wrote fig_premium;", len(rows), "cells")
