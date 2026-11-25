"""Figure (main text): cost of the guarantee L against exposure ratio x = r d / h, as bin medians with the
interquartile range of the paced arm. All individual points are in fig_regime_map_full.py (appendix)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from style import ARM_STYLE, PALETTE as P, RES, WIDTH, apply_style, load_json, panel_label, save

ex = load_json(RES / "exposure_ratio_test.json")
rows = ex["rows"]
BINS = [(0.0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, np.inf)]
DIRECT = {"f3_pi1": ("full sampling", (6, 14)), "f3v2d": ("paced", (6, -16)), "v3": ("v3", (6, 2))}

apply_style(8.5)
fig, axes = plt.subplots(1, 2, figsize=(WIDTH, 2.75), sharey=True, gridspec_kw=dict(wspace=0.08, left=0.1, right=0.985, top=0.9, bottom=0.2))
for ax, (src, title) in zip(axes, (("scarce", "Simulation (label-scarce family)"), ("real", "Real streams, clean feedback"))):
    ax.axvspan(0.5, 1.0, color=P["neutral"], alpha=0.35, lw=0)
    ax.axhline(0.0, color=P["dark"], lw=0.8)
    ax.axhline(1.0, color=P["dark"], lw=0.8, ls=":")
    for arm, (lab, col, mk) in ARM_STYLE.items():
        x, L = np.array([(r["x"], r["L"]) for r in rows if r["source"] == src and r["arm"] == arm]).T
        bx, med, lo, hi = [], [], [], []
        for a, b in BINS:
            m = (x >= a) & (x < b)
            bx.append(np.exp(np.median(np.log(x[m])))); med.append(np.median(L[m]))
            lo.append(np.percentile(L[m], 25)); hi.append(np.percentile(L[m], 75))
        if arm == "f3v2d":
            ax.fill_between(bx, lo, hi, color=col, alpha=0.16, lw=0)
        ax.plot(bx, med, color=col, lw=1.8, marker=mk, ms=5.5, mfc="white", mew=1.5, zorder=4)
    ax.set_xscale("log"); ax.set_xlim(1.5e-2, 12); ax.set_ylim(-0.1, 1.35)
    ax.set_title(title.lower(), loc="left", fontsize=8, pad=8, family=["Courier New","Menlo","DejaVu Sans Mono"], fontweight="bold")
    panel_label(ax, "a" if src == "scarce" else "b", -0.0, 1.12)
    ax.text(0.71, 1.3, "$0.5\\leq x<1$", ha="center", va="center", fontsize=7.5, color=P["grey"])
    ax.set_xlabel("exposure ratio $x = rd/h$")
axes[0].set_ylabel("share of Wald's gain given up, $L$")
axes[1].text(1e-3*1.3, 1.03, "none kept", fontsize=7.5, va="bottom", color=P["dark"])
axes[1].text(1e-3*1.3, 0.03, "all kept", fontsize=7.5, va="bottom", color=P["dark"])
axes[1].tick_params(axis="y", left=False); axes[1].spines["left"].set_visible(False)
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
hs = [Line2D([], [], color=c, marker=m, mfc="white", mew=1.4, lw=1.6, ms=5, label=l) for l, c, m in ARM_STYLE.values()]
hs.append(Patch(color=ARM_STYLE["f3v2d"][1], alpha=0.25, label="paced, interquartile range"))
axes[1].legend(handles=hs, loc="center left", bbox_to_anchor=(0.0, 0.47), fontsize=7.2, handlelength=1.6, borderaxespad=0.3, labelspacing=0.3)
axes[0].text(0.017, 1.03, "none kept", fontsize=7.5, va="bottom", color=P["dark"], alpha=0) 
save(fig, "regime_map")
