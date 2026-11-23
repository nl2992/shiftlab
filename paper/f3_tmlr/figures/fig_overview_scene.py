"""Figure 1 (overview), built as ONE canvas in the figures4papers 'miscellaneous' style: flat line-art icons
(assets_raw/icons2_sheet.png), round strip drawn from cells, a translucent zoom cone into the shield's check, a dark-red
highlight frame, pale tinted callouts with bold keywords, and the exceedance bars drawn on the same canvas from the result
files (values asserted against tables/numbers.tex)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from schematic import CALLOUT, MONO, OUTLINE, bubble, cell, cut_sheet, frame, icon_coin, macros, mono, paste, rich, zoom_cone
from style import PALETTE as P, RES, apply_style, load_json

HERE = Path(__file__).resolve().parent
M = macros(HERE.parent / "tables/numbers.tex")
apply_style(8)
W, H = 6.5, 3.95
fig = plt.figure(figsize=(W, H), dpi=300)
ov = fig.add_axes([0, 0, 1, 1]); ov.set_xlim(0, W); ov.set_ylim(0, H); ov.axis("off")
robot, envelope, shield, stop = cut_sheet(HERE / "assets_raw" / "icons2_sheet.png", rows=1, cols=4)
BLUE, RED, GREEN = P["blue_main"], P["red_strong"], "#3F7F3B"
kw = lambda c: dict(weight="bold", color=c)

# ---- panel letters and claim
ov.text(0.04, H - 0.14, "a", fontsize=15, fontweight="bold", va="center")
ov.text(4.52, H - 0.14, "b", fontsize=15, fontweight="bold", va="center")
ov.add_patch(FancyBboxPatch((0.4, 3.62), 3.75, 0.28, boxstyle="round,pad=0,rounding_size=0.07", fc="#F1F1F1", ec=OUTLINE, lw=0.9, ls=(0, (5, 2.5))))
rich(ov, 2.275, 3.76, [("Labels arrive late, so part of the harm of a switch is ", {}), ("still unseen", kw(RED)), (".", {})], fs=8.4, ha="center")

# ---- panel a: the round strip
paste(ov, robot, 0.4, 3.0, 0.4)
bubble(ov, 0.7, 3.14, 0.8, 0.26, tail=(0.55, 3.06), fill="white", ec=OUTLINE, lw=0.8)
mono(ov, 1.12, 3.27, "switch now?", fs=6.2, ha="center")
paste(ov, envelope, 0.4, 2.4, 0.3)
X0, CW_, CG, CH_ = 1.58, 0.235, 0.02, 0.2
cx = lambda i: X0 + (i - 1) * (CW_ + CG)           # left edge of round i
rows = {"round": 2.8, "dep": 2.53, "lab": 2.26}
for name, lab in (("round", "round t"), ("dep", "deployed"), ("lab", "label")):
    mono(ov, X0 - 0.07, rows[name] + CH_ / 2, lab, fs=5.9, ha="right")
shades = ["#B5D3F0", "#9CC1EA", "#80AEE2", "#5F95D5", "#3F7CC6", "#245FAE", "#0F4D92"]
for i in range(1, 12):
    cell(ov, cx(i), rows["round"], CW_, CH_, "#E3E2E2", lw=0.6, r=0.03)
    ov.text(cx(i) + CW_ / 2, rows["round"] + CH_ / 2, str(i), fontsize=6.4, family=MONO, ha="center", va="center", zorder=8)
    on = 4 <= i <= 10
    cell(ov, cx(i), rows["dep"], CW_, CH_, shades[i - 4] if on else "white", lw=0.6, r=0.03)
    if on and i <= 7:
        cell(ov, cx(i), rows["lab"], CW_, CH_, BLUE, lw=0.6, r=0.03)
    elif on:
        cell(ov, cx(i), rows["lab"], CW_, CH_, "white", lw=0.8, r=0.03, ls=(0, (2.2, 1.6)), ec=BLUE)
        ov.text(cx(i) + CW_ / 2, rows["lab"] + CH_ / 2, "?", fontsize=7.5, fontweight="bold", color=BLUE, ha="center", va="center", zorder=8)
    else:
        cell(ov, cx(i), rows["lab"], CW_, CH_, "white", lw=0.6, r=0.03)

def bracket(x0, x1, y, h, up=True):
    s = 1 if up else -1
    ov.plot([x0, x0, x1, x1], [y - s * h, y, y, y - s * h], color=OUTLINE, lw=0.8, solid_joinstyle="round")
xL = lambda i: cx(i) - 0.0; xR = lambda i: cx(i) + CW_
bracket(xL(1), xR(3), 3.32, 0.05); bracket(xL(4), xR(10), 3.32, 0.05)
ov.text((xL(1) + xR(3)) / 2, 3.42, "incumbent", fontsize=7, style="italic", ha="center", va="center")
ov.text((xL(4) + xR(10)) / 2, 3.42, "challenger deployed", fontsize=7, style="italic", ha="center", va="center")
icon_coin(ov, cx(4) + CW_ / 2, 3.12, r=0.075); icon_coin(ov, cx(11) + CW_ / 2, 3.12, r=0.075)
bracket(xL(4), xR(7), 2.2, 0.05, up=False); bracket(xL(8), xR(10), 2.2, 0.05, up=False)
ov.text((xL(4) + xR(7)) / 2, 2.1, "seen", fontsize=7, style="italic", ha="center", va="center")
ov.text((xL(8) + xR(10)) / 2, 2.1, "in transit", fontsize=7, style="italic", ha="center", va="center")
nowx = cx(10) + CW_ + CG / 2
ov.plot([nowx, nowx], [2.2, 3.05], color=RED, lw=1.0, ls=(0, (3, 2)), zorder=7)
ov.text(nowx + 0.05, 2.1, "now", fontsize=7, style="italic", color=RED, fontweight="bold", ha="left", va="center")

# ---- zoom into the shield's check
PX0, PY0, PW_, PH_ = 0.1, 0.42, 4.3, 1.28
segx = PX0 + 0.22 + 0.42 + 0.55 + 0.58
zoom_cone(ov, (xL(8), 2.0, xR(10), 2.04), (segx, PY0, segx + 0.98, PY0 + 0.62 + 0.27 + 0.01), color=P["blue_secondary"], alpha=0.22, zorder=2.5)
ov.add_patch(FancyBboxPatch((PX0, PY0), PW_, PH_, boxstyle="round,pad=0,rounding_size=0.08", fc="white", ec=OUTLINE, lw=0.9, zorder=2))
paste(ov, shield, PX0 + 0.22, PY0 + PH_ - 0.2, 0.26)
rich(ov, PX0 + 0.45, PY0 + PH_ - 0.2, [("the shield's check ", {}), ("$W_t$", dict(weight="bold")), (", made before each round", {})], fs=7)
segs = [("fees", 0.42, "#E3E2E2"), ("rollback\nreserve", 0.55, "#F6CFCB"), ("seen\nharm", 0.58, "#7DAAE0"),
        ("in transit,\nworst case", 0.98, "#D4E6F8"), ("this\nround", 0.5, "#FBD9A8"), ("width", 0.45, "#DCCBEF")]
sx = PX0 + 0.22; sy, sh = PY0 + 0.62, 0.27
x = sx; xs = []
for lab, w, c in segs:
    ov.add_patch(FancyBboxPatch((x, sy), w, sh, boxstyle="round,pad=0,rounding_size=0.0", fc=c, ec=OUTLINE, lw=0.7, zorder=3))
    mono(ov, x + w / 2, sy - 0.13, lab, fs=5.6, ha="center", va="center", linespacing=1.3)
    xs.append((x, w)); x += w
frame(ov, xs[3][0] - 0.01, sy - 0.04, xs[3][1] + 0.02, sh + 0.08, color="#8B1E1E", lw=1.5, r=0.05, zorder=7)
bx_ = x + 0.12
ov.plot([bx_, bx_], [sy - 0.3, sy + sh + 0.12], color=RED, lw=1.0, ls=(0, (3, 2)), zorder=7)
rich(ov, bx_ - 0.02, sy + sh + 0.2, [("budget ", {"family": MONO}), ("R", dict(weight="bold", color=RED, style="italic"))], fs=6.3, ha="right")
ov.add_patch(FancyBboxPatch((PX0 + 0.2, PY0 + 0.08), PW_ - 0.4, 0.22, boxstyle="round,pad=0,rounding_size=0.06", fc=CALLOUT["green"][0], ec="none", zorder=2))
rich(ov, PX0 + PW_ / 2, PY0 + 0.19, [("Deploy", kw(GREEN)), (" only if ", {}), ("$W_t\\leq R$", kw(GREEN)), ("; otherwise ", {}), ("roll back", kw(GREEN)), (".", {})], fs=7.4, ha="center")

# ---- panel b: exceedance bars on the same canvas
conf = load_json(RES / "confirm_summary.json")
c3, c1, c2 = conf["C3"]["arms"], conf["C1"]["arms"], conf["C2"]["arms"]
bars = [("Wald cutoff", c3["wald_cut"], "r"), ("CUSUM", c3["cusum"], "r"), ("e-process gate", c3["gate_wald"], "r"),
        ("CUSUM rollback", c3["cusum_rb_h8"], "r"), ("stop-loss", c3["stoploss_R20"], "r"),
        ("shield, full", c1["f3_pi1_R20"], "b"), ("shield, paced", c2["f3v2d_R20"], "b")]
vals = [max(r["rate"] for r in a["per_regime"].values()) for _, a, _ in bars]
assert abs(vals[0] - float(M["WorstWald"])) < 1e-3 and abs(vals[4] - float(M["WorstStop"])) < 1e-3
mono(ov, 4.62, 3.6, "budget exceedance", fs=7.6, weight="bold")
ov.text(4.62, 3.38, "share of runs above R = 20,\nworst regime", fontsize=6.4, color=P["grey"], style="italic", va="center", linespacing=1.15)
ax = fig.add_axes([5.35 / W, 0.62 / H, 1.05 / W, 2.2 / H]); ax.patch.set_alpha(0)
yy = list(range(len(bars)))[::-1]
for yi, (lab, a, k), v in zip(yy, bars, vals):
    col = RED if k == "r" else BLUE
    ax.barh(yi, v, color=col, height=0.62, edgecolor=OUTLINE, linewidth=0.5)
    ax.text(v + 0.04, yi, f"{v:.3f}".lstrip("0") if v else "0", va="center", fontsize=6.5, color=col, fontweight="bold" if k == "b" else "normal")
ax.set_yticks(yy); ax.set_yticklabels([b[0] for b in bars], fontsize=6.6)
ax.set_xlim(0, 1.3); ax.set_ylim(-0.6, len(bars) - 0.4); ax.set_xticks([0, .5, 1])
ax.tick_params(axis="x", labelsize=6.3, length=2.5, pad=1.5); ax.tick_params(axis="y", length=0, pad=2)

# ---- takeaway: thin rule and a plain sentence
ov.plot([0.1, 6.4], [0.3, 0.3], color=BLUE, lw=0.6)
rich(ov, 0.1, 0.16, [("The shield keeps the realised harm ", {}), ("inside the budget", kw(BLUE)), (" where heuristic controllers do not.", {})], fs=8)

fig.savefig(HERE / "fig_overview.pdf", dpi=300); fig.savefig(HERE / "fig_overview.png", dpi=300)
plt.close(fig)
print("overview ok", [round(v, 3) for v in vals])
