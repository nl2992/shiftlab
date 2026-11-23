"""Appendix version of the regime map (all points, all arms). Figure 2: cost of the guarantee L against exposure ratio x = r d / h (exposure_ratio_test.json)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import ARM_STYLE, PALETTE as P, RES, WIDTH, apply_style, load_json, panel_label, save

ex = load_json(RES / "exposure_ratio_test.json")
rows = ex["rows"]
BINS = [(0.0, 0.5, "[0,0.5)"), (0.5, 1.0, "[0.5,1)"), (1.0, 2.0, "[1,2)"), (2.0, np.inf, "[2,inf)")]

apply_style(8.5)
fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 3.1), sharey=True, gridspec_kw=dict(wspace=0.06))
meds = {}
for ax, (src, title) in zip(axes, (("scarce", "Simulation (label-scarce family)"), ("real", "Real streams (clean feedback)"))):
    ax.axvspan(0.5, 1.0, color=P["neutral"], alpha=0.35, lw=0)
    ax.axvline(0.5, color=P["grey"], lw=0.9, ls=(0, (4, 2)))
    ax.axvline(1.0, color=P["grey"], lw=0.9, ls=(0, (4, 2)))
    ax.axhline(0.0, color=P["dark"], lw=0.8)
    ax.axhline(1.0, color=P["dark"], lw=0.8, ls=":")
    for arm, (lab, col, mk) in ARM_STYLE.items():
        pts = [(r["x"], r["L"]) for r in rows if r["source"] == src and r["arm"] == arm]
        x, L = np.array(pts).T
        ax.scatter(x, L, s=11, color=col, marker=mk, alpha=0.45, linewidths=0, zorder=3)
        bx, by = [], []
        for lo, hi, key in BINS:
            m = (x >= lo) & (x < hi)
            bx.append(np.exp(np.median(np.log(x[m])))); by.append(np.median(L[m]))
            meds[(src, arm, key)] = (int(m.sum()), float(np.median(L[m])))
        ax.plot(bx, by, color=col, lw=1.4, zorder=4)
        ax.scatter(bx, by, s=34, color="white", edgecolor=col, marker=mk, linewidths=1.5, zorder=5)
    ax.set_xscale("log"); ax.set_xlim(1.5e-2 if src == "scarce" else 1e-3, 12); ax.set_ylim(-0.25, 1.75)
    ax.set_title(title, loc="left", fontsize=8.5)
    ax.text(0.5, 1.68, "$x$=0.5 ", ha="right", va="center", fontsize=7.5, color=P["grey"], rotation=0)
    ax.text(1.0, 1.68, " $x$=1", ha="left", va="center", fontsize=7.5, color=P["grey"])
axes[0].set_ylabel("share of Wald's gain given up, $L$\n(0 = all kept, 1 = none kept)")
axes[0].text(1.7e-2, 1.04, "$L$=1: no gain kept", fontsize=7.5, color=P["dark"], va="bottom")
axes[0].text(11, 0.04, "$L$=0: all gain kept", fontsize=7.5, color=P["dark"], va="bottom", ha="right")
axes[1].tick_params(axis="y", left=False)
axes[1].spines["left"].set_visible(False)
handles = [Line2D([], [], color=c, marker=m, lw=1.4, ms=5, label=l) for l, c, m in ARM_STYLE.values()]
handles.append(Line2D([], [], color=P["grey"], marker="o", mfc="white", mew=1.4, lw=0, ms=6, label="open marker: median per bin of $x$"))
fig.subplots_adjust(bottom=0.27, top=0.92, left=0.1, right=0.99)
fig.text(0.545, 0.175, "exposure ratio $x=rd/h$ (disagreement rate $\\times$ label delay / headroom; log scale)", fontsize=8.5, ha="center", va="center")
fig.legend(handles=handles, loc="lower center", ncol=4, bbox_to_anchor=(0.55, 0.0), fontsize=8, columnspacing=1.6)
save(fig, "regime_map_full")
for k, v in meds.items():
    print(k, v)
for k, v in ex["summary"]["bins"].items():
    src, arm = k.split("/")
    for _, _, key in BINS:
        n, med = meds[(src, arm, key)]
        assert n == v[key]["n"] and abs(med - v[key]["median_L"]) < 1e-9, (k, key, n, med, v[key])
print("bins match exposure_ratio_test.json summary")
