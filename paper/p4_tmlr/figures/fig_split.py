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
apply_style(8.5)
fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.9), sharey=True, gridspec_kw=dict(wspace=0.12))

iid = [(0, 0), (2 * W, 0), (0, 2 * W)]
causal = [(0, 0), (W, 0), (W, W), (0, 2 * W)]
borrow = (0.45, 0.15)  # feasible under i.i.d., infeasible under adaptive (w0 > w')

for ax, poly, title in ((axes[0], iid, "i.i.d. null:  $(w_0+w_1)/2 \\leq w'$"),
                        (axes[1], causal, "adaptive null:  also $w_0 \\leq w'$")):
    if ax is axes[1]:
        ax.add_patch(Polygon(iid, closed=True, facecolor=P["red_1"], edgecolor="none", alpha=0.9))
    col_face = P["neutral"] if ax is axes[0] else P["blue_secondary"]
    ax.add_patch(Polygon(poly, closed=True, facecolor=col_face, edgecolor=P["dark"], lw=1.0,
                         alpha=0.55 if ax is axes[1] else 0.6))
    ax.plot([0, 0.7], [0, 0.7], color=P["grey"], lw=0.8, ls=":")
    ax.text(0.62, 0.66, "$w_0=w_1$", fontsize=7.5, color=P["grey"], ha="right")
    ax.set_xlim(0, 0.7); ax.set_ylim(0, 0.7)
    ax.set_xticks([0, W, 2 * W]); ax.set_xticklabels(["0", "$w'$", "$2w'$"])
    ax.set_yticks([0, W, 2 * W]); ax.set_yticklabels(["0", "$w'$", "$2w'$"])
    ax.set_aspect("equal")
    ax.set_title(title, loc="left", fontsize=8.5)

axes[0].set_ylabel("$w_1$: risk budget after $Y=1$")
axes[0].scatter(*borrow, s=30, color=P["dark"], zorder=5)
axes[0].annotate("borrowing: $w_0>w'$\nallowed when the\nbranches are averaged", xy=borrow, xytext=(0.36, 0.42),
                 fontsize=7.5, bbox=dict(fc="white", ec="none", pad=1),
                 arrowprops=dict(arrowstyle="->", lw=0.8, color=P["dark"]))
axes[1].scatter(*borrow, s=30, facecolor="white", edgecolor=P["red_strong"], lw=1.3, zorder=5)
axes[1].annotate("forbidden: the null can\nforce $Y=0$ by setting $p=0$", xy=borrow, xytext=(0.33, 0.42),
                 fontsize=7.5, color=P["red_strong"], bbox=dict(fc="white", ec="none", pad=1),
                 arrowprops=dict(arrowstyle="->", lw=0.8, color=P["red_strong"]))
axes[1].text(0.47, 0.05, "lost region:\nthe premium's source", fontsize=7.5, color=P["red_strong"], ha="center")
axes[1].tick_params(axis="y", left=False)
panel_label(axes[0], "a", dx=-0.18); panel_label(axes[1], "b", dx=-0.06)
fig.text(0.5, -0.02, "$w_0$: risk budget after a label favouring the incumbent ($Y=0$)", ha="center", fontsize=8.5)
save(fig, "split")
print("wrote fig_split")
