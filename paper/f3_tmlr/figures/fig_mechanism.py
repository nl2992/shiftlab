"""Figure (main text): the mechanism tape, reduced to the two harm curves and the budget. The check line, labels in
transit and deployed bars are in fig_mechanism_full.py (appendix). The chart is pasted into the generated frame by
compose_composites.py; numbered badges 1 and 2 match the callouts in the frame."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from style import PALETTE as P, apply_style
from mech_data import *  # noqa: F401,F403  (t, T, R, K, NPLUS, D, Hs, Hl, roll_s, roll_l, res)

apply_style(8.5)
fig, ax = plt.subplots(figsize=(5.4, 2.75))
ax.axvspan(0.5, NPLUS + 0.5, color=P["green_1"], lw=0, alpha=0.8)
ax.text(NPLUS / 2 + 0.5, 30, "challenger\nbetter", ha="center", va="top", fontsize=7.5, color="#3E5A2A")
ax.axhline(0, color=P["neutral"], lw=0.8)
ax.axhline(R, color=P["dark"], lw=1.1, ls=(0, (5, 2)))
ax.text(1.0, R + 0.7, "budget $R$ = 20", fontsize=8, color=P["dark"], va="bottom")
ax.step(t, Hl, where="post", color=P["red_strong"], lw=2.0)
ax.step(t, Hs, where="post", color=P["blue_main"], lw=2.4)
ts, tl = int(t[np.argmax(Hs)]), int(t[np.argmax(Hl)])
ax.plot(ts, Hs.max(), "o", color=P["blue_main"], ms=6, zorder=5)
ax.plot(tl, Hl.max(), "o", color=P["red_strong"], ms=6, zorder=5)
ax.annotate(f"shield rolls back at $t$ = {roll_s}\npeak harm {Hs.max():.0f}", (ts, Hs.max()), xytext=(-12, 20), textcoords="offset points",
            ha="right", va="bottom", fontsize=8, color=P["blue_main"],
            arrowprops=dict(arrowstyle="-", color=P["blue_main"], lw=0.8, shrinkA=2, shrinkB=4))
ax.annotate(f"stop-loss rolls back at $t$ = {roll_l}\npeak harm {Hl.max():.0f}", (tl, Hl.max()), xytext=(8, 5), textcoords="offset points",
            ha="left", va="bottom", fontsize=8, color=P["red_strong"])
# numbered badges matching the callouts
for (x, y, n, c) in ((ts - 19.0, 26.6, "1", P["blue_main"]), (tl + 0.2, Hl.max() + 3.2, "2", P["red_strong"])):
    ax.text(x, y, n, ha="center", va="center", fontsize=7.5, color="white", fontweight="bold",
            bbox=dict(boxstyle="circle,pad=0.25", fc=c, ec="none"), zorder=6)
ax.set_xlim(0.5, T); ax.set_ylim(-9, 31)
ax.set_xlabel("round $t$"); ax.set_ylabel("cumulative harm $H_t$")
ax.set_yticks([0, 10, 20, 30])
fig.subplots_adjust(left=0.13, right=0.985, top=0.97, bottom=0.2)
fig.savefig(Path(__file__).resolve().parent / "assets_raw" / "panel_mechanism.png", dpi=400, transparent=True, bbox_inches="tight", pad_inches=0.03)
plt.close(fig)
print("shield", Hs.max(), roll_s, "stop", Hl.max(), roll_l)
