"""Schematic (no data): the problem (delayed or missing labels, fees) and the shield's check W_t against R."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from style import PALETTE as P, WIDTH, apply_style, save

AMBER = "#E08E45"
apply_style(8)
fig, ax = plt.subplots(figsize=(WIDTH, 3.5))
ax.set_xlim(0, 84); ax.set_ylim(-3.1, 6.6); ax.axis("off")

# ---- timeline of rounds ----
N, W, X0, Y0, H = 21, 3.6, 4.0, 0.0, 1.0
PROMO, ROLL, D, T_CHECK, NEVER = 4, 16, 3, 13, 7
cx = lambda i: X0 + (i - 1) * 4.0
for i in range(1, N + 1):
    exposed = PROMO <= i < ROLL
    ax.add_patch(Rectangle((cx(i), Y0), W, H, fc=P["blue_secondary"] if exposed else P["neutral"], ec="white", lw=0.8, zorder=2))
    ax.text(cx(i) + W / 2, Y0 + H / 2, str(i) if i in (1, PROMO, T_CHECK, ROLL, N) else "", ha="center", va="center", fontsize=6.5,
            color="white" if exposed else P["dark"], zorder=3)
ax.text(cx(1) - 0.3, Y0 + H + 0.25, "rounds $t$", fontsize=7, color=P["grey"], ha="left", va="bottom")
ax.text(cx(2) + W / 2, Y0 + H + 0.25, "incumbent", fontsize=7.5, color=P["grey"], ha="center", va="bottom")
ax.text(cx(19) + W / 2, Y0 + H + 0.25, "incumbent", fontsize=7.5, color=P["grey"], ha="center", va="bottom")
ax.text((cx(PROMO) + cx(ROLL - 1) + W) / 2 + 6.5, Y0 + H + 0.25, "challenger deployed (exposed rounds)", fontsize=7.5,
        color=P["blue_main"], ha="center", va="bottom") if False else None
# fee markers
for i, lab, dx in ((PROMO, "promotion\nfee $k$", 0), (ROLL, "rollback\nfee $k$", 0)):
    ax.annotate(lab, (cx(i) + W / 2 + (-W / 2 if i == PROMO else W / 2), Y0 + H), xytext=(cx(i) + W / 2, Y0 + H + 1.5),
                ha="center", va="bottom", fontsize=7, color=P["red_strong"],
                arrowprops=dict(arrowstyle="-|>", color=P["red_strong"], lw=1.0, shrinkA=0, shrinkB=0, mutation_scale=7))
ax.text(cx(PROMO + 2) + W / 2, Y0 - 0.35, "exposed: challenger acts, labels requested", fontsize=7, color=P["blue_main"], ha="left", va="top") if False else None
# label requests -> releases
for s in range(PROMO, ROLL - 1):
    r = s + D
    pend = r > T_CHECK and s < T_CHECK
    col = AMBER if pend else P["grey"]
    if s == NEVER:
        a = FancyArrowPatch((cx(s) + W / 2, Y0), (cx(s) + W / 2 + 4.8, Y0 - 1.55), connectionstyle="arc3,rad=0.25", arrowstyle="-",
                            color=P["red_strong"], lw=1.0, ls=(0, (2, 1.5)))
        ax.add_patch(a)
        ax.text(cx(s) + W / 2 + 5.4, Y0 - 1.75, "$\\times$", color=P["red_strong"], fontsize=10, ha="center", va="center", fontweight="bold")
        continue
    if s >= T_CHECK: continue
    ax.add_patch(FancyArrowPatch((cx(s) + W / 2, Y0), (cx(r) + W / 2, Y0), connectionstyle="arc3,rad=0.35", arrowstyle="-|>",
                                 mutation_scale=6, color=col, lw=0.9, shrinkA=1, shrinkB=1, zorder=1))
ax.text(cx(NEVER) + W / 2 + 7.6, Y0 - 1.7, "label never arrives", fontsize=7, color=P["red_strong"], ha="left", va="center")
ax.text(cx(PROMO) + 0.2, Y0 - 2.05, "label requested", fontsize=7, color=P["grey"], ha="left", va="top") if False else None
ax.text(cx(1) - 0.3, Y0 - 2.7, "arrows: label requested at the arrow's start, released $d$ rounds later "
        "(grey: released before round $t$; amber: still in transit at $t$)", fontsize=6.8, color=P["grey"], ha="left", va="center")
# check marker on the timeline
ax.plot([cx(T_CHECK) + W / 2] * 2, [Y0 + H, 2.9], color=P["dark"], lw=0.9, ls=(0, (2, 2)), zorder=1)
ax.text(cx(T_CHECK) + W / 2, Y0 + H + 0.05, "", fontsize=6)

# ---- the check W_t as a stacked bar ----
BY, BH = 3.1, 1.15
segs = [("fees paid\n$kN$", 11, P["blue_main"]), ("rollback\nreserve $k$", 6, P["teal"]), ("resolved\nharm $A$", 14, P["blue_secondary"]),
        ("labels in\ntransit $P$", 13, AMBER), ("this\nround", 6, P["red_2"]), ("width\n$D_\\delta$", 9, P["neutral"])]
x = 6.0
for lab, w, c in segs:
    ax.add_patch(Rectangle((x, BY), w, BH, fc=c, ec="white", lw=0.8, zorder=2))
    ax.text(x + w / 2, BY + BH + 0.2, lab, ha="center", va="bottom", fontsize=7, color=P["dark"], linespacing=0.95)
    x += w
R_X = 72.0
ax.plot([R_X, R_X], [BY - 0.35, BY + BH + 0.35], color=P["red_strong"], lw=1.6)
ax.text(R_X + 0.9, BY + BH / 2, "budget $R$", color=P["red_strong"], fontsize=8, va="center", ha="left", fontweight="bold")
ax.text(5.5, BY + BH / 2, "check\n$W_t$", ha="right", va="center", fontsize=8, color=P["blue_main"], fontweight="bold")
ax.annotate("", (R_X - 0.4, BY - 0.55), (x, BY - 0.55), arrowprops=dict(arrowstyle="<->", color=P["grey"], lw=0.8, shrinkA=0, shrinkB=0))
ax.text((x + R_X) / 2, BY - 0.75, "slack", fontsize=6.5, color=P["grey"], ha="center", va="top")
ax.text(46, 6.35, "deploy the challenger in round $t$ only if $W_t\\le R$; otherwise stay with (or roll back to) the incumbent",
        fontsize=7.8, color=P["dark"], ha="center", va="center")
save(fig, "overview")
