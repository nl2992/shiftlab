"""Figure 4: the value W_X(1, beta_1, n, w) is piecewise linear in the risk budget w with breakpoints on {k/2^n}.

Computed with the lattice solver (src/shiftlab/paper4/risk_budget_dp_fast.py, lattice_exact=True) on one small cell:
T = 6, B = 3, transition 19/20 in both directions, emission e = 1/50, alpha = 1/10 (so N = 10 * 2^3 = 80 risk steps),
n_beta = 401, c = k = 0. The y-axis is the value of information C0 - W (cost saved against never promoting).
Asserts: every kink of every plotted curve lies on the dyadic grid {k/2^n}.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from style import PALETTE as P, WIDTH, apply_style, panel_label, save

import lattice_data as LD

res, N, C0 = LD.get()
B = LD.B
w = np.arange(N + 1) / N

apply_style(8.5, axes_linewidth=1.3)  # design-theory rcParams (axes 2.5, font 16) at half scale for single-column width
fig, axes = plt.subplots(1, 3, figsize=(WIDTH, 2.5), sharex=False, gridspec_kw=dict(wspace=0.36))
nb = {}
for ax, n in zip(axes, range(1, B + 1)):
    for k in range(2 ** n + 1):
        ax.axvline(k / 2 ** n, color=P["neutral"], lw=0.7, alpha=0.55, zorder=0)
    vi, vc = C0 - res["iid"][1][n], C0 - res["causal"][1][n]
    ax.fill_between(w, vc, vi, color=P["red_1"], lw=0, zorder=1, label="premium")
    for mode, col, ls, v in (("iid", P["red_strong"], "-", vi), ("causal", P["blue_main"], "--", vc)):
        ax.plot(w, v, color=col, ls=ls, lw=1.9, zorder=3, label="i.i.d." if mode == "iid" else "adaptive")
        j = LD.kinks(res[mode][1][n])
        pts = j / N
        # every kink must sit on the dyadic grid {k / 2^n}
        assert np.all(np.abs(pts * 2 ** n - np.round(pts * 2 ** n)) < 1e-9), (mode, n, pts)
        nb[(mode, n)] = pts
        if mode == "causal":  # open markers: white face, 1.5 pt outline
            ax.scatter(pts, v[j], s=22, facecolor="white", zorder=4, edgecolor=col, lw=1.5)
        else:
            ax.scatter(pts, v[j], s=22, color=col, zorder=4, edgecolor="black", lw=0.9)
    assert len(nb[("iid", n)]) >= 1
    ax.set_xticks([k / 2 ** n for k in range(2 ** n + 1)] if n < 3 else [0, 0.25, 0.5, 0.75, 1])
    ax.set_xticklabels([(f"{k}/{2 ** n}" if k % 2 else f"{k // 2}/{2 ** (n - 1)}") if 0 < k < 2 ** n else str(k // 2 ** n) for k in range(2 ** n + 1)]
                       if n < 3 else ["0", "1/4", "1/2", "3/4", "1"])
    ax.set_title(f"$n={n}$ label{'' if n == 1 else 's'} left", loc="left", fontsize=8.5, color=P["dark"])
    ax.set_xlim(0, 1); ax.set_ylim(0, 2.1)  # common range; data max is 2.0025 (n=3)
    ax.set_yticks([0, 0.5, 1, 1.5, 2]); ax.set_yticklabels(["0", "0.5", "1", "1.5", "2"])
    if n > 1:
        ax.tick_params(axis="y", labelleft=True)
    panel_label(ax, "abc"[n - 1], dx=-0.27, dy=1.02)
axes[0].set_ylabel("value of information $C_0-W_X$")
axes[1].set_xlabel("risk budget $w$ (grey: grid $k/2^n$)")
h, l = axes[0].get_legend_handles_labels()
order = [l.index("i.i.d."), l.index("adaptive")]
axes[0].legend([h[i] for i in order], [l[i] for i in order], loc="upper right", fontsize=8, handlelength=2.0)
vi3, vc3 = C0 - res["iid"][1][3], C0 - res["causal"][1][3]
k = int(round(0.5 * N)); lo, hi = sorted((vc3[k], vi3[k]))
axes[2].plot([0.5, 0.5], [lo, hi], color=P["red_strong"], lw=1.6, zorder=3.5, solid_capstyle="butt")
for yy in (lo, hi):
    axes[2].plot([0.5 - 0.02, 0.5 + 0.02], [yy, yy], color=P["red_strong"], lw=1.6, zorder=3.5, solid_capstyle="butt")
# at the midpoint the label would straddle the i.i.d. curve, so it hugs the bracket's upper end (still left, 6 pt gap)
axes[2].annotate("premium", (0.5, hi), xytext=(-6, 1), textcoords="offset points", fontsize=8,
                 color=P["red_strong"], fontweight="bold", va="bottom", ha="right")
print("premium at w=1/2, n=3:", lo, hi)
save(fig, "lattice")
print({k: [round(x, 4) for x in v] for k, v in nb.items()})
print("wrote fig_lattice")
