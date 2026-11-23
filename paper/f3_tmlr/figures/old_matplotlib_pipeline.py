"""Figure (Section 5): the evaluation in four stages, each with a small illustrated motif built from its own results
(figures4papers composite style, see STYLE_SPEC.md). Data: confirm_summary.json (stage 1), numbers.tex (stages 2-4),
real_summary.json (stage 3), outputs/.../screen100/tally.json (stage 4).
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matplotlib.colors import LinearSegmentedColormap, to_hex
from matplotlib.patches import Circle, Polygon
from schematic import OUTLINE, block_arrow, canvas, cell, cut_sheet, finish, macros, mono, panel, paste, rich, tag
from shiftlab.paper3.riskbudget.real_streams import STREAMS
from style import CONFIGS, OUT, PALETTE as P, RES, WIDTH, apply_style, load_json, save

HERE = Path(__file__).resolve().parent
M = macros(HERE.parent / "tables/numbers.tex", HERE.parent / "tables/screen_numbers.tex")
apply_style(8)
ICONS = cut_sheet(HERE / "assets_raw/icons_sheet.png")  # incumbent, challenger, shield, envelope
W, H = WIDTH, 2.62
fig, ax = canvas(W, H)
CW_, CG, X0 = 1.49, 0.115, 0.1
CY, CH_ = 0.44, 1.9
cardx = lambda k: X0 + k * (CW_ + CG)
B = dict(weight="bold", color=P["blue_main"])
R_ = dict(weight="bold", color=P["red_strong"])

heads = ["1  simulation", "2  calibration", "3  real streams", "4  public screen"]
for k, h in enumerate(heads):
    panel(ax, cardx(k), CY, CW_, CH_, fill="white", lw=0.9, shadow=True)
    paste(ax, ICONS[[1, 0, 3, 2][k]], cardx(k) + CW_ - 0.17, CY + CH_ - 0.17, 0.2)
    mono(ax, cardx(k) + 0.09, CY + CH_ - 0.15, h, fs=6.4, weight="bold")
    if k < 3:
        ax.add_patch(Polygon([(cardx(k) + CW_ + 0.012, CY + CH_ / 2 - 0.05), (cardx(k) + CW_ + CG - 0.012, CY + CH_ / 2),
                              (cardx(k) + CW_ + 0.012, CY + CH_ / 2 + 0.05)], fc=OUTLINE, ec="none", zorder=4))

# ---------------------------------------------------------------- 1: 30 regimes tiles coloured by Wald exceedance
conf = load_json(RES / "confirm_summary.json")
c3 = conf["C3"]["arms"]
stress = [r["id"] for r in load_json(CONFIGS / "regimes_f3_v1.json")["regimes"]]
regs = list(c3["wald_cut"]["per_regime"])
order = [r for r in regs if r not in stress] + stress
rate = [c3["wald_cut"]["per_regime"][g]["rate"] for g in order]
cm = LinearSegmentedColormap.from_list("r", ["#FFFFFF", "#F2B8B2", "#B64342", "#5E1F1E"])
tw, th, tg = 0.185, 0.135, 0.028
gx0 = cardx(0) + (CW_ - (6 * tw + 5 * tg)) / 2
gy0 = CY + 0.8
for i, v in enumerate(rate):
    r_, c_ = divmod(i, 6)
    cell(ax, gx0 + c_ * (tw + tg), gy0 - r_ * (th + tg) + 0.62, tw, th, to_hex(cm(min(1, v / 0.9))), lw=0.6, r=0.025, zorder=3)
ax.text(gx0 + 6 * (tw + tg) - tg, gy0 + 0.62 - 4 * (th + tg) - 0.065, "stress", fontsize=5.6, color=P["red_strong"], ha="right", va="center", style="italic")

# ---------------------------------------------------------------- 2: stop-loss margin line (blocks promotion past R-2k)
Rv, kv = 20.0, 3.0
cs = float(M["CalStopCB"])
lx0, lx1 = cardx(1) + 0.14, cardx(1) + CW_ - 0.14
fx = lambda c: lx0 + (lx1 - lx0) * c / Rv
ly = CY + 1.0
ax.add_patch(Polygon([(fx(0), ly - 0.07), (fx(Rv - 2 * kv), ly - 0.07), (fx(Rv - 2 * kv), ly + 0.07), (fx(0), ly + 0.07)], fc="#DFF1DF", ec=OUTLINE, lw=0.7, zorder=3))
ax.add_patch(Polygon([(fx(Rv - 2 * kv), ly - 0.07), (fx(Rv), ly - 0.07), (fx(Rv), ly + 0.07), (fx(Rv - 2 * kv), ly + 0.07)], fc="#F6D5D2", ec=OUTLINE, lw=0.7, zorder=3))
ax.text((fx(0) + fx(Rv - 2 * kv)) / 2, ly, "promotion possible", fontsize=5.4, ha="center", va="center", color="#3F7F3B", zorder=5)
ax.text((fx(Rv - 2 * kv) + fx(Rv)) / 2, ly, "none", fontsize=5.4, ha="center", va="center", color=P["red_strong"], zorder=5)
for c, lab in ((0, "0"), (Rv - 2 * kv, "R$-$2k"), (Rv, "R")):
    ax.plot([fx(c)] * 2, [ly - 0.07, ly - 0.12], color=OUTLINE, lw=0.7, zorder=4)
    ax.text(fx(c), ly - 0.2, lab, fontsize=5.8, ha="center", va="center", color=P["dark"])
ax.add_patch(Polygon([(fx(cs), ly + 0.1), (fx(cs) - 0.045, ly + 0.2), (fx(cs) + 0.045, ly + 0.2)], fc=P["red_strong"], ec=OUTLINE, lw=0.6, zorder=6))
mono(ax, lx0, ly + 0.42, "stop-loss margin c", fs=5.6, color=P["grey"])
rich(ax, fx(cs) + 0.03, ly + 0.3, [("first c that meets .05", dict(weight="bold", color=P["red_strong"], style="italic"))], fs=5.8, ha="right")

# ---------------------------------------------------------------- 3: per-stream shield cost vs never switching (h = 14, clean)
rs = json.loads((HERE.parent.parents[1] / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget/real_summary.json").read_text())
st = rs["results"]["clean"]["streams"]
gains = sorted([(-st[s]["arms"]["f3_pi1_h14"]["d_never"]["delta"], s) for s in STREAMS], reverse=True)
mx = max(abs(g) for g, _ in gains)
bw_, bg_ = 0.07, 0.019
bx0 = cardx(2) + (CW_ - (12 * bw_ + 11 * bg_)) / 2
by0 = CY + 0.98
ax.plot([bx0 - 0.03, bx0 + 12 * bw_ + 11 * bg_ + 0.03], [by0, by0], color=OUTLINE, lw=0.8, zorder=3)
for i, (g, s) in enumerate(gains):
    h = 0.36 * g / mx
    x = bx0 + i * (bw_ + bg_)
    cell(ax, x, min(by0, by0 + h), bw_, abs(h), "", grad=("#8DB4E2", "#2E67A8") if g > 0 else ("#F2B8B2", "#B64342"), r=0.012, lw=0.55, zorder=3)
mono(ax, cardx(2) + 0.09, CY + 1.5, "shield cost vs never", fs=5.4, color=P["grey"])
ax.text(bx0 + 12 * bw_ + 11 * bg_, by0 - 0.3, "airlines, bank: harmful", fontsize=5.2, color=P["red_strong"], style="italic", va="center", ha="right")

# ---------------------------------------------------------------- 4: 100 dots, S2 met vs not
tally = json.loads((OUT / "screen100/tally.json").read_text())["rows"]
sup = sorted([r for r in tally if r["status"] == "supported"], key=lambda r: -r["shield_gain_vs_never"])
non = [r for r in tally if r["status"] != "supported"]
dots = sup + non
dr, dsp = 0.043, 0.113
dx0 = cardx(3) + (CW_ - 9 * dsp) / 2
dy0 = CY + 1.42
for i, r in enumerate(dots):
    rr, cc = divmod(i, 10)
    x, y = dx0 + cc * dsp, dy0 - rr * 0.098 + 0.0
    ok = r["status"] == "supported"
    ax.add_patch(Circle((x, y), dr * 0.9, fc=P["blue_secondary"] if ok else "#E6E6E6", ec=P["red_strong"] if not r["S1"] else (OUTLINE if ok else "#BDBDBD"),
                        lw=1.2 if not r["S1"] else 0.5, zorder=4))
mono(ax, cardx(3) + 0.09, CY + 1.57, "blue: S2 met", fs=5.4, color=P["blue_main"], weight="bold")

# ---------------------------------------------------------------- captions
caps = [
    [[(f"{M['NRegimes']} regimes", True), (f", {M['NSeedsPerRegime']} seeds each;", False)], [("shield: ", False), (f"{M['COneTotal']} violations", True), (" (full)", False)]],
    [[("stop-loss meets the target", False)], [("only by ", False), ("blocking promotion", True)]],
    [[("12 real streams", True), (f", {M['NStreamEpisodes']} episodes;", False)], [("shield: ", False), (f"{M['RealShieldViolClean']} violations", True)]],
    [[(f"{M['ScreenPool']} public streams", True), (":", False)], [(f"S1 on {M['ScreenSOne']}, S2 on ", False), (f"{M['ScreenSupported']}", True)]],
]
for k, lines in enumerate(caps):
    for j, line in enumerate(lines):
        parts = [(t, (dict(weight="bold", color=P["red_strong"]) if k == 1 else B) if kw else {}) for t, kw in line]
        rich(ax, cardx(k) + CW_ / 2, CY + 0.34 - j * 0.15, parts, fs=6.2, ha="center")

block_arrow(ax, 0.1, 0.03, 6.3, 0.3, c0="#EAF1FA", c1="#6F9ED3", head=0.28)
rich(ax, 3.2, 0.18, [("The same ", {}), ("frozen arms", B), (" are run from synthetic stress to public streams.", {})], fs=7, ha="center")
finish(ax)
save(fig, "pipeline")
print("wrote fig_pipeline")
