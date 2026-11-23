"""Appendix figure: full per-regime exceedance heatmap and real-stream counts (all arms)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from style import PALETTE as P, WIDTH, apply_style, panel_label, save
from viol_data import *

apply_style(8)
fig = plt.figure(figsize=(WIDTH, 5.3))
gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.42, left=0.14, right=0.985, top=0.93, bottom=0.17)
ax = fig.add_subplot(gs[0]); bx = fig.add_subplot(gs[1])
cmap = LinearSegmentedColormap.from_list("w2r", ["#FFFFFF", P["red_1"], P["red_strong"], "#5E1B1A"])
im = ax.pcolormesh(np.arange(M.shape[1] + 1) - 0.5, np.arange(M.shape[0] + 1) - 0.5, M, cmap=cmap, vmin=0, vmax=1, edgecolors="face", linewidth=0.3, rasterized=False)
ax.set_xlim(-0.5, M.shape[1] - 0.5); ax.set_ylim(M.shape[0] - 0.5, -0.5)
ax.set_xticks(range(len(cols))); ax.set_xticklabels([c[2] for c in cols], fontsize=7)
ax.xaxis.tick_top(); ax.tick_params(axis="x", length=0)
lab = lambda g: g.replace("_", " ")
ax.set_yticks(range(len(order))); ax.set_yticklabels([("* " if g in stress else "") + lab(g) for g in order], fontsize=6.8)
for t, g in zip(ax.get_yticklabels(), order):
    if g in stress: t.set_color(P["red_strong"]); t.set_fontweight("bold")
ax.tick_params(axis="y", length=0, pad=2)
for s in ax.spines.values(): s.set_visible(False)
ax.axhline(len(orig) - 0.5, color=P["dark"], lw=0.8)
ax.axvline(4.5, color=P["dark"], lw=0.8)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = M[i, j]
        if v >= 0.1: ax.text(j, i, f"{v:.2f}".lstrip("0"), ha="center", va="center", fontsize=6.5, color="white" if v > 0.45 else P["dark"])
        elif j >= 5: ax.text(j, i, f"{v:.3f}".lstrip("0") if v > 0 else "0", ha="center", va="center", fontsize=6.5, color=P["dark"])
cax = fig.add_axes([0.14, 0.07, 0.3, 0.012])
cb = fig.colorbar(im, cax=cax, orientation="horizontal"); cb.set_label("exceedance rate of $R$=20 (runs above $R$ / 1,000)", fontsize=7)
cb.outline.set_visible(False); cb.solids.set_rasterized(False); cb.solids.set_edgecolor("face"); cb.ax.tick_params(labelsize=6.5, length=2)
panel_label(ax, "(a)", -0.55, 1.08)
ax.text(0.5, -0.045, "", transform=ax.transAxes)

# (b)
x = np.arange(len(conds)); w = 0.16
for i, (a, lbl, col, mk) in enumerate(rarms):
    xs = x + (i - 2) * w
    bx.vlines(xs, 0, cnt[a], color=col, lw=1.2)
    bx.scatter(xs, cnt[a], color=col, marker=mk, s=26, zorder=3, label=lbl)
    for xi, v in zip(xs, cnt[a]):
        if not v: bx.text(xi, 55, "0", ha="center", va="bottom", fontsize=7.5, color=col)
bx.set_xticks(x); bx.set_xticklabels(["clean", "adverse\ndropout", "adverse\ndelay"])
bx.set_ylabel(f"runs with harm above $R$=24 (of {tot[0]:,})")
bx.set_ylim(0, 1300); bx.set_yticks(range(0, 1201, 200)); bx.set_xlim(-0.55, 2.55)
bx.legend(loc="upper left", ncol=2, fontsize=7, bbox_to_anchor=(-0.02, 1.0), columnspacing=0.8, handletextpad=0.2, borderaxespad=0)
panel_label(bx, "(b)", -0.28, 1.06)
bx.set_title("Real streams ($R$=24)", loc="center", fontsize=8, y=1.0, pad=6)
ax.text(0.5, 1.07, "Simulation, registered run ($R$=20)", transform=ax.transAxes, ha="center", fontsize=8)
save(fig, "violations_full")
print("tot runs", tot); print({a: v for a, v in cnt.items()})
print("worst per col", dict(zip([c[0] for c in cols], M.max(0).round(3))), "pooled", dict(zip([c[0] for c in cols], M.mean(0).round(4))))
