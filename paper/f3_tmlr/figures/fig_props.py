"""Propositions: (a) attainment of floor(R-2k) (props_check.json prop3), (b) ruin bound vs simulated frequency (prop4)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from style import PALETTE as P, RES, WIDTH, apply_style, load_json, panel_label, save

pc = load_json(RES / "props_check.json")
p3, p4 = pc["prop3"], pc["prop4"]
assert all(r["attains"] and r["first_spell"] == r["floor_R_minus_2k"] for r in p3)
NRUN = 2000  # runs per cell (main.tex appendix: Proposition 4 check)

apply_style(8.5)
fig, (ax, bx) = plt.subplots(1, 2, figsize=(WIDTH, 3.1), gridspec_kw=dict(wspace=0.32))
dcol = {1: P["blue_main"], 3: P["teal"], 5: P["violet"], 10: "#E08E45"}
dmk = {1: "o", 3: "s", 5: "^", 10: "D"}
# (a): jitter x slightly by d so the four d values per R stay visible
ax.plot([0, 16], [0, 16], color=P["grey"], lw=0.9, ls=(0, (4, 2)), zorder=1)
off = {1: -0.9, 3: -0.3, 5: 0.3, 10: 0.9}
for d in (1, 3, 5, 10):
    rr = [r for r in p3 if r["d"] == d]
    ax.scatter([r["floor_R_minus_2k"] + off[d] for r in rr], [r["first_spell"] for r in rr], s=26, color=dcol[d],
               marker=dmk[d], zorder=3, label=f"$d$={d}", linewidths=0)
ax.set_xlim(0, 16); ax.set_ylim(0, 16)
ax.set_xlabel("$\\lfloor R-2k\\rfloor$ (most any valid controller can hold)")
ax.set_ylabel("shield's first-spell length\n(exposed rounds)")
ax.set_xticks([2, 6, 14]); ax.set_yticks([2, 6, 14])
ax.legend(loc="upper left", ncol=2, fontsize=7.5, handletextpad=0.1, columnspacing=0.8)
ax.text(15.8, 0.5, "all 12 cells on the line", fontsize=7, color=P["dark"], ha="right", va="bottom")
ax.text(2, 4.2, "$R$=8", fontsize=6.5, color=P["grey"], ha="center"); ax.text(6, 8.2, "$R$=12", fontsize=6.5, color=P["grey"], ha="center")
ax.text(14, 16.1, "$R$=20", fontsize=6.5, color=P["grey"], ha="center", va="bottom", clip_on=False)
panel_label(ax, "(a)", -0.2, 1.04)
# (b)
floor = 1.0 / NRUN / 2
for d in (1, 5):
    rr = [r for r in p4 if r["d"] == d]
    x = np.array([r["bound_ruin"] for r in rr]); y = np.array([r["forced_frac"] for r in rr])
    zero = y == 0
    bx.scatter(x[~zero], y[~zero], s=24, color=dcol[d], marker=dmk[d], linewidths=0, zorder=3, label=f"$d$={d}")
    bx.scatter(x[zero], np.full(zero.sum(), floor), s=24, facecolor="white", edgecolor=dcol[d], marker=dmk[d], linewidths=1.0, zorder=3)
bx.plot([1e-9, 2], [1e-9, 2], color=P["grey"], lw=0.9, ls=(0, (4, 2)), zorder=1)
bx.set_xscale("log"); bx.set_yscale("log"); bx.set_xlim(1e-9, 2); bx.set_ylim(floor * 0.5, 1.2)
bx.set_xlabel("ruin bound on first-spell exit"); bx.set_ylabel("simulated forced-rollback frequency")
bx.set_xticks([1e-8, 1e-6, 1e-4, 1e-2, 1]); bx.set_yticks([1e-3, 1e-2, 1e-1, 1])
bx.text(1.5e-9, floor * 0.62, "open: 0 of 2000 runs", fontsize=6.3, color=P["grey"], va="bottom")
bx.text(0.02, 0.2, "$y=x$", fontsize=7, color=P["grey"], rotation=38, ha="center", va="bottom")
bx.legend(loc="lower right", fontsize=7.5, handletextpad=0.1, bbox_to_anchor=(1.0, 0.1))
panel_label(bx, "(b)", -0.2, 1.04)
save(fig, "props")
print("prop3 cells", len(p3), "prop4 cells", len(p4), "floor", floor)
for d in (1, 5):
    rr = [r for r in p4 if r["d"] == d and r["forced_frac"] > 0 and r["bound_ruin"] < 1]
    print(d, "ratio sim/bound median", np.median([r["forced_frac"] / r["bound_ruin"] for r in rr]), "n", len(rr))
print("above bound:", [(r["p"], r["d"], r["R"], r["forced_frac"], round(r["bound_ruin"], 5)) for r in p4 if r["forced_frac"] > r["bound_ruin"]])
print("d=1 p=.6 R=10", [(r["forced_frac"], r["bound_ruin"]) for r in p4 if r["d"] == 1 and r["p"] == 0.6 and r["R"] == 10])
