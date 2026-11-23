"""Figure 1 (teaser), in the illustrated style of the figures4papers composites (see STYLE_SPEC.md).

(a) rounds as token-like cells, pending labels as '?' cells, a zoom cone into the shield's check W_t (stacked cells);
(b) data: worst-regime exceedance of R=20 per arm, from results/riskbudget/confirm_summary.json, asserted against
tables/numbers.tex. Everything else is drawn; sizes in (a) are illustrative.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from schematic import (OUTLINE, arrow, banner, block_arrow, callout, canvas, cell, finish, frame, icon_clock, icon_coin,
                       inset, load_icon, cut_sheet, paste, bubble, macros, mono, panel, rich, tag, zoom_cone)
from style import PALETTE as P, RES, WIDTH, apply_style, load_json, save

HERE = Path(__file__).resolve().parent
M = macros(HERE.parent / "tables/numbers.tex")
apply_style(8)
ICONS = cut_sheet(HERE / "assets_raw/icons_sheet.png")  # incumbent, challenger, shield, envelope (Codex image generation)
W, H = WIDTH, 3.78
fig, ax = canvas(W, H)

# --------------------------------------------------------------------------- banner
banner(ax, 0.28, 3.46, 6.18, 0.27,
       [("Labels arrive late, so part of the harm of a switch is ", {}), ("still unseen", dict(weight="bold", color=P["red_strong"])),
        (".", {})], fs=7.8)
tag(ax, 0.06, 3.58, "a")
tag(ax, 4.12, 3.2, "b")

# --------------------------------------------------------------------------- (a) rounds, deployment, labels
X0, CW, GAP = 1.42, 0.19, 0.036
step = CW + GAP
cx = lambda i: X0 + (i - 1) * step
rows = {"t": 2.9, "dep": 2.52, "lab": 2.2}
N, PROMO, ROLL, NOW = 11, 4, 11, 10
mono(ax, 1.3, rows["t"] + 0.085, "round t", fs=6.3, ha="right")
paste(ax, ICONS[1], 0.62, rows["dep"] + 0.15, 0.4)       # challenger
paste(ax, ICONS[3], 0.62, rows["lab"] + 0.02, 0.26)      # label in the mail
bubble(ax, 0.2, 3.1, 0.86, 0.27, tail=(0.62, 2.9), fill="white", lw=0.8)
mono(ax, 0.63, 3.235, "switch now?", fs=5.6, ha="center")
CH = 0.17
for i in range(1, N + 1):
    cell(ax, cx(i), rows["t"], CW, CH, "#EEEEEE", grad=("#F7F7F7", "#DADADA"), zorder=3)
    ax.text(cx(i) + CW / 2, rows["t"] + CH / 2, str(i), fontsize=5.5, ha="center", va="center", color=P["grey"], zorder=6)
    if PROMO <= i < ROLL:
        cell(ax, cx(i), rows["dep"], CW, CH, "", grad=("#BBD3EF", "#3775BA"), zorder=3)
    else:
        cell(ax, cx(i), rows["dep"], CW, CH, "white", zorder=3)
    if PROMO <= i < ROLL:
        if i <= NOW - 3:   # label already back
            cell(ax, cx(i), rows["lab"], CW, CH, "", grad=("#3775BA", "#0F4D92"), zorder=3)
        else:              # still in transit
            cell(ax, cx(i), rows["lab"], CW, CH, "white", ec=P["blue_secondary"], ls=(0, (2, 1.4)), zorder=3)
            ax.text(cx(i) + CW / 2, rows["lab"] + CH / 2 - 0.004, "?", fontsize=6.5, ha="center", va="center",
                    color=P["blue_main"], fontweight="bold", zorder=6)
ax.text(cx(1) + 1.5 * step, rows["dep"] + CH + 0.075, "incumbent", fontsize=6.2, ha="center", color=P["grey"], style="italic")
ax.text((cx(PROMO) + cx(ROLL - 1) + CW) / 2, rows["dep"] + CH + 0.075, "challenger deployed", fontsize=6.2, ha="center",
        color=P["blue_main"], style="italic")
icon_coin(ax, cx(PROMO) + CW / 2, rows["t"] + CH + 0.14, 0.065)
icon_coin(ax, cx(ROLL) + CW / 2, rows["t"] + CH + 0.14, 0.065)
ax.plot([cx(NOW) + CW + GAP / 2] * 2, [rows["lab"] - 0.05, rows["t"] + CH + 0.03], color=P["red_strong"], lw=0.9, ls=(0, (2, 1.5)), zorder=6)
mono(ax, cx(NOW) + CW + GAP / 2 + 0.03, rows["lab"] - 0.095, "now", fs=5.8, color=P["red_strong"])
yb = rows["lab"] - 0.12
ax.text((cx(PROMO) + cx(NOW - 3) + CW) / 2, yb, "seen", fontsize=6.2, ha="center", va="center", color=P["blue_main"], style="italic")
icon_clock(ax, cx(NOW - 2) + 0.02, yb, 0.055)
ax.text(cx(NOW - 2) + 0.1, yb, "in transit", fontsize=6.2, ha="left", va="center", color=P["blue_main"], style="italic")

# --------------------------------------------------------------------------- zoom into the check W_t
LX, LY, LW_, LH = 0.2, 0.42, 3.72, 1.42
panel(ax, LX, LY, LW_, LH, fill="white", lw=0.9, zorder=1.8, shadow=True)
paste(ax, ICONS[2], LX + 0.2, LY + LH - 0.19, 0.27)
mono(ax, LX + 0.4, LY + LH - 0.19, "the shield's check W_t, made before each round", fs=6.8, weight="bold")
segs = [("fees", 0.46, ("#F4F4F4", "#D5D5D5"), P["dark"]), ("rollback\nreserve", 0.44, ("#F9D9D6", "#E9A6A1"), P["red_strong"]),
        ("seen\nharm", 0.5, ("#8DB4E2", "#3775BA"), P["blue_main"]), ("in transit,\nworst case", 0.78, ("#E4EEF9", "#C7DBF2"), P["blue_main"]),
        ("this\nround", 0.24, ("#FBE7D2", "#F0C493"), "#B5651D"), ("width", 0.26, ("#EBDDF0", "#D5B9DE"), P["violet"])]
bx, by, bh = LX + 0.18, LY + 0.62, 0.3
x = bx
inx = None
for lab, w, g, tc in segs:
    cell(ax, x, by, w, bh, "", grad=g, r=0.03, zorder=3, ec=OUTLINE, lw=0.7)
    ax.text(x + w / 2, by - 0.12, lab, fontsize=6.1, ha="center", va="center", color=tc, linespacing=1.05, zorder=6)
    if lab.startswith("in transit"):
        inx = (x, w)
    x += w
frame(ax, inx[0] - 0.015, by - 0.03, inx[1] + 0.03, bh + 0.06, lw=1.3, r=0.04)
RXp = bx + 3.05
ax.plot([RXp, RXp], [by - 0.07, by + bh + 0.1], color=P["red_strong"], lw=1.3, ls=(0, (3, 1.6)), zorder=6)
rich(ax, RXp, by + bh + 0.2, [("budget ", {}), ("R", dict(weight="bold", color=P["red_strong"]))], fs=6.3, ha="center")
callout(ax, LX + 0.18, LY + 0.06, LW_ - 0.36, 0.2, [[("Deploy", True), (" only if ", False), ("W$_t$ $\\leq$ R", True),
                                                      ("; otherwise ", False), ("roll back", True), (".", False)]], tint="green", fs=6.3)
zoom_cone(ax, (cx(NOW - 2), rows["lab"] - 0.17, cx(NOW) + CW, rows["lab"] - 0.17), (LX + 0.05, LY + LH, LX + LW_ - 0.05, LY + LH), alpha=0.16)

# --------------------------------------------------------------------------- (b) data: exceedance in the worst regime
conf = load_json(RES / "confirm_summary.json")
c3, c1, c2 = conf["C3"]["arms"], conf["C1"]["arms"], conf["C2"]["arms"]
bars = [("Wald cutoff", c3["wald_cut"], "r"), ("CUSUM", c3["cusum"], "r"), ("e-process gate", c3["gate_wald"], "r"),
        ("CUSUM rollback", c3["cusum_rb_h8"], "r"), ("stop-loss (told R)", c3["stoploss_R20"], "r"),
        ("shield, full", c1["f3_pi1_R20"], "b"), ("shield, paced", c2["f3v2d_R20"], "b")]
vals = [max(r["rate"] for r in a["per_regime"].values()) for _, a, _ in bars]
assert abs(vals[0] - float(M["WorstWald"])) < 1e-3 and abs(vals[4] - float(M["WorstStop"])) < 1e-3
mono(ax, 4.38, 3.2, "budget exceedance", fs=7, weight="bold")
ax.text(4.38, 3.03, "share of runs above R=20, worst regime", fontsize=6.2, color=P["grey"], style="italic", va="center")
axc = inset(fig, W, H, 4.72, 0.52, 1.6, 2.32)
yy = list(range(len(bars)))[::-1]
for yi, (lab, a, k), v in zip(yy, bars, vals):
    col = P["red_strong"] if k == "r" else P["blue_main"]
    axc.barh(yi, v, color=col, height=0.62, edgecolor=OUTLINE, linewidth=0.6)
    axc.text(v + 0.03, yi, f"{v:.3f}".lstrip("0") if v else "0", va="center", fontsize=6.4, color=col, fontweight="bold" if k == "b" else "normal")
axc.set_yticks(yy)
axc.set_yticklabels([b[0] for b in bars], fontsize=6.4)
axc.set_xlim(0, 1.2)
axc.set_ylim(-0.6, len(bars) - 0.4)
axc.set_xticks([0, .5, 1])
axc.tick_params(axis="x", labelsize=6.2, length=3)
axc.tick_params(axis="y", length=0)
axc.spines["left"].set_linewidth(1.0)
axc.spines["bottom"].set_linewidth(1.0)
axc.text(0.52, 1.0, "never above R\nunder full sampling", fontsize=6.2, color=P["blue_main"], fontweight="bold", ha="center", va="center",
         linespacing=1.15)

# --------------------------------------------------------------------------- takeaway block arrow
block_arrow(ax, 0.2, 0.02, 6.2, 0.34, c0="#EAF1FA", c1="#6F9ED3", head=0.3)
rich(ax, 3.1, 0.19, [("The shield keeps the realised harm ", {}), ("inside the budget", dict(weight="bold", color=P["blue_main"])),
                     (" where heuristic controllers do not.", {})], fs=7.4, ha="center")
finish(ax)
save(fig, "overview")
print("wrote fig_overview", [round(v, 3) for v in vals])
