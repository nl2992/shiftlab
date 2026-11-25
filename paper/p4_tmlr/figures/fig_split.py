"""Figure 1: the query-branch constraint on the two child risk budgets (w0, w1) given a parent budget w'.

Conceptual figure, no data. I.i.d. null: (w0 + w1)/2 <= w'. Adaptive null adds w0 <= w' (Corollary 1).
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from style import PALETTE as P, WIDTH, apply_style, panel_label, save

W = 0.3  # parent budget w'
apply_style(8.5, axes_linewidth=0.9)
fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.9), sharey=True, gridspec_kw=dict(wspace=0.12))

iid = [(0, 0), (2 * W, 0), (0, 2 * W)]
causal = [(0, 0), (W, 0), (W, W), (0, 2 * W)]
borrow = (0.45, 0.15)  # feasible under i.i.d., infeasible under adaptive (w0 > w')

RET, REM = "#CFE3F6", P["red_1"]
RED = "#B64342"
for ax, poly, title in ((axes[0], iid, "i.i.d. null:  $(w_0+w_1)/2 \\leq w^{\\prime}$"),
                        (axes[1], causal, "adaptive null:  also $w_0 \\leq w^{\\prime}$")):
    if ax is axes[1]:
        ax.add_patch(Polygon(iid, closed=True, facecolor=REM, edgecolor="none"))
    ax.add_patch(Polygon(poly, closed=True, facecolor=RET, edgecolor=P["dark"], lw=0.9))
    ax.plot([0, 0.7], [0, 0.7], color=P["grey"], lw=0.8, ls=":")
    ax.text(0.62, 0.66, "$w_0=w_1$", fontsize=7.5, color=P["grey"], ha="right")
    ax.set_xlim(0, 0.7); ax.set_ylim(0, 0.7)
    ax.set_xticks([0, W, 2 * W]); ax.set_xticklabels(["0", "$w^{\\prime}$", "$2w^{\\prime}$"])
    ax.set_yticks([0, W, 2 * W]); ax.set_yticklabels(["0", "$w^{\\prime}$", "$2w^{\\prime}$"])
    ax.set_aspect("equal")
    ax.set_title(title, loc="left", fontsize=8.5, pad=3)

axes[0].set_ylabel("$w_1$ after $Y=1$")
axes[0].scatter(*borrow, s=30, color=P["dark"], zorder=5)
axes[0].text(0.47, 0.215, "$(1.5w^{\\prime}, 0.5w^{\\prime})$", fontsize=7.5, va="bottom")
axes[0].text(0.47, 0.155, "Average = $w^{\\prime}$", fontsize=7.5, va="bottom")
axes[1].scatter(*borrow, s=30, facecolor="white", edgecolor=RED, lw=1.3, zorder=5)
axes[1].plot([W, W], [0, W], color=RED, lw=2.0, zorder=4, solid_capstyle="butt")
axes[1].text(W - 0.015, 0.5 * W, "$w_0=w^{\\prime}$", fontsize=7.5, color=RED, ha="right", va="center")
axes[1].text(0.47, 0.215, "$p=0$ forces\n$Y=0$", fontsize=7.5, color=RED, va="bottom", linespacing=1.1)
axes[1].text(0.405, 0.045, "Excluded\nsplits", fontsize=7, color=RED, ha="center", va="center", linespacing=1.05)
axes[1].tick_params(axis="y", left=False)
for ax, s in zip(axes, "ab"):
    panel_label(ax, s, dx=-0.02, dy=1.1)
fig.text(0.5, -0.09, "$w_0$ after $Y=0$", ha="center", fontsize=8.5)
save(fig, "split")
print("wrote fig_split")
