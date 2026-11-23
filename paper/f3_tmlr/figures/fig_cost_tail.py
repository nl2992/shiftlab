"""Figure (main text): cost against tail risk at the default budget R=20 (registered run, descriptive).
The panels for R=12 (with the ablations) and R=30 are in fig_cost_tail_full.py (appendix)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from style import PALETTE as P, RES, WIDTH, apply_style, load_json, save

desc = load_json(RES / "confirm_summary.json")["descriptive"]
R = 20
OTHER = {"wald_cut": "Wald cutoff", "cusum": "CUSUM", "gate_wald": "e-process gate", "cusum_rb_h4": "CUSUM rb 4", "cusum_rb_h8": "CUSUM rb 8"}
apply_style(8.5)
fig, ax = plt.subplots(figsize=(WIDTH * 0.72, 2.9))
ax.axvspan(-3, R, color=P["green_1"], alpha=0.6, lw=0)
ax.axvline(R, color=P["dark"], lw=1.0)
ax.text(R - 0.7, 71.95, "$q_{99}\\leq R$: budget met", ha="right", va="top", fontsize=7.5, color="#3E5A2A")
for a in OTHER:
    ax.scatter(desc[a]["sup_q99"], desc[a]["J"], s=26, marker="o", facecolor="none", edgecolor=P["red_2"], linewidths=1.1, zorder=2)
ax.text(33.0, 71.62, "other comparators\n(no budget)", fontsize=7.5, color=P["red_strong"], ha="center", va="top", alpha=0.9)
ax.scatter(0, desc["never"]["J"], s=44, marker="X", color=P["grey"], zorder=3)
ax.annotate("never switch", (0, desc["never"]["J"]), xytext=(7, 0), textcoords="offset points", fontsize=7.5, color=P["grey"], va="center")
for a, lab, dx, dy, ha in (("f3_pi1_R20", "shield (full)", 7, 5, "left"), ("f3v2d_R20", "paced", -7, 6, "right"), ("f3v2_R20_blind8", "blind-8", -7, -6, "right")):
    d = desc[a]
    ax.scatter(d["sup_q99"], d["J"], s=52, marker="s", color=P["blue_main"], zorder=4)
    ax.annotate(lab, (d["sup_q99"], d["J"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=8, color=P["blue_main"])
d = desc["stoploss_R20"]
ax.scatter(d["sup_q99"], d["J"], s=52, marker="o", facecolor="white", edgecolor=P["red_strong"], linewidths=1.8, zorder=4)
ax.annotate("stop-loss", (d["sup_q99"], d["J"]), xytext=(-8, -6), textcoords="offset points", ha="right", va="center", fontsize=8, color=P["red_strong"])
ax.set_xlim(-2, 40); ax.set_ylim(68.4, 72.1)
ax.set_xlabel("99th percentile of maximum harm (loss units)"); ax.set_ylabel("mean cost $J$ per episode")
ax.set_title("cost against tail harm, R = 20", loc="left", fontsize=8, pad=6, family=["Courier New","Menlo","DejaVu Sans Mono"], fontweight="bold")
fig.subplots_adjust(left=0.13, right=0.985, top=0.9, bottom=0.17)
save(fig, "cost_tail")
