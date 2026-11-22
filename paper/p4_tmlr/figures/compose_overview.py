"""Figure 1 (teaser): composed schematic.  (a) the promotion problem, (b) RB-DP solver, (c) a real value landscape with a
real policy rollout, (d) i.i.d.-calibrated gate vs RB-DP.  Run:  PYTHONPATH=src ../../../.venv/bin/python compose_overview.py
Every number comes from the solver (overview_assets) or phase10_baselines/tally.json and is asserted below.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import overview_assets as OA
import lattice_data as LD
from svgkit import Svg, C, MONO, SERIF

HERE = Path(__file__).resolve().parent
BUILD = HERE / "_build"
BUILD.mkdir(exist_ok=True)

# ---------------------------------------------------------------- data (all asserted)
L = OA.landscape()
seed, steps = OA.pick_rollout(L)
T, B, ALPHA = LD.T, LD.B, 0.1
assert L["solver"].cfg.T == T and L["solver"].cfg.B == B and abs(L["solver"].cfg.alpha - ALPHA) < 1e-12
assert len(steps) == T and sum(r["query"] for r in steps) == B  # whole horizon seen, all B labels bought
lab = [("0" if r["y"] == 0 else "1") if r["query"] else "?" for r in steps]
gap = L["Wi"] - L["Wc"]
GAP_MAX = float(gap.max())
assert GAP_MAX > 0
tal = OA.tally()
mr = tal["max_ratio"]
N_SET, N_CHAIN, N_IIDBREAK = tal["settings"], tal["chains"], tal["iid_break_datasets"]
assert tal["dearer"] == 0 and tal["cheaper"] + tal["tie"] == N_SET == 12 * N_CHAIN
UNSAFE = {p: mr[p] for p in ("P3", "P4", "P5")}
SAFE = {p: mr[p] for p in ("P1", "P2", "P6", "P7")}
assert all(v > 1 + 1e-9 for v in UNSAFE.values()) and all(v <= 1 + 1e-9 for v in SAFE.values())
WORST = max(UNSAFE.values())
assert WORST == int(WORST)
# the number of chains must agree with the paper's ORDER (the figure fails loudly if the ledger and tally drift apart)
sys.path.insert(0, str(HERE.parent))
import make_tables as MT
assert N_CHAIN == len(MT.ORDER), (N_CHAIN, len(MT.ORDER))

# ---------------------------------------------------------------- 3D asset
land_png = BUILD / "landscape.png"
anch, (zmin, zmax) = OA.render_landscape(land_png, L, steps, dpi=600)
im = Image.open(land_png)
bb = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
im.crop(bb).save(BUILD / "landscape_crop.png", optimize=True)
W0, H0 = im.size
cw, ch = bb[2] - bb[0], bb[3] - bb[1]


def to_img(pt):  # fraction of the full render -> fraction of the cropped image
    return ((pt[0] * W0 - bb[0]) / cw, (pt[1] * H0 - bb[1]) / ch)


# ---------------------------------------------------------------- canvas
W, H = 624, 624
S = Svg(W, H)
INK, MID = C["ink"], C["mid"]
GT = "#3F3F3F"
segs = [("t", C["butter"]), ("β", C["blue"]), ("n", C["sage"]), ("w", C["pink"])]

# ================================================================= (a) the promotion problem
S.text(2, 15, "a", size=16, weight="bold")
S.text(20, 14, "The promotion problem", size=11.5, weight="bold", fill=GT)
for k in range(3):
    S.rect(10 + k * 3, 46 + k * 3, 30, 36, fill="#FFFFFF", stroke=INK, sw=0.9, rx=3, shadow=(k == 2))
S.text(28, 70, "<i>x<sub>t</sub></i>", size=11, anchor="middle")
S.text(28, 108, "same", size=9.6, fill=C["gtxt"], anchor="middle")
S.text(28, 119, "inputs", size=9.6, fill=C["gtxt"], anchor="middle")
S.text(82, 30, "incumbent", size=9.8, weight="bold", fill=C["dred"], anchor="middle")
S.trapezoid(54, 34, 56, 34, C["pink"], letter="<i>f</i><sub>0</sub>", size=13)
S.text(82, 98, "challenger", size=9.8, weight="bold", fill=C["dblue"], anchor="middle")
S.trapezoid(54, 102, 56, 34, C["blue"], letter="<i>f</i><sub>1</sub>", size=13)
S.arrow([(46, 62), (50, 62), (50, 51), (53, 51)], sw=0.9)
S.arrow([(46, 72), (50, 72), (50, 119), (53, 119)], sw=0.9)
agree = {2, 6, 8}
x0, pitch = 124, 14.5
rowpred = [(1, 0, 1, 0, 0, 1, 1, 0, 1), (0, 1, 0, 1, 1, 0, 1, 1, 1)]
fillc = {0: C["pink"], 1: C["blue"]}
S.text(x0 + 4 * pitch + 5, 30, "rounds", size=9.8, weight="bold", fill=GT, anchor="middle")
for k in range(9):
    cx = x0 + k * pitch + 5
    a_ = rowpred[0][k], rowpred[1][k]
    if k in agree:
        a_ = (a_[0], a_[0])
    op = 0.32 if k in agree else 1
    for rr, yy in ((0, 50), (1, 120)):
        S.circle(cx, yy, 5, fill=fillc[a_[rr]], stroke=INK, sw=0.8, opacity=op)
    if k in agree:
        S.path("M%g,58 L%g,112" % (cx, cx), stroke="#9A9A9A", sw=0.8, dash="2 2")
        S.text(cx, 89, "=", size=10, anchor="middle", fill="#9A9A9A")
    else:
        S.path("M%g,58 L%g,112" % (cx, cx), stroke="#272727", sw=0.8)
        S.text(cx, 89, "≠", size=10, anchor="middle", fill=C["dred"], weight="bold")
S.text(x0 + 4 * pitch + 5, 141, "agree: faded, disagree: kept", size=9.5, fill=C["gtxt"], anchor="middle")
S.arrow([(111, 51), (119, 51)], sw=0.9)
S.arrow([(111, 119), (119, 119)], sw=0.9)
S.block_arrow(262, 85, 292, 22, C["blue2"])
S.text(298, 92, "Y =", size=10.5, family=MONO, weight="bold")
fill_y = {"0": C["pink"], "1": C["blue"], "?": C["grey"]}
SX, SW = 322, 19
S.tokens(SX, 76, lab, SW, 22, [fill_y[s_] for s_ in lab], size=11)
for k, s_ in enumerate(steps):
    if s_["query"]:
        S.coin(SX + (k + .5) * SW, 66, 5.4, "1")
S.text(SX + 6 * SW, 114, "? = not queried", size=9.6, fill=C["gtxt"], anchor="end")
S.text(SX + 3 * SW, 46, "labels on disagreements", size=9.8, weight="bold", fill=GT, anchor="middle")
tx, ty = 478, 56
S.poly([(tx, ty + 18), (tx + 14, ty), (tx + 144, ty), (tx + 144, ty + 36), (tx + 14, ty + 36)], fill=C["butter"], stroke=INK, sw=1, shadow=True)
S.circle(tx + 14, ty + 18, 3, fill="#FFFFFF", stroke=INK, sw=0.8)
S.text(tx + 24, ty + 15, "label budget", size=9.8)
S.text(tx + 24, ty + 29, "<i>B</i> = %d queries" % B, size=10.5, weight="bold")
S.coin(tx + 124, ty + 18, 6.5, "1")
S.text(tx, ty + 56, "<i>T</i> = %d rounds, α = %g" % (T, ALPHA), size=9.6, fill=GT)
S.text(tx, ty + 68, "(stream rolled out in c)", size=9.6, fill=GT)
S.text(tx, ty + 88, "schematic", size=9.6, fill=C["gtxt"], style="italic")
S.arrow([(SX + 9, 101), (SX + 9, 160), (60, 160), (60, 196)], sw=1)
S.text(SX + 16, 155, "released labels <i>Y</i>", size=9.6, fill=GT)

# ================================================================= (b) RB-DP solver
BX0, BY0, BW, BH = 4, 178, 350, 228
S.text(2, BY0 + 2, "b", size=16, weight="bold")
S.group_box(BX0 + 14, BY0 + 18, BW - 14, BH - 18, "RB-DP (exact)", C["dblue"], tx=214)
S.text(26, 216, "Belief filter", size=10.5, weight="bold", fill=C["dsage"])
c0, c1 = (46, 250), (112, 250)
S.sphere(*c0, 15, "#E9A6A1"); S.sphere(*c1, 15, "#5B93D0")
S.text(c0[0], c0[1] + 3.4, "<i>S</i>=0", size=9.4, anchor="middle")
S.text(c1[0], c1[1] + 3.4, "<i>S</i>=1", size=9.4, anchor="middle", fill="#FFFFFF")
S.curve((c0[0] + 8, c0[1] - 14), (c1[0] - 8, c1[1] - 14), 12, sw=1)
S.curve((c1[0] - 8, c1[1] + 14), (c0[0] + 8, c0[1] + 14), 12, sw=1)
S.text(79, 228, "<i>t</i><sub>01</sub>", size=10, anchor="middle")
S.text(79, 282, "<i>t</i><sub>10</sub>", size=10, anchor="middle")
S.text(26, 302, "belief β = P(<i>S</i>=1 | labels)", size=9.6, fill=C["gtxt"])
S.block_arrow(134, 250, 156, 22, C["blue2"])
S.text(166, 216, "State", size=10.5, weight="bold", fill=C["dlav"])
for k, (lb, col) in enumerate(segs):
    S.rect(166, 226 + k * 22, 14, 22, fill=col, stroke=INK, sw=0.9, shadow=(k == 0))
    S.text(186, 242 + k * 22, lb, size=11.5, family=SERIF, style="italic")
S.block_arrow(206, 262, 226, 22, C["blue2"])
S.text(236, 216, "Bellman split", size=10.5, weight="bold", fill=C["dblue"])
rx, ry = 278, 242
S.circle(rx, ry, 8, fill="#4D4D4D", stroke=INK, sw=0.9, shadow=True)
S.text(rx + 11, ry + 4, "<i>w</i>′", size=11)
ch0, ch1 = (248, 292), (308, 292)
S.arrow([(rx - 3, ry + 8), (ch0[0] + 2, ch0[1] - 9)], sw=1)
S.arrow([(rx + 3, ry + 8), (ch1[0] - 2, ch1[1] - 9)], sw=1)
S.rect(ch0[0] - 9, ch0[1] - 8, 18, 18, fill=C["pink"], stroke=INK, sw=0.9, shadow=True)
S.rect(ch1[0] - 9, ch1[1] - 8, 18, 18, fill=C["blue"], stroke=INK, sw=0.9, shadow=True)
S.text(ch0[0], ch0[1] + 24, "<i>w</i><sub>0</sub>", size=11, anchor="middle")
S.text(ch1[0], ch1[1] + 24, "<i>w</i><sub>1</sub>", size=11, anchor="middle")
S.text(ch0[0], ch0[1] + 5, "0", size=11, anchor="middle", family=MONO, weight="bold")
S.text(ch1[0], ch1[1] + 5, "1", size=11, anchor="middle", family=MONO, weight="bold")
S.text(rx + 30, ry - 4, "<i>p</i> ∈ {0, ½}", size=10.5, weight="bold", fill=C["dred"], style="italic")
S.text(rx + 30, ry + 8, "adversary", size=9.6, fill=C["dred"], style="italic")
S.curve((ch0[0] - 11, ch0[1] - 3), (rx - 10, ry + 3), -20, col=C["dred"], sw=1.3, dash="3 2")
S.text(278, 336, "<i>w</i><sub>0</sub> ≤ <i>w</i>′", size=10.5, weight="bold", fill=C["dred"], style="italic", anchor="middle")
S.text(278, 348, "adaptive null only", size=9.6, fill=C["dred"], style="italic", anchor="middle")
S.circle(236, 326, 2, fill=INK, stroke=None)
S.arrow([(236, 326), (196, 326), (196, 372), (172, 372)], sw=1)
S.text(26, 340, "Policy", size=10.5, weight="bold", fill=C["dlav"])
ly = 372
S.path("M22,%g L166,%g" % (ly, ly), stroke=INK, sw=1.2)
lx, vx, ux = 56, 92, 128
S.rect(lx, ly - 3.5, ux - lx, 7, fill=C["blue_main"], opacity=0.5)
for xx, lb, colr in ((lx, "<i>L</i>", C["blue_main"]), (vx, "<i>V</i><sup>★</sup>", INK), (ux, "<i>U</i>", C["blue_main"])):
    S.circle(xx, ly, 3.8, fill=colr, stroke=INK, sw=0.9)
    S.text(xx, ly - 8, lb, size=10.5, anchor="middle")
S.text(26, 392, "certified <i>L</i> ≤ <i>V</i><sup>★</sup> ≤ <i>U</i>", size=9.6, fill=C["gtxt"])
S.rect(212, 358, 140, 44, fill="#FFFFFF", stroke=INK, sw=1, rx=6, dash="4 3")
S.die(220, 363, 14)
S.text(242, 374, "i.i.d. null, no cap", size=9.6)
S.shield(221, 381, 11)
S.text(242, 394, "adaptive-safe", size=9.6)

# ================================================================= (c) landscape
CX0 = 366
S.text(CX0 - 8, BY0 + 2, "c", size=16, weight="bold")
S.text(CX0 + 8, BY0 + 2, "Value landscape, one rollout", size=11.5, weight="bold", fill=C["dblue"])
IW = 232
IH = IW * ch / cw
IX, IY = CX0 + 20, BY0 + 18
S._gid += 1
cone_id = "cone%d" % S._gid
S.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8BCF8B" stop-opacity="0.9"/>'
              '<stop offset="1" stop-color="#DDF3DE" stop-opacity="0.1"/></linearGradient>' % cone_id)
tr_pts = [to_img(p) for p in anch["traj"]]
px = lambda p: (IX + p[0] * IW, IY + p[1] * IH)
Zs = [px(p) for p in tr_pts]
S.image(IX, IY, IW, IH, BUILD / "landscape_crop.png")
barx, bary = CX0 - 8, IY + IH * 0.40
S.poly([(barx + 8, bary - 24), (barx + 8, bary + 24), (Zs[0][0] + 2, Zs[0][1] + 8), (Zs[0][0] + 2, Zs[0][1] - 26)], fill="url(#%s)" % cone_id, stroke=None)
for k, (lb, col) in enumerate(segs):
    S.rect(barx, bary - 24 + k * 12, 8, 12, fill=col, stroke=INK, sw=0.7)
offs = {0: (-4, -8, "end"), 1: (6, -4, "start"), 2: (-8, -5, "end"), 3: (-5, -8, "end"), 4: (7, 12, "start"), 5: (-5, -8, "end")}
for k, (zx, zy) in enumerate(Zs):
    dx, dy, an = offs.get(k, (5, -8, "start"))
    S.text(zx + dx, zy + dy, "<i>s</i><sub>%d</sub>" % (k + 1), size=10.5, fill=C["green"], anchor=an, weight="bold")
S.text(IX + IW - 4, IY + 12, "i.i.d. (pale layer)", size=9.8, weight="bold", fill=C["blue_main"], anchor="end")
S.text(IX + IW - 4, IY + IH - 8, "adaptive (solid)", size=9.8, weight="bold", fill=C["red"], anchor="end")
bc0 = px(to_img(anch["corner_b0w0"])); bc1 = px(to_img(anch["corner_b1w0"])); wc1 = px(to_img(anch["corner_b0w1"]))
S.text(CX0 + 2, BY0 + BH - 12, "<i>t</i>=1, <i>n</i>=%d. Surface from the Bellman tables," % B, size=9.4, fill=C["dsage"])
S.text(CX0 + 2, BY0 + BH - 1, "path = one policy run, <i>s<sub>t</sub></i> = (\u03b2<sub>t</sub>, <i>w<sub>t</sub></i>)", size=9.4, fill=C["dsage"])
o = np.array(px(to_img(anch["corner_b0w0"])))
for tgt, lbl in ((anch["corner_b1w0"], "\u03b2"), (anch["corner_b0w1"], "<i>w</i>")):
    d_ = np.array(px(to_img(tgt))) - o
    d_ = d_ / np.linalg.norm(d_) * 24
    ox, oy = CX0 - 4, IY + 150
    S.arrow([(ox, oy), (ox + d_[0], oy + d_[1])], sw=1.1)
    S.text(ox + d_[0] * 1.25 - 3, oy + d_[1] * 1.25 + 3, lbl, size=10.5, family=SERIF, style="italic", fill=GT)
S.arrow([(ox, oy), (ox, oy - 24)], sw=1.1)
S.text(ox + 4, oy - 22, "<i>V</i>", size=10.5, fill=GT, family=SERIF, style="italic")

# ================================================================= (d) side by side
DY = 424
S.text(2, DY + 6, "d", size=16, weight="bold")
S.text(156, DY + 8, "i.i.d.-calibrated gate", size=13, weight="bold", family=MONO, anchor="middle", fill=INK)
S.text(470, DY + 8, "RB-DP", size=13, weight="bold", family=MONO, anchor="middle", fill=INK)
S.path("M312,%g L312,%g" % (DY + 18, DY + 192), stroke=C["neutral"], sw=1, dash="3 3")


def bars(x0, ybase, names, vals, cols, unit=15.0, bw=24, gapw=12):
    n = len(names)
    wtot = n * bw + (n - 1) * gapw
    for k, (nm, v, (fc, ec)) in enumerate(zip(names, vals, cols)):
        x = x0 + k * (bw + gapw)
        hh = max(v * unit, 1.5)
        S.rect(x, ybase - hh, bw, hh, fill=fc, stroke=ec, sw=1.1, shadow=True)
        S.text(x + bw / 2, ybase - hh - 3, ("%gα" % round(v, 3)) if v > 1.0000001 else "≤α", size=9.6, weight="bold", anchor="middle", fill=ec)
        S.text(x + bw / 2, ybase + 11, nm, size=9.6, anchor="middle")
    S.path("M%g,%g L%g,%g" % (x0 - 8, ybase, x0 + wtot + 6, ybase), stroke=INK, sw=1.1)
    S.path("M%g,%g L%g,%g" % (x0 - 8, ybase - unit, x0 + wtot + 6, ybase - unit), stroke=C["dred"], sw=1.1, dash="4 3")
    S.text(x0 - 11, ybase - unit + 3.5, "α", size=10.5, fill=C["dred"], style="italic", family=SERIF, anchor="end")


def trace(x0, y_alpha, up):
    S.path("M%g,%g L%g,%g" % (x0, y_alpha, x0 + 126, y_alpha), stroke=C["dred"], sw=1.1, dash="4 3")
    S.text(x0 - 4, y_alpha + 3.5, "α", size=10.5, fill=C["dred"], style="italic", family=SERIF, anchor="end")
    ys = [6, 2, 8, 0, 5, -2, -9, -22] if up else [8, 4, 9, 3, 7, 4, 6, 5]
    d = "M" + " L".join("%g,%g" % (x0 + i * 18, y_alpha + y_) for i, y_ in enumerate(ys))
    S.path(d, stroke=INK if up else C["blue_main"], sw=1.6, marker=True)


YB = DY + 170
S.text(26, DY + 30, "worst-case adaptive risk, in units of α", size=9.6, fill=C["gtxt"])
S.text(326, DY + 30, "worst-case adaptive risk, in units of α", size=9.6, fill=C["gtxt"])
red = (C["pink"], C["dred"]); blue = (C["blue"], C["blue_main"]); grey = (C["grey"], "#4D4D4D")
bars(34, YB, ["P3", "P4", "P5"], [UNSAFE["P3"], UNSAFE["P4"], UNSAFE["P5"]], [red] * 3, unit=16)
bars(334, YB, ["P1", "P2", "P6", "P7"], [SAFE["P1"], SAFE["P2"], SAFE["P6"], SAFE["P7"]], [grey, grey, grey, blue], unit=16)
S.path("M326,%g L460,%g" % (YB - 8 * 16, YB - 8 * 16), stroke="#B0B0B0", sw=0.9, dash="1.5 2.5")
S.text(328, YB - 8 * 16 - 3, "8\u03b1: left panel's worst case", size=9.4, fill="#8A8A8A")
trace(176, DY + 62, True)
S.text(176, DY + 84, "adversary path", size=9.6, style="italic", fill=C["dred"])
trace(486, DY + 62, False)
S.text(486, DY + 84, "same adversary, RB-DP", size=9.6, style="italic", fill=C["blue_main"])
S.rect(172, DY + 100, 134, 74, fill="#FBE3E0", rx=9)
S.text(239, DY + 116, "breaks the budget:", size=10.4, weight="bold", fill=C["red"], anchor="middle")
S.text(239, DY + 129, "up to %dα on real streams" % WORST, size=10.4, weight="bold", fill=C["red"], anchor="middle")
S.text(239, DY + 146, "%d of %d datasets (P3–P5," % (N_IIDBREAK, N_CHAIN), size=9.4, fill=C["red"], anchor="middle")
S.text(239, DY + 158, "calibrated to i.i.d.)", size=9.4, fill=C["red"], anchor="middle")
S.rect(472, DY + 100, 148, 86, fill="#E8F3E2", rx=9)
S.text(546, DY + 116, "never dearer than any", size=10.4, weight="bold", fill=C["green"], anchor="middle")
S.text(546, DY + 129, "of six safe baselines,", size=10.4, weight="bold", fill=C["green"], anchor="middle")
S.text(546, DY + 142, "%d settings" % N_SET, size=10.4, weight="bold", fill=C["green"], anchor="middle")
S.text(546, DY + 158, "cheaper in %d, tied in %d" % (tal["cheaper"], tal["tie"]), size=9.4, fill=C["green"], anchor="middle")
S.text(546, DY + 170, "risk ≤ α in every setting", size=9.4, fill=C["green"], anchor="middle")
#S.text(2, H - 4, "Schematic. (c) and the strip in (a) are computed by the lattice solver (T=%d, B=%d); (d) is read from phase10_baselines/tally.json." % (T, B), size=9.4, fill=C["gtxt"])

S.save(HERE / "fig_overview")
print("seed", seed, "labels", lab, "gap max", round(GAP_MAX, 3), "worst", WORST, N_SET, tal["cheaper"], tal["tie"], N_CHAIN, N_IIDBREAK)
