"""Main-text mechanism figure, built as ONE canvas in the figures4papers 'miscellaneous' style: the real harm curves with
annotations drawn directly on them (pale tinted callouts with bold coloured keywords, a dark-red highlight frame,
curved arrows) and flat line-art icons (generated, assets_raw/icons2_sheet.png). No pasted chart box, no banner.
Data come from mech_data.py (committed code run on the tape)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from style import PALETTE as P, apply_style, save
from schematic import CALLOUT, MONO, arrow, callout, cut_sheet, frame, paste, rich
from mech_data import *  # noqa: F401,F403

HERE = Path(__file__).resolve().parent
apply_style(8)
W, H = 6.5, 3.55
fig = plt.figure(figsize=(W, H), dpi=300)
ov = fig.add_axes([0, 0, 1, 1], zorder=5)           # overlay in inch coordinates
ov.set_xlim(0, W); ov.set_ylim(0, H); ov.axis("off"); ov.patch.set_alpha(0)
CX, CY, CW, CH = 0.62, 0.5, 5.8, 2.52               # chart rectangle (inches)
ax = fig.add_axes([CX / W, CY / H, CW / W, CH / H])
X0, X1, Y0, Y1 = 0.5, 60.0, -13.0, 35.0
ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1)
px = lambda t: CX + (t - X0) / (X1 - X0) * CW        # data -> inches
py = lambda y: CY + (y - Y0) / (Y1 - Y0) * CH

# ---- the data
ax.axhline(0, color=P["neutral"], lw=0.8, zorder=1)
ax.axhline(R, color=P["dark"], lw=0.9, ls=(0, (5, 2.5)), zorder=2)
kd = int(np.argmax(np.asarray(Hs) != np.asarray(Hl)))       # first round where the two controllers differ
ax.step(t[:kd + 1], Hs[:kd + 1], where="post", color="#34383C", lw=2.2, zorder=3)
ax.step(t[kd:], Hl[kd:], where="post", color=P["red_strong"], lw=2.2, zorder=3)
ax.step(t[kd:], Hs[kd:], where="post", color=P["blue_main"], lw=2.2, zorder=4)
ts, tl = int(t[np.argmax(Hs)]), int(t[np.argmax(Hl)])
ax.plot(ts, Hs.max(), "o", color=P["blue_main"], ms=5.5, zorder=5)
ax.plot(tl, Hl.max(), "o", color=P["red_strong"], ms=5.5, zorder=5)
ax.set_yticks([0, 10, 20, 30]); ax.set_xticks([10, 20, 30, 40, 50, 60])
ax.set_xlabel("round $t$", labelpad=2); ax.set_ylabel("cumulative harm $H_t$", labelpad=2)
ax.text(X0 + 1, R + 0.8, "budget $R$ = 20", ha="left", va="bottom", fontsize=7.5, color=P["dark"])

icons = cut_sheet(HERE / "assets_raw" / "icons2_sheet.png", rows=1, cols=4)
robot, envelope, shield, stop = icons

# ---- title (bold monospace, as in the references)
ov.text(0.05, H - 0.2, "two controllers, one outcome sequence", family=MONO, fontsize=10, fontweight="bold", ha="left", va="center")

# ---- challenger-better: a shallow strip along the bottom of the opening interval
ov.add_patch(FancyBboxPatch((px(0.5), py(-13.0)), px(NPLUS + 0.5) - px(0.5), 0.2, boxstyle="square,pad=0", fc="#E8F0E5", ec="none", zorder=1))
ov.text((px(0.5) + px(NPLUS + 0.5)) / 2, py(-13.0) + 0.1, "challenger better", ha="center", va="center", fontsize=6.6, color="#3F7F3B", fontweight="bold")

# ---- the five pending labels, drawn: a white card with five envelopes, leader to the shield's stopping round
cw, ch = 2.3, 0.62
cx0, cy0 = px(ts) - cw - 0.35, py(Hs.max()) + 0.42
ov.add_patch(FancyBboxPatch((cx0, cy0), cw, ch, boxstyle="round,pad=0,rounding_size=0.07", fc="white", ec="#34383C", lw=0.8, zorder=6))
rich(ov, cx0 + 0.12, cy0 + ch - 0.14, [(f"At round {ts}", dict(weight="bold"))], fs=6.8)
for i in range(5):
    ex, ey = cx0 + 0.14 + i * 0.26, cy0 + 0.2
    ov.add_patch(FancyBboxPatch((ex, ey), 0.2, 0.14, boxstyle="round,pad=0,rounding_size=0.015", fc="white", ec="#34383C", lw=0.8, zorder=7))
    ov.plot([ex, ex + 0.1, ex + 0.2], [ey + 0.14, ey + 0.07, ey + 0.14], color="#34383C", lw=0.7, zorder=7)
rich(ov, cx0 + 1.5, cy0 + 0.27, [("5 labels", dict(weight="bold", color="#A57B0B")), (" pending", {})], fs=6.4)
arrow(ov, (cx0 + cw, cy0 + 0.08), (px(ts) - 0.03, py(Hs.max()) + 0.07), color="#34383C", lw=0.8, ms=6)

# ---- overshoot, measured on the plot: a bracket between the budget and the stop-loss plateau
bxp = px(tl + 1.3)
ov.plot([bxp - 0.04, bxp, bxp, bxp - 0.04], [py(R), py(R), py(Hl.max()), py(Hl.max())], color="#8B1E1E", lw=1.1, zorder=7)
ov.text(bxp + 0.06, py(0.5 * (R + Hl.max())), f"+{Hl.max() - R:.0f}", color="#8B1E1E", fontsize=8, fontweight="bold", va="center", ha="left")

# ---- endpoint labels: method names in bold mono, times in sans, two aligned columns
lx = px(43.5)
ov.text(lx, py(Hl.max()) + 0.14, "STOP-LOSS", family=MONO, fontsize=8, fontweight="bold", color=P["red_strong"], va="bottom", ha="left")
ov.text(lx + 0.72, py(Hl.max()) + 0.14, f"rollback $t$ = {roll_l}", fontsize=6.6, color=P["dark"], va="bottom", ha="left")
ov.text(lx, py(R) - 0.12, "SHIELD", family=MONO, fontsize=8, fontweight="bold", color=P["blue_main"], va="top", ha="left")
ov.text(lx + 0.72, py(R) - 0.12, f"rollback $t$ = {roll_s}", fontsize=6.6, color=P["dark"], va="top", ha="left")
paste(ov, shield, lx - 0.16, py(R) - 0.2, 0.2)

fig.savefig(HERE / "fig_mechanism.pdf", dpi=300)
fig.savefig(HERE / "fig_mechanism.png", dpi=300)
plt.close(fig)
print("scene ok", Hs.max(), roll_s, Hl.max(), roll_l)
