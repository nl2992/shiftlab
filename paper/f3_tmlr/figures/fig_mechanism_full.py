"""Appendix figure: full detail of the mechanism tape (check line, labels in transit, deployed bars)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from style import PALETTE as P, WIDTH, apply_style, panel_label, save
from mech_data import *

apply_style(8.5)
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(WIDTH, 4.5), sharex=True, gridspec_kw=dict(height_ratios=[2.6, 1.0], hspace=0.12))
ax.axhspan(R - K, R, color=P["red_1"], alpha=0.8, lw=0)
ax.axhline(R, color=P["red_strong"], lw=1.1)
ax.axhline(R - K, color=P["red_strong"], lw=0.8, ls=(0, (3, 2)))
ax.text(T + 0.5, R, " budget $R$=20", color=P["red_strong"], va="center", fontsize=8)
ax.text(T + 0.5, R - K - 0.1, " $R-k$=17", color=P["red_strong"], va="top", fontsize=8)
ax.text(1.5, R - K / 2, "rollback reserve $k$ (the fee to undo)", color=P["red_strong"], va="center", fontsize=7.5)
ax.axhline(0, color=P["neutral"], lw=0.8)
ax.axvspan(0.5, NPLUS + 0.5, color=P["green_1"], lw=0, alpha=0.7)
ax.text(NPLUS / 2 + 0.5, 27.8, "challenger\nbetter\n($Z$=+1)", ha="center", va="top", fontsize=7.5, color=P["dark"])
ax.text(NPLUS + 1.5, 27.8, "challenger worse ($Z$=-1)", ha="left", va="top", fontsize=7.5, color=P["dark"])

ax.step(t, res["shield"]["log"]["I"], where="post", color=P["blue_secondary"], lw=1.1, ls=(0, (1, 1.2)))
ax.step(t, Hs, where="post", color=P["blue_main"], lw=1.8)
ax.step(t, Hl, where="post", color=P["red_strong"], lw=1.8, ls=(0, (5, 1.8)))
ax.plot(t[np.argmax(Hl)], Hl.max(), "o", color=P["red_strong"], ms=5, zorder=5)
ax.plot(t[np.argmax(Hs)], Hs.max(), "o", color=P["blue_main"], ms=5, zorder=5)
ax.text(NPLUS + 1.0, 27.0, "shield bound $U_t$ + reserve (dotted)", color=P["blue_secondary"], fontsize=7.5, ha="left", va="bottom") if False else None
ax.set_ylabel("harm $H_t$ (loss units)")
ax.set_ylim(-9, 29); ax.set_xlim(0.5, T)
# direct line labels
ax.text(14.0, 5.8, "shield harm $H_t$", color=P["blue_main"], fontsize=8, rotation=0, ha="left", va="bottom") if False else None
from matplotlib.lines import Line2D
ax.legend(handles=[
    Line2D([], [], color=P["blue_main"], lw=2.0, label=f"shield: harm peaks at {Hs.max():.0f} = $R$,\nrolled back at $t$={roll_s}"),
    Line2D([], [], color=P["blue_secondary"], lw=1.1, ls=(0, (1, 1.2)), label="shield's check $W_t$ (fees, reserves,\nresolved and pending harm)"),
    Line2D([], [], color=P["red_strong"], lw=1.8, ls=(0, (5, 1.8)), label=f"naive stop-loss: harm peaks at\n{Hl.max():.0f} > $R$, rolled back at $t$={roll_l}"),
], loc="lower right", fontsize=6.8, bbox_to_anchor=(1.0, 0.02), handlelength=2.6, borderaxespad=0.2, labelspacing=0.7)
panel_label(ax, "(a)", -0.07, 1.0)

# bottom: labels in transit and deployed action
ax2.step(t, res["shield"]["pend"], where="post", color=P["blue_main"], lw=1.8)
ax2.step(t, res["stop"]["pend"], where="post", color=P["red_strong"], lw=1.4, ls=(0, (5, 1.8)))
ax2.fill_between(t, 0, res["shield"]["pend"], step="post", color=P["blue_secondary"], alpha=0.18, lw=0)
for key, y, c in (("shield", -2.1, P["blue_main"]), ("stop", -3.3, P["red_strong"])):
    a = res[key]["rec"].a
    ax2.fill_between(t, y, y + 0.9, where=a == 1, step="post", color=c, lw=0)
ax2.text(T + 0.5, -1.5, " shield deployed", color=P["blue_main"], fontsize=7.5, va="center")
ax2.text(T + 0.5, -3.05, " stop-loss deployed", color=P["red_strong"], fontsize=7.5, va="center")
ax2.set_ylim(-3.8, 6.2); ax2.set_yticks([0, 2, 4])
ax2.set_ylabel("labels in\ntransit $P_t$")
ax2.set_xlabel("round $t$")
ax2.text(46.0, 3.9, f"$d$={D}: up to {int(res['shield']['pend'].max())}\nlabels in transit\n(pending reserve $P_t$)", fontsize=7.5, color=P["blue_main"], va="center")
panel_label(ax2, "(b)", -0.07, 0.96)
fig.align_ylabels([ax, ax2])
save(fig, "mechanism_full")
print("shield peak", Hs.max(), "rollback", roll_s, "| stoploss peak", Hl.max(), "rollback", roll_l,
      "| max pending", res["shield"]["pend"].max(), res["stop"]["pend"].max())
