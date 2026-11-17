"""Per-stream comparison on the 14 real streams, clean feedback (outputs/paper3/riskbudget/real/clean/*.json)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import OUT, PALETTE as P, WIDTH, apply_style, load_json, panel_label, save

HARMFUL = ["airlines", "bank"]
BEN = ["criteo", "elec2", "openml_ldpa", "rialto", "spam", "uci_occupancy", "weather", "appliances",
       "beijing_pm25", "bike_hour", "household_power", "metro"]
# arm -> (label, colour, marker, own budget R)
ARMS = {"wald_cut": ("Wald cutoff", P["red_strong"], "o", 24), "stoploss_h14": ("stop-loss", "#E08E45", "v", 24),
        "f3_pi1_h14": ("shield full, $h$=14", P["blue_main"], "s", 24), "f3v2d_h50": ("shield paced, $h$=50", P["teal"], "^", 60)}
data = {}
for s in HARMFUL + BEN:
    d = load_json(OUT / "real/clean" / f"{s}.json")
    J = np.array(d["fields"]["J"], float); sh = np.array(d["fields"]["sup_harm"], float)
    jn = J[d["arms"].index("never")].mean()
    data[s] = {a: ((J[d["arms"].index(a)].mean() - jn) / jn * 100, sh[d["arms"].index(a)].max()) for a in ARMS}
    data[s]["never_J"] = jn
order = HARMFUL + sorted(BEN, key=lambda s: data[s]["f3_pi1_h14"][0])
ypos = {}; y = 0
for i, s in enumerate(order):
    if i == len(HARMFUL): y += 0.7
    ypos[s] = y; y += 1

apply_style(8)
fig, (ax, bx) = plt.subplots(1, 2, figsize=(WIDTH, 4.1), sharey=True, gridspec_kw=dict(width_ratios=[1.6, 1], wspace=0.06))
ax.axvline(0, color=P["dark"], lw=0.9)
ax.axhspan(-0.5, len(HARMFUL) - 0.5, color=P["red_1"], alpha=0.35, lw=0)
for a, (lab, col, mk, R) in ARMS.items():
    ax.scatter([data[s][a][0] for s in order], [ypos[s] for s in order], color=col, marker=mk, s=22, zorder=4, label=lab)
    bx.scatter([data[s][a][1] / R for s in order], [ypos[s] for s in order], color=col, marker=mk, s=22, zorder=4)
ax.set_xscale("symlog", linthresh=10, linscale=0.8)
ax.set_xlim(-120, 40)
ax.set_xticks([-100, -50, -10, 0, 10, 30]); ax.set_xticklabels(["$-100$", "$-50$", "$-10$", "0", "10", "30"])
ax.set_yticks([ypos[s] for s in order]); ax.set_yticklabels([s.replace("_", " ") for s in order], fontsize=7)
ax.invert_yaxis(); ax.tick_params(axis="y", length=0)
ax.set_xlabel("cost relative to never switching,\n$100\\,(J-J_{never})/J_{never}$ (%; left = better)")
ax.set_title("Cost per stream", loc="left", fontsize=8.5)
ax.text(0.99, 0.99, "harmful streams shaded", transform=ax.transAxes, ha="right", va="top", fontsize=6.5, color=P["red_strong"])
bx.axvline(1.0, color=P["red_strong"], lw=1.0)
bx.set_xscale("log"); bx.set_xlim(0.15, 40)
bx.text(1.1, -0.9, "budget", color=P["red_strong"], fontsize=7, va="center")
bx.set_ylim(len(order) + 0.5, -1.3); bx.tick_params(axis="y", left=False)
bx.spines["left"].set_visible(False)
bx.set_xlabel("worst sup-harm / own budget $R$\n(log; right of 1 = violation)")
bx.set_title("Budget use", loc="left", fontsize=8.5)
bx.set_xticks([0.3, 1, 3, 10, 30]); bx.set_xticklabels(["0.3", "1", "3", "10", "30"])
bx.minorticks_off()
fig.subplots_adjust(left=0.15, right=0.99, top=0.9, bottom=0.24)
fig.legend(handles=[Line2D([], [], color=c, marker=m, lw=0, ms=5, label=l) for l, c, m, _ in ARMS.values()],
           loc="lower center", ncol=4, bbox_to_anchor=(0.55, -0.01), fontsize=7.5, columnspacing=1.2, handletextpad=0.2)
save(fig, "real_streams")
for s in order: print(s, {a: tuple(round(v, 2) for v in data[s][a]) for a in ARMS})
print("max ratio per arm", {a: round(max(data[s][a][1] / ARMS[a][3] for s in order), 3) for a in ARMS})
