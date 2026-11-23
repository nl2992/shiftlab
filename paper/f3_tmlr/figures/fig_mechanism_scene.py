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
X0, X1, Y0, Y1 = 0.5, 60.0, -9.0, 35.0
ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1)
px = lambda t: CX + (t - X0) / (X1 - X0) * CW        # data -> inches
py = lambda y: CY + (y - Y0) / (Y1 - Y0) * CH

# ---- the data
ax.axvspan(X0, NPLUS + 0.5, color="#E3F1E1", lw=0, zorder=0)
ax.axhline(0, color=P["neutral"], lw=0.8, zorder=1)
ax.axhline(R, color=P["dark"], lw=1.0, ls=(0, (5, 2.5)), zorder=2)
ax.step(t, Hl, where="post", color=P["red_strong"], lw=2.0, zorder=3)
ax.step(t, Hs, where="post", color=P["blue_main"], lw=2.4, zorder=4)
ts, tl = int(t[np.argmax(Hs)]), int(t[np.argmax(Hl)])
ax.plot(ts, Hs.max(), "o", color=P["blue_main"], ms=6, zorder=5)
ax.plot(tl, Hl.max(), "o", color=P["red_strong"], ms=6, zorder=5)
ax.set_yticks([0, 10, 20, 30]); ax.set_xticks([10, 20, 30, 40, 50, 60])
ax.set_xlabel("round $t$", labelpad=2); ax.set_ylabel("cumulative harm $H_t$", labelpad=2)
ax.text(X1, R - 1.0, "budget $R$ = 20", ha="right", va="top", fontsize=7.5, color=P["dark"])

icons = cut_sheet(HERE / "assets_raw" / "icons2_sheet.png", rows=1, cols=4)
robot, envelope, shield, stop = icons

# ---- title and panel-free labels, in the reference's bold monospace
ov.text(0.05, H - 0.2, "one tape, two controllers", family=MONO, fontsize=10.5, fontweight="bold", ha="left", va="center")
rich(ov, 0.05, H - 0.43, [("Only the ", {}), ("shield", dict(weight="bold", color=P["blue_main"])),
                          (" stops at the budget.", {})], fs=8)

# ---- challenger-better band
paste(ov, robot, px(5.5), py(30.2), 0.3)
ov.text(px(5.5), py(24.6), "challenger\nbetter", ha="center", va="center", fontsize=6.6, color="#3F7F3B", fontweight="bold", linespacing=1.0)

# ---- late labels (envelope) callout, upper middle
bx, by, bw, bh = px(14.5), py(25.0), 2.1, 0.55
ov.add_patch(FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0,rounding_size=0.07", fc=CALLOUT["gold"][0], ec="none", zorder=2))
paste(ov, envelope, bx + 0.3, by + bh / 2, 0.34)
rich(ov, bx + 0.55, by + bh / 2 + 0.075, [("Labels arrive ", {}), ("five rounds", dict(weight="bold", color="#A57B0B"))], fs=6.8)
rich(ov, bx + 0.55, by + bh / 2 - 0.075, [("late, so recent harm is ", {}), ("unseen", dict(weight="bold", color="#A57B0B")), (".", {})], fs=6.8)

# ---- shield callout, lower right, with a curved arrow to the rollback point
sx, sy, sw, sh = px(39.6), py(1.5), 1.95, 0.78
ov.add_patch(FancyBboxPatch((sx, sy), sw, sh, boxstyle="round,pad=0,rounding_size=0.07", fc=CALLOUT["blue"][0], ec="none", zorder=2))
paste(ov, shield, sx + 0.27, sy + sh / 2, 0.36)
rows = [[("The shield ", {}), ("books the 5 labels", dict(weight="bold", color=P["blue_main"]))],
        [("in transit as possible harm", {})],
        [("and rolls back at ", {}), (f"t = {roll_s}", dict(weight="bold", color=P["blue_main"])), (".", {})]]
for i, r_ in enumerate(rows):
    rich(ov, sx + 0.5, sy + sh / 2 + 0.15 - i * 0.15, r_, fs=6.2)
arrow(ov, (sx + 0.12, sy + sh + 0.02), (px(ts) + 0.02, py(Hs.max()) - 0.09), color=P["blue_main"], lw=1.0, rad=0.0, ms=7)

# ---- stop-loss callout, top right, red highlight frame on the overshoot
rx, ry, rw, rh = px(39.6), py(28.3), 1.95, 0.56
ov.add_patch(FancyBboxPatch((rx, ry), rw, rh, boxstyle="round,pad=0,rounding_size=0.07", fc=CALLOUT["red"][0], ec="none", zorder=2))
paste(ov, stop, rx + 0.27, ry + rh / 2, 0.36)
rich(ov, rx + 0.5, ry + rh / 2 + 0.075, [("The stop-loss ", {}), ("ignores", dict(weight="bold", color=P["red_strong"])), (" unseen", {})], fs=6.2)
rich(ov, rx + 0.5, ry + rh / 2 - 0.075, [("labels and ", {}), ("overshoots the budget", dict(weight="bold", color=P["red_strong"])), (".", {})], fs=6.2)
frame(ov, px(tl) - 0.14, py(R) - 0.05, 0.28 + 0.0, py(Hl.max()) - py(R) + 0.13, color="#8B1E1E", lw=1.5, r=0.06, zorder=7)
ov.text(px(tl) + 0.2, py(0.5 * (R + Hl.max())), f"+{Hl.max() - R:.0f}", color="#8B1E1E", fontsize=7.5, fontweight="bold", va="center", ha="left")
ov.text(px(tl) + 0.2, py(0.5 * (R + Hl.max())) - 0.0, "", fontsize=1)
ov.text(px(tl) + 0.55, py(Hl.max()) - 0.12, f"rolls back at $t$ = {roll_l}", color=P["red_strong"], fontsize=6.6, va="top", ha="left")

fig.savefig(HERE / "fig_mechanism.pdf", dpi=300)
fig.savefig(HERE / "fig_mechanism.png", dpi=300)
plt.close(fig)
print("scene ok", Hs.max(), roll_s, Hl.max(), roll_l)
