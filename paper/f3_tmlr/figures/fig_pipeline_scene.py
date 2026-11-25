"""Pipeline figure (start of Section 5), built as ONE canvas in the figures4papers 'miscellaneous' style: four stages,
flat line-art icons, small gradient block arrows, a data motif per stage drawn from the result files, captions with bold
coloured keywords, and a pale tinted takeaway box. Numbers are read from tables/*.tex macros."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_hex
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from matplotlib.patches import Polygon as _Poly
from schematic import MONO, OUTLINE, gradient_patch, cut_sheet, macros, mono, paste, rich
from shiftlab.paper3.riskbudget.real_streams import STREAMS
from style import CONFIGS, OUT, PALETTE as P, RES, apply_style, load_json

HERE = Path(__file__).resolve().parent
M = macros(HERE.parent / "tables/numbers.tex", HERE.parent / "tables/screen_numbers.tex")
apply_style(8)
W, H = 6.5, 2.3
fig = plt.figure(figsize=(W, H), dpi=300)
ov = fig.add_axes([0, 0, 1, 1]); ov.set_xlim(0, W); ov.set_ylim(0, H); ov.axis("off")
robot, envelope, shield, stop = cut_sheet(HERE / "assets_raw" / "icons2_sheet.png", rows=1, cols=4)
BLUE, RED = P["blue_main"], P["red_strong"]
kw = lambda c, **k: dict(weight="bold", color=c, **k)
SW, STEP, S = 1.38, 1.6, 1.06                        # stage width, stage pitch, motif scale (motif units are 1.3 x 1.0)
OX = [0.08 + i * STEP for i in range(4)]
OY = 0.84
DK = '#444444'

conf = load_json(RES / "confirm_summary.json"); c3 = conf["C3"]["arms"]
titles = ["1  simulation", "2  calibration", "3  real streams", "4  public screen"]
for ox, t, ic in zip(OX, titles, (robot, None, envelope, shield)):
    mono(ov, ox, 2.1, t, fs=7.6, weight="bold")
    if ic is not None:
        paste(ov, ic, ox + SW - 0.12, 2.1, 0.27)


def oarrow(x, y, w=0.17, h=0.12, head=0.06):
    b = h * 0.5; yc = y
    pts = [(x, yc - b / 2), (x + w - head, yc - b / 2), (x + w - head, yc - h / 2), (x + w, yc), (x + w - head, yc + h / 2),
           (x + w - head, yc + b / 2), (x, yc + b / 2)]
    gradient_patch(ov, _Poly(pts, closed=True, fc="none", ec="none"), "#F1F5F8", "#A9C5DA", vertical=False, zorder=2)
    ov.add_patch(_Poly(pts, closed=True, fc="none", ec="#505860", lw=0.6, zorder=3))


for i in range(3):
    oarrow(OX[i] + SW + 0.0, 1.35)


mx = lambda ox, u: ox + u * S                         # motif x in inches
my = lambda v: OY + v * S

# 1: 30 regime tiles coloured by Wald exceedance
stress = [r["id"] for r in load_json(CONFIGS / "regimes_f3_v1.json")["regimes"]]
regs = list(c3["wald_cut"]["per_regime"])
order = [r for r in regs if r not in stress] + stress
rate = [c3["wald_cut"]["per_regime"][g]["rate"] for g in order]
cm = LinearSegmentedColormap.from_list("r", ["#FFFFFF", "#F2B8B2", "#B64342", "#5E1F1E"])
tw, th, tg = 0.185, 0.12, 0.024
x0 = (1.3 - (6 * tw + 5 * tg)) / 2
for i, v in enumerate(rate):
    r_, c_ = divmod(i, 6)
    ov.add_patch(FancyBboxPatch((mx(OX[0], x0 + c_ * (tw + tg)), my(0.75 - r_ * (th + tg))), tw * S, th * S, boxstyle="round,pad=0,rounding_size=0.02",
                                fc=to_hex(cm(min(1, v / 0.9))), ec="#777D82", lw=0.45, zorder=3))
ov.text(mx(OX[0], x0 + 6 * (tw + tg) - tg), my(0.75 - 4 * (th + tg) - 0.055), "stress regimes", fontsize=6.6, color=RED, ha="right", va="center", style="italic")
mono(ov, mx(OX[0], x0), my(0.985), "Wald share above R", fs=6.5, color=DK, va="top")
kx, ky = mx(OX[0], x0), my(0.75 - 4 * (th + tg) - 0.055)
ov.imshow(np.linspace(0, 1, 64)[None, :], cmap=cm, extent=(kx + 0.1, kx + 0.5, ky - 0.03, ky + 0.03), aspect="auto", zorder=3)
ov.add_patch(FancyBboxPatch((kx + 0.1, ky - 0.03), 0.4, 0.06, boxstyle="square,pad=0", fc="none", ec=OUTLINE, lw=0.4, zorder=4))
ov.text(kx + 0.07, ky, "0", fontsize=6.2, ha="right", va="center", color=DK)
ov.text(kx + 0.53, ky, ".9", fontsize=6.2, ha="left", va="center", color=DK)

# 2: stop-loss margin line
Rv, kv, cs = 20.0, 3.0, float(M["CalStopCB"])
lx0, lx1, ly = 0.1, 1.2, 0.45
fx = lambda c: mx(OX[1], lx0 + (lx1 - lx0) * c / Rv)
hh = 0.1 * S
ov.add_patch(FancyBboxPatch((fx(0), my(ly) - hh), fx(Rv - 2 * kv) - fx(0), 2 * hh, boxstyle="round,pad=0,rounding_size=0.0", fc="#E3F1E1", ec=OUTLINE, lw=0.7))
ov.add_patch(FancyBboxPatch((fx(Rv - 2 * kv), my(ly) - hh), fx(Rv) - fx(Rv - 2 * kv), 2 * hh, boxstyle="round,pad=0,rounding_size=0.0", fc="#F6D5D2", ec=OUTLINE, lw=0.7))
ov.text((fx(0) + fx(Rv - 2 * kv)) / 2, my(ly), "possible", fontsize=6.4, ha="center", va="center", color="#3F7F3B", fontweight="bold")
ov.text((fx(Rv - 2 * kv) + fx(Rv)) / 2, my(ly), "none", fontsize=6.4, ha="center", va="center", color=RED, fontweight="bold")
for c, lab in ((0, "0"), (Rv - 2 * kv, "R$-$2k"), (Rv, "R")):
    ov.plot([fx(c)] * 2, [my(ly) - hh, my(ly) - hh - 0.05], color=OUTLINE, lw=0.7)
    ov.text(fx(c), my(ly) - hh - 0.13, lab, fontsize=6.6, ha="center", va="center")
ov.add_patch(Polygon([(fx(cs), my(ly) + hh), (fx(cs) - .05, my(ly) + hh + 0.1), (fx(cs) + .05, my(ly) + hh + 0.1)], fc=RED, ec=OUTLINE, lw=0.6, zorder=4))
mono(ov, mx(OX[1], lx0), my(1.0), "stop-loss margin c", fs=6.5, color=DK)
ov.text(fx(cs) + .02, my(ly) + hh + 0.24, "first c that\nmeets .05", fontsize=6.6, color=RED, fontweight="bold", style="italic", ha="right", va="center", linespacing=1.1)

# 3: per-stream shield cost vs never (h = 14, clean)
rs = json.loads((HERE.parent.parents[1] / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget/real_summary.json").read_text())
st = rs["results"]["clean"]["streams"]
gains = sorted([(-st[s]["arms"]["f3_pi1_h14"]["d_never"]["delta"], s) for s in STREAMS], reverse=True)
gm = max(abs(g) for g, _ in gains)
NS = len(gains)
bw_, bg_ = 0.07, 0.019
bw_ = min(bw_, 1.2 / (NS * 1.27)); bg_ = bw_ * 0.27
bx0 = (1.3 - (NS * bw_ + (NS - 1) * bg_)) / 2
by0 = 0.38
ov.plot([mx(OX[2], bx0 - 0.03), mx(OX[2], bx0 + NS * bw_ + (NS - 1) * bg_ + 0.03)], [my(by0)] * 2, color=OUTLINE, lw=0.8)
for i, (g, s) in enumerate(gains):
    h = 0.5 * g / gm
    ov.add_patch(FancyBboxPatch((mx(OX[2], bx0 + i * (bw_ + bg_)), my(min(by0, by0 + h))), bw_ * S, abs(h) * S, boxstyle="round,pad=0,rounding_size=0.01",
                                fc="#5C93D1" if g > 0 else "#E08A84", ec=OUTLINE, lw=0.5, zorder=3))
mono(ov, mx(OX[2], bx0), my(0.96), "shield gain vs never", fs=6.5, color=DK, va="center")
nneg = sum(1 for g, _ in gains if g < 0)
assert NS == len(STREAMS)
bxn0, bxn1 = mx(OX[2], bx0 + (NS - nneg) * (bw_ + bg_)), mx(OX[2], bx0 + NS * bw_ + (NS - 1) * bg_)
yb = my(by0 - 0.5 * abs(min(g for g, _ in gains)) / gm) - 0.05
ov.plot([bxn0, bxn0, bxn1, bxn1], [yb + 0.03, yb, yb, yb + 0.03], color=RED, lw=0.7)
ov.text((bxn0 + bxn1) / 2, yb - 0.08, f"{nneg} of {NS} worse than never", fontsize=6.2, color=RED, ha="center", va="center")

# 4: 100 dots, S2 met vs not
tally = json.loads((OUT / "screen100/tally.json").read_text())["rows"]
sup = sorted([r for r in tally if r["status"] == "supported"], key=lambda r: -r["shield_gain_vs_never"])
non = [r for r in tally if r["status"] != "supported"]
dsp, dr = 0.113, 0.043
dx0 = (1.3 - 9 * dsp) / 2
for i, r in enumerate(sup + non):
    rr, cc = divmod(i, 10)
    ok = r["status"] == "supported"
    ov.add_patch(Circle((mx(OX[3], dx0 + cc * dsp), my(0.9 - rr * 0.085)), dr * 0.8 * S, fc="#4A82C4" if ok else "#E6E6E6",
                        ec=RED if not r["S1"] else (OUTLINE if ok else "#BDBDBD"), lw=1.1 if not r["S1"] else 0.5, zorder=3))

ky4 = 0.8
kxs = OX[3] + 0.08
ov.add_patch(Circle((kxs, ky4), 0.03, fc="#4A82C4", ec=OUTLINE, lw=0.5, zorder=3)); ov.text(kxs + 0.05, ky4, "S2 met", fontsize=6.2, va="center", color=DK)
ov.add_patch(Circle((kxs + 0.43, ky4), 0.03, fc="#E6E6E6", ec="#BDBDBD", lw=0.5, zorder=3)); ov.text(kxs + 0.48, ky4, "not", fontsize=6.2, va="center", color=DK)
ov.add_patch(Circle((kxs + 0.78, ky4), 0.03, fc="#E6E6E6", ec=RED, lw=1.1, zorder=3)); ov.text(kxs + 0.83, ky4, "S1 failed", fontsize=6.2, va="center", color=DK)

# captions (counts from the macros)
for k, key in (("NRegimes", "30"), ("ScreenPool", "100"), ("ScreenSOne", "99"), ("ScreenSupported", "57"), ("NStreamEpisodes", "230")):
    assert M[k].replace("{,}", "") == key, (k, M[k])
cap = [
    ([("30 regimes", kw(BLUE)), (", 1,000 seeds each;", {})], [("shield: ", {}), ("0 violations", kw(BLUE)), (" (full)", {})]),
    ([("stop-loss meets the target", {})], [("only by ", {}), ("blocking promotion", kw(RED))]),
    ([(f"{len(STREAMS)} real streams", kw(BLUE)), (", 230 episodes;", {})], [("shield: ", {}), ("0 violations", kw(BLUE))]),
    ([("100 public streams", kw(BLUE)), (":", {})], [("S1 on 99, S2 on ", {}), ("57", kw(BLUE))]),
]
for ox, (l1, l2) in zip(OX, cap):
    rich(ov, ox, 0.58, l1, fs=6.9); rich(ov, ox, 0.43, l2, fs=6.9)

ov.plot([0.08, 6.42], [0.29, 0.29], color=BLUE, lw=0.6)
rich(ov, 0.08, 0.15, [("The same ", {}), ("frozen arms", kw(BLUE)), (" are run from synthetic stress to public streams.", {})], fs=7.8)

fig.savefig(HERE / "fig_pipeline.pdf", dpi=300); fig.savefig(HERE / "fig_pipeline.png", dpi=300)
plt.close(fig)
print("pipeline ok")
