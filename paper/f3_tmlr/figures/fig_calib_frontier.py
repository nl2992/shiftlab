"""Calibration frontiers of the two budget-aware comparators against the shield (calib_summary.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import PALETTE as P, RES, WIDTH, apply_style, load_json, panel_label, save

c = load_json(RES / "calib_summary.json")
cal, arms = c["calibration"]["calibration"], c["sim"]["arms"]
J_never = arms["never"]["J"]
STOP, CUS = "#E08E45", P["red_strong"]
ANN = {"stoploss_cal": {12: [6, 9], 20: [13, 14, 15], 30: [24, 27]},
       "cusumrb_cal": {12: [0.5, 2], 20: [0.5, 2], 30: [0.5, 2]}}

apply_style(8.5)
fig, axes = plt.subplots(1, 3, figsize=(WIDTH, 3.0), sharey=True, gridspec_kw=dict(wspace=0.08))
for ax, R in zip(axes, (12, 20, 30)):
    ax.axhline(0.05, color=P["grey"], lw=0.9, ls=(0, (4, 2)))
    ax.axvline(J_never, color=P["dark"], lw=0.9, ls=":")
    for key, col, mk, nm in (("stoploss_cal", STOP, "v", "c"), ("cusumrb_cal", CUS, "D", "theta_c")):
        fr = cal[f"R{R}"][key]["frontier"]
        x = [f["pooled_J"] for f in fr]; y = [f["worst_viol"] for f in fr]
        ax.plot(x, y, color=col, lw=1.2, marker=mk, ms=3.2, zorder=3)
        for f in fr:
            if f["value"] in ANN[key][R]:
                v = f["value"]; lab = f"{v:g}"
                if key == "cusumrb_cal":
                    dx, dy, ha = (3, 2, "left")
                else:
                    dx, dy, ha = (-3, 3, "right") if v < R / 2 else (3, 3, "left")
                if key == "stoploss_cal" and f["worst_viol"] == 0: dy = 14
                ax.annotate(lab, (f["pooled_J"], f["worst_viol"]), xytext=(dx, dy), textcoords="offset points",
                            fontsize=6.5, color=col, ha=ha, va="bottom")
        ch = arms[f"{key}_R{R}"]
        ax.scatter(ch["J"], ch["violation"]["worst_stats"]["rate"], s=36, facecolor="white", edgecolor=col, marker=mk,
                   linewidths=1.3, zorder=5)
    sh = arms[f"f3_pi1_R{R}"]
    assert sh["violation"]["worst_stats"]["rate"] == 0.0
    ax.scatter(sh["J"], 0.0, s=60, color=P["blue_main"], marker="o", zorder=6, clip_on=False)
    ax.text(sh["J"], 0.1, "shield", color=P["blue_main"], fontsize=7.5, ha="center", va="bottom", fontweight="bold") if R == 12 else None
    ax.set_xlim(67.5, 87); ax.set_ylim(-0.04, 1.0)
    ax.set_title(f"$R$={R}", loc="left", fontsize=8.5)
    ax.set_xticks([70, 75, 80, 85])
axes[0].set_ylabel("worst-regime violation rate")
axes[1].set_xlabel("pooled cost $J$ (lower is better)")
for a in axes[1:]: a.tick_params(axis="y", left=False); a.spines["left"].set_visible(False)
axes[0].text(87, 0.065, "standard .05", fontsize=6.5, color=P["grey"], ha="right", va="bottom")
axes[0].text(J_never + 0.25, 0.9, "never\nswitch", fontsize=6.5, color=P["dark"], va="top")
h = [Line2D([], [], color=STOP, marker="v", ms=4, lw=1.2, label="stop-loss, margin $c$"),
     Line2D([], [], color=CUS, marker="D", ms=4, lw=1.2, label="CUSUM rollback, threshold $\theta_c$"),
     Line2D([], [], color=P["grey"], marker="o", mfc="white", mew=1.3, lw=0, ms=5.5, label="calibrated choice, fresh seeds"),
     Line2D([], [], color=P["blue_main"], marker="o", lw=0, ms=6, label="shield, fresh seeds")]
fig.subplots_adjust(left=0.085, right=0.99, top=0.9, bottom=0.3)
fig.legend(handles=h, loc="lower center", ncol=2, bbox_to_anchor=(0.54, -0.02), fontsize=7.5, columnspacing=1.5)
save(fig, "calib_frontier")
for R in (12, 20, 30):
    print(R, "shield J", round(arms[f"f3_pi1_R{R}"]["J"], 2), "stop fresh", round(arms[f"stoploss_cal_R{R}"]["J"], 2),
          "cus fresh", round(arms[f"cusumrb_cal_R{R}"]["J"], 2), arms[f"cusumrb_cal_R{R}"]["violation"]["worst_stats"]["rate"])
    for key in ("stoploss_cal", "cusumrb_cal"):
        fr = cal[f"R{R}"][key]["frontier"]; print(" ", key, "min viol with J<=never:", min([f["worst_viol"] for f in fr if f["pooled_J"] <= J_never] or [None]),
              "min J among viol<=.05:", min([f["pooled_J"] for f in fr if f["worst_viol"] <= 0.05] or [None]))
print("never J", J_never)
