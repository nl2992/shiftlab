"""Appendix version (all three budgets and the ablations). Figure 4: mean cost J vs 99th percentile of sup-harm, all arms of the registered run (confirm_summary.json, descriptive).
One panel per budget R; arms without a budget (comparators, never) are repeated faintly in every panel."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import PALETTE as P, RES, WIDTH, apply_style, load_json, save

desc = load_json(RES / "confirm_summary.json")["descriptive"]
# arm -> (label, family, (dx, dy, ha)) ; family: sh shield, st stop-loss, abl ablation
PANELS = {
    12: {"f3_pi1_R12": ("full", "sh", (-6, 5, "right")), "stoploss_R12": ("stop-loss", "st", (0, 13, "center")),
         "f3_pi1_R12_nopending": ("no pending", "abl", (-6, 7, "right")), "f3_pi1_R12_norollback": ("no rollback", "abl", (6, 11, "left")),
         "f3_pi25_R12_noconf": ("no width", "abl", (0, -10, "center"))},
    20: {"f3_pi1_R20": ("full", "sh", (6, 4, "left")), "f3v2d_R20": ("paced", "sh", (-6, 6, "right")),
         "f3v2_R20_blind8": ("blind-8", "sh", (-6, -6, "right")), "stoploss_R20": ("stop-loss", "st", (-7, -9, "right"))},
    30: {"f3_pi1_R30": ("full", "sh", (-6, 5, "right")), "f3v2d_R30": ("paced", "sh", (-6, -7, "right")),
         "stoploss_R30": ("", "st", (0, 0, "left"))},
}
NOBUD = ["wald_cut", "cusum", "gate_wald", "cusum_rb_h4", "cusum_rb_h8"]
COL = {"sh": P["blue_main"], "st": P["red_strong"], "abl": P["violet"]}
MK = {"sh": "s", "st": "o", "abl": "^"}
assert set(desc) == set(NOBUD) | {"never"} | {a for p in PANELS.values() for a in p}

apply_style(8.5)
fig, axes = plt.subplots(1, 3, figsize=(WIDTH, 3.1), sharey=True, gridspec_kw=dict(wspace=0.08, left=0.1, right=0.99, top=0.88, bottom=0.2))
for k, (ax, (R, arms)) in enumerate(zip(axes, PANELS.items())):
    ax.axvspan(-3, R, color=P["green_1"], alpha=0.55, lw=0)
    ax.axvline(R, color=P["dark"], lw=1.0)
    ax.set_title(f"budget $R$ = {R}", loc="left", fontsize=8.5)
    for a in NOBUD:
        ax.scatter(desc[a]["sup_q99"], desc[a]["J"], s=22, marker="o", facecolor="none", edgecolor=P["red_2"], linewidths=1.0, zorder=2)
    ax.scatter(0, desc["never"]["J"], s=34, marker="X", color=P["grey"], zorder=2)
    for a, (lab, fam, (dx, dy, ha)) in arms.items():
        d = desc[a]; ok = d["sup_q99"] <= R
        ax.scatter(d["sup_q99"], d["J"], s=40, marker=MK[fam], edgecolor=COL[fam], facecolor=COL[fam] if ok else "white", linewidths=1.4, zorder=4)
        if lab: ax.annotate(lab, (d["sup_q99"], d["J"]), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center", fontsize=7.5, color=COL[fam])
    ax.set_xlim(-2, 40); ax.set_ylim(68.2, 72.1)
    ax.set_xlabel("$q_{99}$ of sup-harm (loss units)")
axes[0].set_ylabel("mean cost $J$ (per episode)")
for ax in axes[1:]: ax.tick_params(axis="y", left=False); ax.spines["left"].set_visible(False)
axes[0].annotate("never\nswitch", (0, desc["never"]["J"]), xytext=(6, 0), textcoords="offset points", fontsize=7.5, color=P["grey"], va="center", ha="left")
handles = [Line2D([], [], marker="s", color=P["blue_main"], lw=0, ms=6, label="shield"),
           Line2D([], [], marker="o", color=P["red_strong"], lw=0, ms=6, label="stop-loss"),
           Line2D([], [], marker="^", color=P["violet"], lw=0, ms=6, label="ablation"),
           Line2D([], [], marker="o", mfc="none", mec=P["red_2"], lw=0, ms=6, label="other comparator"),
           Line2D([], [], marker="o", mfc="white", mec=P["dark"], lw=0, ms=6, label="open: $q_{99}>R$")]
fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.55, -0.03), fontsize=7.5, columnspacing=1.2, handletextpad=0.2)
save(fig, "cost_tail_full")
