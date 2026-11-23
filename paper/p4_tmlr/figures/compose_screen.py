"""Figure 5: how real streams become supporting datasets.  (a) composed schematic (source icons -> bit strips -> screen gates),
(b, c) matplotlib bars embedded as inline SVG.  Run: PYTHONPATH=src ../../../.venv/bin/python compose_screen.py
Counts are read at build time from LEDGER_PHASE10.md, make_tables.ORDER, REAL_CHAINS.md, the baseline settings files and
phase9_replay.jsonl, and cross-checked; nothing is hard-coded (the ledger now covers Phases 10, 10b and 10c).
"""
import io
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from style import DARK, PALETTE as P, RBDP, REAL, apply_style, read_jsonl
from svgkit import Svg, C, MONO, SERIF
import make_tables as MT

# ---------------------------------------------------------------- numbers from files
ledger = (RBDP / "real_data/LEDGER_PHASE10.md").read_text()
cnt = {}
for key, pat in (("attempted", r"Attempted: (\d+)"), ("positive", r"Positive \(supporting\): (\d+)"),
                 ("excluded", r"Positive by the evaluator but excluded: (\d+)"),
                 ("null", r"Evaluated, no premium \(null\): (\d+)"), ("short", r"Too short: (\d+)"),
                 ("fit", r"Fit rejected \(G1 or G2\): (\d+)"), ("unavail", r"Source unavailable: (\d+)"),
                 ("dup", r"Already evaluated in Phase 4: (\d+)")):
    cnt[key] = int(re.search(pat, ledger).group(1))
assert sum(v for k, v in cnt.items() if k != "attempted") == cnt["attempted"], cnt

pos = MT.load_positive()
kinds = Counter()
for ids, name, kind in MT.ORDER:
    assert any(pos.get(i) for i in ids.split("|")), ids
    kinds[kind] += 1
N_SUP = len(MT.ORDER)
assert sum(kinds.values()) == N_SUP

rc = (RBDP / "real_data/REAL_CHAINS.md").read_text()
assert "| positive and non-degenerate | 2 (8%) | 13 (8.7%) |" in rc and "24 i.i.d. Gaussian series" in rc
NOISE, NOISE_N, REAL_POS, REAL_N = 2, 24, 13, 150
n_rec = sum(len(read_jsonl(REAL / f"{d}/settings.jsonl")) for d in ("phase7_baselines_T16_32", "phase10_baselines", "phase10c_baselines"))
assert n_rec % (7 * 12) == 0
N_SET = n_rec // 7
assert N_SET == 12 * N_SUP, (N_SET, N_SUP)  # 7 policies x 12 settings x chains
n_win = sum(r["n_windows"] for r in read_jsonl(REAL / "phase9_replay.jsonl"))
assert n_win > 0

SCR = HERE.parents[2] / "scripts/paper4_continuation/rbdp/real_data"
HYDRO = set(re.search(r'^HYDRO = set\("(\w+)"\)', (SCR / "run_phase5.py").read_text(), re.M).group(1))
VOWELS = set(re.search(r'^LATIN_BASE = set\("aeiouy" \+ "(.+)"\)', (SCR / "run_phase6.py").read_text(), re.M).group(1)) | set("aeiouy")
assert HYDRO == set("IVLFCMA") and set("aeiouy") <= VOWELS
t10b = (SCR / "run_phase10b.py").read_text()
assert "ivk = iv[ok][:CAP]" in t10b and "> median" in t10b

n_stream = cnt["attempted"] - cnt["short"] - cnt["unavail"] - cnt["dup"]
n_fit = n_stream - cnt["fit"]
n_prem = n_fit - cnt["null"]  # passes the evaluator, including the excluded Frisian stream
assert n_prem == cnt["positive"] + cnt["excluded"]
N_EARLIER = N_SUP - cnt["positive"]
assert N_EARLIER >= 0

# ---------------------------------------------------------------- (b), (c) bars as inline SVG (matplotlib)
apply_style(7.5, axes_linewidth=1.0)
plt.rcParams["svg.hashsalt"] = "p4screen"
BH = 2.0
fig = plt.figure(figsize=(6.5, BH))
axb = fig.add_axes([0.205, 0.06, 0.29, 0.70]); axc = fig.add_axes([0.745, 0.06, 0.22, 0.70])
labs = [("fit rejected (G1/G2)", cnt["fit"], P["red_2"]), ("no premium", cnt["null"], P["neutral"]),
        ("too short", cnt["short"], P["neutral"]), ("unavailable", cnt["unavail"], P["neutral"]),
        ("already in Phase 4", cnt["dup"], P["neutral"]), ("excluded (not Frisian)", cnt["excluded"], P["neutral"]),
        ("supporting", cnt["positive"], P["blue_main"])]
kl = [("texts", kinds["text"]), ("promotion", kinds["promotion"]), ("proteins", kinds["protein"]), ("geysers", kinds["geyser"])]
for ax_, items, xl in ((axb, labs, max(v for _, v, _ in labs) * 1.22), (axc, [(l, v, P["blue_main"]) for l, v in kl], max(v for _, v in kl) * 1.22)):
    for k, (l, v, c) in enumerate(items):
        ax_.barh(k, v, color=c, height=0.66, edgecolor="black", linewidth=1.0)
        ax_.text(v + xl * 0.02, k, str(v), va="center", fontsize=7.8, fontweight="bold")
    ax_.set_yticks(range(len(items))); ax_.set_yticklabels([l for l, *_ in items], fontsize=7.5)
    ax_.invert_yaxis(); ax_.set_xlim(0, xl); ax_.set_xticks([])
    ax_.spines["bottom"].set_visible(False); ax_.tick_params(axis="y", length=0, pad=3)
axb.set_title("outcome of the %d sources" % cnt["attempted"], loc="left", fontsize=8.2, fontweight="bold", color=DARK["blue"], pad=5)
axc.set_title("the %d, by type" % N_SUP, loc="left", fontsize=8.2, fontweight="bold", color=DARK["blue"], pad=5)
buf = io.StringIO()
fig.savefig(buf, format="svg")
plt.close(fig)
bars_svg = buf.getvalue()

# ---------------------------------------------------------------- composed panel (a)
W = 624
AH = 238
H = AH + BH * 96 - 18
S = Svg(W, H)
INK, GT = C["ink"], "#3F3F3F"
S.text(2, 15, "a", size=16, weight="bold")
S.text(20, 14, "Sources", size=11.5, weight="bold", fill=C["dsage"])
S.defs.append('<pattern id="grid" width="3" height="3" patternUnits="userSpaceOnUse"><rect x="0.5" y="0.5" width="2" height="2" fill="#0F4D92"/></pattern>')
CW = 11.0
fill_y = {"0": C["pink"], "1": C["blue"]}
STRIP_X = 166


def bit_strip(y, bits):
    S.tokens(STRIP_X, y - 7.5, list(bits), CW, 15, [fill_y[b] for b in bits], size=9.6)


def letter_strip(x, y, txt, hot=None):
    S.tokens(x, y - 7.5, list(txt), CW, 15, ["#FFFFFF" if not (hot and ch in hot) else C["sage"] for ch in txt], size=9.6)


rows = [50, 98, 146, 194]
# 1 text -> vowel / consonant (book page icon)
word = "moonlight"
y = rows[0]
for k in range(2, -1, -1):
    S.rect(8 + k * 2, y - 17 - k * 2 + 4, 26, 32, fill="#FFFFFF", stroke=INK, sw=0.8, rx=2, shadow=(k == 0))
S.poly([(28, y - 13), (34, y - 13), (34, y - 7)], fill="#E3E2E2", stroke=INK, sw=0.6)
for i in range(4):
    S.path("M13,%g L%g,%g" % (y - 5 + i * 5, 24 + (i % 2) * 4, y - 5 + i * 5), stroke="#9A9A9A", sw=1.1)
letter_strip(54, y, word, hot=VOWELS)
bit_strip(y, "".join("1" if c in VOWELS else "0" for c in word))
S.text(54, y + 20, "text: vowel / consonant", size=9.4, fill=C["gtxt"])
S.arrow([(54 + 9 * CW + 3, y), (STRIP_X - 3, y)], sw=0.9)
# 2 protein -> hydrophobic / polar (helix ribbon)
y = rows[1]
pro = "GVPGVGVPG"
xs = np.linspace(0, 1, 60)
for ph, col, wid in ((np.pi, "#C9A074", 4.5), (0, "#E08A5A", 5.5)):
    pts = [(12 + 30 * t, y + 8 * np.sin(2 * np.pi * 2.4 * t + ph)) for t in xs]
    d = "M" + " L".join("%.2f,%.2f" % q for q in pts)
    S.path(d, stroke="#6A3B1E", sw=wid + 1.6)
    S.path(d, stroke=col, sw=wid)
    S.path(d, stroke="#FFFFFF", sw=1.6, opacity=0.35)
letter_strip(54, y, pro, hot=HYDRO)
bit_strip(y, "".join("1" if c in HYDRO else "0" for c in pro))
S.text(54, y + 20, "protein: hydrophobic / polar", size=9.4, fill=C["gtxt"])
S.arrow([(54 + 9 * CW + 3, y), (STRIP_X - 3, y)], sw=0.9)
# 3 geyser -> long / short gap (plume + interval bars)
y = rows[2]
S.poly([(6, y + 16), (14, y + 8), (26, y + 5), (38, y + 8), (46, y + 16)], fill="#B7A58C", stroke="#6B5A43", sw=0.8)
for (cx, cy, r, op) in ((26, y - 2, 4.5, 0.95), (23, y - 9, 5.5, 0.9), (29, y - 15, 6, 0.85), (24, y - 20, 5, 0.75), (30, y - 23, 3.8, 0.6)):
    S.circle(cx, cy, r, fill="#F3F8FD", stroke="#9DB6CF", sw=0.7, opacity=op)
gaps = [79, 54, 74, 62, 85, 55, 88, 85, 51]
med = float(np.median(gaps))
for k, g in enumerate(gaps):
    hh = 17 * g / 88
    S.rect(54 + k * CW + 1.5, y + 8 - hh, CW - 3, hh, fill=C["neutral"], stroke=INK, sw=0.8)
S.path("M54,%g L%g,%g" % (y + 8 - 17 * med / 88, 54 + 9 * CW, y + 8 - 17 * med / 88), stroke=C["dred"], sw=0.9, dash="3 2")
bit_strip(y, "".join("1" if g > med else "0" for g in gaps))
S.text(54, y + 20, "geyser: gap > median", size=9.4, fill=C["gtxt"])
S.arrow([(54 + 9 * CW + 3, y), (STRIP_X - 3, y)], sw=0.9)
# 4 two models -> disagreement rounds
y = rows[3]
S.trapezoid(6, y - 15, 34, 28, C["pink"], letter="<i>f</i><sub>0</sub>", size=11)
S.trapezoid(46, y - 15, 34, 28, C["blue"], letter="<i>f</i><sub>1</sub>", size=11)
S.arrow([(82, y), (92, y)], sw=0.9)
for k in range(9):
    on = k not in (2, 5, 7)
    S.circle(100 + k * 7, y - 5, 2.6, fill=C["pink"], stroke=INK, sw=0.5, opacity=1 if on else 0.3)
    S.circle(100 + k * 7, y + 5, 2.6, fill=C["blue"] if on else C["pink"], stroke=INK, sw=0.5, opacity=1 if on else 0.3)
bit_strip(y, "011010011")
S.text(6, y + 26, "promotion: challenger wins a disagreement", size=9.4, fill=C["gtxt"])
S.arrow([(172, y), (STRIP_X - 3, y)], sw=0.9) if False else None
# converge to one bit stream
XM = 282
YM = (rows[0] + rows[3]) / 2
for yr in rows:
    S.path("M%g,%g L%g,%g L%g,%g" % (STRIP_X + 9 * CW + 4, yr, XM - 12, yr, XM - 12, YM), stroke=INK, sw=0.9)
S.arrow([(XM - 12, YM), (XM - 2, YM)], sw=0.9)
S.text(XM + 44, YM - 22, "one bit stream", size=10, weight="bold", fill=GT, anchor="middle")
S.tokens(XM, YM - 7.5, list("01101001"), CW, 15, [fill_y[b] for b in "01101001"], size=9.6)
S.lines(XM - 4, YM + 24, ["levels only,", "no differences:", "noise passes %d/%d," % (NOISE, NOISE_N), "real streams %d/%d" % (REAL_POS, REAL_N)], dy=10.5, size=9.4, fill=C["dred"], style="italic")
# gates inside a dashed group
GX0, GX1 = 382, 556
S.group_box(GX0, 40, GX1 - GX0, 152, "screen (fixed rule)", C["dblue"], tx=GX0 + 20)
S.text((GX0 + GX1) / 2, 62, "%d sources" % cnt["attempted"], size=9.8, weight="bold", fill=GT, anchor="middle")
S.text((GX0 + GX1) / 2, 74, "Phases 10, 10b, 10c", size=9.4, fill=C["gtxt"], anchor="middle")
S.arrow([(XM + 8 * CW + 3, YM), (GX0 - 1, YM)], sw=1)
names = [["\u2265200", "rounds,", "available"], ["fit", "<i>G</i><sub>1</sub>, <i>G</i><sub>2</sub>"], ["premium", "> 0"], ["shuffle", "control"]]
surv = [n_stream, n_fit, n_prem, n_prem]  # the last gate also holds the excluded Frisian stream (one more check, by source)
pitch = (GX1 - GX0 - 8) / 4
for k in range(4):
    cx = GX0 + 4 + pitch * (k + .5)
    hh = 44
    S.poly([(cx - 16, YM - 22), (cx + 16, YM - 22), (cx + 5, YM + 22), (cx - 5, YM + 22)], fill=S.grad("#FFFFFF", "#CFCECE", 0, 1), stroke=INK, sw=1.1, shadow=True)
    S.text(cx, YM - 28, str(surv[k]), size=12, weight="bold", anchor="middle")
    for i, ln in enumerate(names[k]):
        S.text(cx, YM + 36 + i * 10.5, ln, size=9.4, anchor="middle")
    if k:
        S.arrow([(cx - pitch + 16 + 3, YM), (cx - 16 - 2, YM)], sw=0.9)
# result
S.block_arrow(558, YM, 572, 22, C["blue2"])
S.text(596, YM + 7, str(N_SUP), size=22, weight="bold", fill=C["blue_main"], anchor="middle")
S.text(596, YM + 20, "supporting", size=9.4, fill=C["gtxt"], anchor="middle")
S.text(596, YM + 31, "%d new + %d" % (cnt["positive"], N_EARLIER), size=9.4, fill=C["gtxt"], anchor="middle")
S.text(596, YM + 42, "earlier", size=9.4, fill=C["gtxt"], anchor="middle")
S.rect(576, YM + 52, 39, 24, fill="url(#grid)", stroke=C["blue_main"], sw=0.6)
S.text(596, YM + 88, "%d settings" % N_SET, size=9.4, fill=C["gtxt"], anchor="middle")
S.text(2, AH - 10 + 0, "", size=9.4)
S.inline_svg(0, AH - 14, W, BH * 96, bars_svg)
S.text(2, AH + 6, "b", size=16, weight="bold")
S.text(458, AH + 6, "c", size=16, weight="bold")
S.save(HERE / "fig_screen")
print("wrote fig_screen", cnt, dict(kinds), N_SUP, N_SET, n_win, (n_stream, n_fit, n_prem))
