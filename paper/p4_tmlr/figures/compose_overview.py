"""Figure 1 (teaser): composed schematic.  (a) the promotion problem, (b) RB-DP solver, (c) a real value landscape with a
real policy rollout.  Run:  PYTHONPATH=src ../../../.venv/bin/python compose_overview.py
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
anch, (zmin, zmax) = OA.render_landscape(land_png, L, steps, dpi=600, elev=30, azim=-68)
im = Image.open(land_png)
bb = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
im.crop(bb).save(BUILD / "landscape_crop.png", optimize=True)
W0, H0 = im.size
cw, ch = bb[2] - bb[0], bb[3] - bb[1]


def to_img(pt):  # fraction of the full render -> fraction of the cropped image
    return ((pt[0] * W0 - bb[0]) / cw, (pt[1] * H0 - bb[1]) / ch)


# ---------------------------------------------------------------- canvas
W, H = 624, 408
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
        S.circle(SX + (k + .5) * SW, 66, 8, fill="#FCEFC7", stroke="#B8892B", sw=1.5)
S.text(SX + 3 * SW, 50, "<i>B</i> = %d queries" % B, size=10.5, weight="bold", fill="#7A5A12", anchor="middle")
S.text(SX + 6 * SW, 114, "? = not queried", size=9.6, fill=C["gtxt"], anchor="end")
S.text(SX + 3 * SW, 36, "labels on disagreements", size=9.8, weight="bold", fill=GT, anchor="middle")
tx, ty = 478, 56
S.text(tx, ty + 6, "<i>T</i> = %d rounds, α = %g" % (T, ALPHA), size=9.6, fill=GT)
S.text(tx, ty + 18, "(stream rolled out in c)", size=9.6, fill=GT)
S.text(tx, ty + 38, "schematic", size=9.6, fill=C["gtxt"], style="italic")
S.arrow([(SX + 9, 101), (SX + 9, 160), (94, 160), (94, 233)], sw=1.6, col="#3F3F3F")
S.text(SX + 16, 155, "released labels <i>Y</i>", size=9.6, fill=GT)

# ================================================================= (b) RB-DP solver
BX0, BY0, BW, BH = 4, 178, 350, 224
S.text(2, BY0 + 2, "b", size=16, weight="bold")
S.group_box(BX0 + 14, BY0 + 18, BW - 14, BH - 18, "RB-DP (exact)", C["dblue"], tx=214, dash="12 7", rx=12)
S.text(26, 216, "Belief filter", size=10.5, weight="bold", fill=C["dsage"])
c0, c1 = (46, 250), (112, 250)
S.sphere(*c0, 15, "#E9A6A1"); S.sphere(*c1, 15, "#5B93D0")
S.text(c0[0], c0[1] + 3.4, "<i>S</i>=0", size=9.4, anchor="middle")
S.text(c1[0], c1[1] + 3.4, "<i>S</i>=1", size=9.4, anchor="middle", fill="#FFFFFF")
S.curve((c0[0] + 8, c0[1] - 14), (c1[0] - 8, c1[1] - 14), 12, sw=1)
S.curve((c1[0] - 8, c1[1] + 14), (c0[0] + 8, c0[1] + 14), 12, sw=1)
S.text(62, 231, "<i>η</i><sub>01</sub>", size=10, anchor="middle")
S.text(79, 282, "<i>η</i><sub>10</sub>", size=10, anchor="middle")
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
S.text(rx, ry - 13, "<i>w</i>′", size=11, anchor="middle")
ch0, ch1 = (248, 292), (308, 292)
S.arrow([(rx - 3, ry + 8), (ch0[0] + 2, ch0[1] - 9)], sw=1)
S.arrow([(rx + 3, ry + 8), (ch1[0] - 2, ch1[1] - 9)], sw=1)
S.rect(ch0[0] - 9, ch0[1] - 8, 18, 18, fill=C["pink"], stroke=INK, sw=0.9, shadow=True)
S.rect(ch1[0] - 9, ch1[1] - 8, 18, 18, fill=C["blue"], stroke=INK, sw=0.9, shadow=True)
S.text(ch0[0] - 13, ch0[1] + 5, "<i>w</i><sub>0</sub>", size=11, anchor="end")
S.text(ch1[0] + 13, ch1[1] + 5, "<i>w</i><sub>1</sub>", size=11, anchor="start")
S.text(ch0[0], ch0[1] + 5, "0", size=11, anchor="middle", family=MONO, weight="bold")
S.text(ch1[0], ch1[1] + 5, "1", size=11, anchor="middle", family=MONO, weight="bold")
S.text(rx + 16, ry - 2, "<i>p</i> ∈ {0,½}", size=10, weight="bold", fill=C["dred"], style="italic")
S.text(rx + 16, ry + 10, "adversary", size=9.6, fill=C["dred"], style="italic")
S.curve((ch0[0] - 11, ch0[1] - 3), (rx - 10, ry + 3), -20, col=C["dred"], sw=1.3, dash="3 2")
S.text(278, 296, "<i>w</i><sub>0</sub> ≤ <i>w</i>′", size=10.5, weight="bold", fill="#8B1E1E", style="italic", anchor="middle")
S.text(278, 312, "adaptive null only", size=9.6, fill="#8B1E1E", style="italic", anchor="middle")
S.arrow([(278, 320), (278, 372), (172, 372)], sw=1.6, col="#3F3F3F")
S.text(26, 340, "Policy", size=10.5, weight="bold", fill=C["dlav"])
ly = 372
S.path("M22,%g L166,%g" % (ly, ly), stroke=INK, sw=1.2)
lx, vx, ux = 56, 92, 128
S.rect(lx, ly - 3.5, ux - lx, 7, fill=C["blue_main"], opacity=0.5)
for xx, lb, colr in ((lx, "<i>L</i>", C["blue_main"]), (vx, "<i>V</i><sup>★</sup>", INK), (ux, "<i>U</i>", C["blue_main"])):
    S.circle(xx, ly, 3.8, fill=colr, stroke=INK, sw=0.9)
    S.text(xx, ly - 8, lb, size=10.5, anchor="middle")
S.text(26, 392, "certified <i>L</i> ≤ <i>V</i><sup>★</sup> ≤ <i>U</i>", size=9.6, fill=C["gtxt"])

# ================================================================= (c) landscape
CX0 = 366
S.text(CX0 - 8, BY0 + 2, "c", size=16, weight="bold")
S.text(CX0 + 8, BY0 + 2, "Value landscape, one rollout", size=11.5, weight="bold", fill=C["dblue"])
IW = 186
IH = IW * ch / cw
IX, IY = CX0 + 10, BY0 + 14
print('IH', IH)
RED_L, BLUE_L = C["red"], "#3775BA"
S._gid += 1
cone_id = "cone%d" % S._gid
S.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8BCF8B" stop-opacity="0.45"/>'
              '<stop offset="1" stop-color="#DDF3DE" stop-opacity="0"/></linearGradient>' % cone_id)
px = lambda p: (IX + p[0] * IW, IY + p[1] * IH)
Zs = [px(to_img(p)) for p in anch["traj"]]
S.image(IX, IY, IW, IH, BUILD / "landscape_crop.png")
barx, bary = CX0 - 8, IY + IH * 0.40
cx_end = Zs[0][0] - 9
S.poly([(barx + 8, bary - 24), (barx + 8, bary + 24), (cx_end, Zs[0][1] + 6), (cx_end, Zs[0][1] - 6)], fill="url(#%s)" % cone_id, stroke=None)
for k, (lb, col) in enumerate(segs):
    S.rect(barx, bary - 24 + k * 12, 8, 12, fill=col, stroke=INK, sw=0.7)
# rollout path: straight projected segments; s3..s6 lie on the w = 0 edge, so the return segments are offset into parallel lanes
GREEN = "#47783B"
dv = np.array(Zs[2]) - np.array(Zs[5])
dv = dv / np.linalg.norm(dv)
nv = np.array([dv[1], -dv[0]])
if nv[1] > 0:
    nv = -nv  # normal pointing up on the page
LANE = {2: 4.5, 3: -4.5, 4: -9.0}  # segment index -> offset in px along nv (s3->s4 up, s4->s5 down, s5->s6 further up)
poly_pts, arrows_at = [], []
for k in range(len(Zs) - 1):
    p0, p1 = np.array(Zs[k]), np.array(Zs[k + 1])
    off = nv * LANE.get(k, 0.0)
    q0, q1 = p0 + off, p1 + off
    if k in LANE:
        seg = [tuple(p0), tuple(q0), tuple(q1), tuple(p1)]
    else:
        seg = [tuple(p0), tuple(p1)]
    segd = "M" + " L".join("%.1f,%.1f" % t for t in seg)
    S.path(segd, stroke="#FFFFFF", sw=4.6, opacity=0.95)
    poly_pts.append(segd)
    m = (q0 + q1) / 2
    tg = (q1 - q0) / np.linalg.norm(q1 - q0)
    arrows_at.append((m, tg))
for segd in poly_pts:
    S.path(segd, stroke=GREEN, sw=1.8)
for m, tg in arrows_at:
    hx, hy = tg
    ax_, ay_ = m
    S.poly([(ax_ + hx * 3.8, ay_ + hy * 3.8), (ax_ - hx * 2.6 - hy * 3.0, ay_ - hy * 2.6 + hx * 3.0),
            (ax_ - hx * 2.6 + hy * 3.0, ay_ - hy * 2.6 - hx * 3.0)], fill=GREEN, stroke="#FFFFFF", sw=0.7)
for zx, zy in Zs:
    S.circle(zx, zy, 3.4, fill="#8CC084", stroke="#2E6B2E", sw=1.1)
offs = {0: (0, -8, "middle"), 1: (7, 3, "start"), 2: (6, -12, "middle"), 3: (-2, -16, "middle"), 4: (2, 19, "middle"), 5: (-6, 4, "end")}
for k, (zx, zy) in enumerate(Zs):
    dx, dy, an = offs[k]
    S.text(zx + dx, zy + dy, "<i>s</i><sub>%d</sub>" % (k + 1), size=10.5, fill=C["green"], anchor=an, weight="bold",
           extra='stroke="#FFFFFF" stroke-width="2.6" paint-order="stroke" stroke-linejoin="round"')
# surface labels, coloured like their surface, with short leaders to the exposed right-hand edges
ia, aa = px(to_img(anch["iid_b1"])), px(to_img(anch["ad_b1"]))
LXr = IX + IW + 6
S.text(LXr, ia[1] - 12, "i.i.d.", size=9.8, weight="bold", fill=RED_L)
S.path("M%g,%g L%g,%g" % (LXr - 1, ia[1] - 14, ia[0] - 1, ia[1]), stroke=RED_L, sw=0.8)
S.text(LXr, aa[1] + 14, "adaptive", size=9.8, weight="bold", fill=BLUE_L)
S.path("M%g,%g L%g,%g" % (LXr - 1, aa[1] + 12, aa[0] - 1, aa[1]), stroke=BLUE_L, sw=0.8)
S.text(CX0 + 2, BY0 + BH - 23, "Rollout projected onto the <i>t</i> = 1, <i>n</i> = %d surface (<i>w</i> ≤ 0.3)," % B, size=9.4, fill=C["dsage"])
S.text(CX0 + 2, BY0 + BH - 12, "<i>s</i><sub>3</sub>–<i>s</i><sub>6</sub> lie on <i>w</i> = 0; return segments offset for legibility", size=9.4, fill=C["dsage"])
o = np.array(px(to_img(anch["corner_b0w0"])))
ox, oy = W - 34, IY + 36
for tgt, lbl in ((anch["corner_b1w0"], "\u03b2"), (anch["corner_b0w1"], "<i>w</i>")):
    d_ = np.array(px(to_img(tgt))) - o
    d_ = d_ / np.linalg.norm(d_) * 20
    S.arrow([(ox, oy), (ox + d_[0], oy + d_[1])], sw=1.1)
    S.text(ox + d_[0] * 1.3 - 3, oy + d_[1] * 1.3 + 3, lbl, size=10.5, family=SERIF, style="italic", fill=GT)
S.arrow([(ox, oy), (ox, oy - 22)], sw=1.1)
S.text(ox + 4, oy - 20, "<i>V</i>", size=10.5, fill=GT, family=SERIF, style="italic")

S.save(HERE / "fig_overview")
print("seed", seed, "labels", lab, "gap max", round(GAP_MAX, 3), "worst", WORST, N_SET, tal["cheaper"], tal["tie"], N_CHAIN, N_IIDBREAK)
