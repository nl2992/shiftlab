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

# ---------------------------------------------------------------- composed panel (a)
W = 624
H = 280
S = Svg(W, H)
INK, GT = C["ink"], "#3F3F3F"
OL = "#4D4D4D"
S.text(2, 14, "Sources", size=11.5, weight="bold", fill=C["dsage"])
CW = 14.0
fill_y = {"0": C["pink"], "1": C["blue"]}
LX = 50
STRIP_X = 196


def strip(x, y, txt, fills):
    """One continuous token strip: tinted backgrounds, a single thin outer border, Courier bold letters."""
    n = len(txt)
    for k, f in enumerate(fills):
        if f != "#FFFFFF":
            S.rect(x + k * CW, y - 9, CW, 18, fill=f)
    S.rect(x, y - 9, n * CW, 18, fill="none", stroke=INK, sw=0.8)
    for k, ch in enumerate(txt):
        S.text(x + (k + .5) * CW, y + 3.6, ch, size=10, anchor="middle", family=MONO, weight="bold")


def letter_strip(y, txt, hot):
    strip(LX, y, txt, [C["sage"] if ch in hot else "#FFFFFF" for ch in txt])


def bit_strip(y, bits):
    strip(STRIP_X, y, bits, [fill_y[b] for b in bits])


rows = [50, 98, 146, 194]
# 1 text -> vowel / consonant (folded page)
word = "moonlight"
y = rows[0]
for k in range(2, -1, -1):
    S.rect(8 + k * 2, y - 17 - k * 2 + 4, 26, 32, fill="#FFFFFF", stroke=OL, sw=1.2, rx=2)
S.poly([(28, y - 13), (34, y - 13), (34, y - 7)], fill="#E3E2E2", stroke=OL, sw=0.8)
for i in range(4):
    S.path("M13,%g L%g,%g" % (y - 5 + i * 5, 24 + (i % 2) * 4, y - 5 + i * 5), stroke="#9A9A9A", sw=1.1)
letter_strip(y, word, VOWELS)
bit_strip(y, "".join("1" if c in VOWELS else "0" for c in word))
S.text(LX, y + 24, "text: vowel / consonant", size=9.4, fill=C["gtxt"])
S.arrow([(LX + 9 * CW + 4, y), (STRIP_X - 4, y)], sw=0.9)
# 2 protein -> hydrophobic / polar (folded ribbon, two turns)
y = rows[1]
pro = "GVPGVGVPG"
up = [(8 + 36 * t, y - 4 + 11 * np.sin(2 * np.pi * 2 * t)) for t in np.linspace(0, 1, 40)]
dn = [(x_, y_ + 9) for x_, y_ in up[::-1]]
S.poly(up + dn, fill="#F6D5BF", stroke=OL, sw=1.2)
for t in (0.25, 0.75):
    xx = 8 + 36 * t
    S.path("M%.1f,%.1f L%.1f,%.1f" % (xx, y - 4 + 11 * np.sin(2 * np.pi * 2 * t), xx, y + 5 + 11 * np.sin(2 * np.pi * 2 * t)), stroke=OL, sw=0.9)
letter_strip(y, pro, HYDRO)
bit_strip(y, "".join("1" if c in HYDRO else "0" for c in pro))
S.text(LX, y + 24, "protein: hydrophobic / polar", size=9.4, fill=C["gtxt"])
S.arrow([(LX + 9 * CW + 4, y), (STRIP_X - 4, y)], sw=0.9)
# 3 geyser -> long / short gap (asymmetric jet over a low mound)
y = rows[2]
S.poly([(4, y + 16), (14, y + 9), (28, y + 6), (42, y + 9), (50, y + 16)], fill="#E4D6C0", stroke=OL, sw=1.2)
S.path("M21,%g C20,%g 24,%g 37,%g C31,%g 33,%g 32,%g Z" % (y + 7, y - 9, y - 17, y - 26, y - 14, y - 3, y + 7),
       fill="#CFE3F6", stroke=OL, sw=1.2)
S.circle(40, y - 15, 2, fill="#CFE3F6", stroke=OL, sw=0.8)
S.circle(44, y - 8, 1.6, fill="#CFE3F6", stroke=OL, sw=0.8)
gaps = [79, 54, 74, 62, 85, 55, 88, 85, 51]
med = float(np.median(gaps))
for k, g in enumerate(gaps):
    hh = 17 * g / 88
    S.rect(LX + k * CW + 2.5, y + 8 - hh, CW - 5, hh, fill=C["neutral"], stroke=INK, sw=0.8)
S.path("M%g,%g L%g,%g" % (LX, y + 8 - 17 * med / 88, LX + 9 * CW, y + 8 - 17 * med / 88), stroke=C["dred"], sw=0.9, dash="3 2")
bit_strip(y, "".join("1" if g > med else "0" for g in gaps))
S.text(LX, y + 24, "geyser: gap > median", size=9.4, fill=C["gtxt"])
S.arrow([(LX + 9 * CW + 4, y), (STRIP_X - 4, y)], sw=0.9)
# 4 two models -> disagreement rounds
y = rows[3]
S.trapezoid(2, y - 15, 24, 28, C["pink"], letter="<i>f</i><sub>0</sub>", size=9.6)
S.trapezoid(28, y - 15, 24, 28, C["blue"], letter="<i>f</i><sub>1</sub>", size=9.6)
for k in range(9):
    on = k not in (2, 5, 7)
    S.circle(LX + k * CW + CW / 2, y - 5, 3.4, fill=C["pink"], stroke=INK, sw=0.6, opacity=1 if on else 0.3)
    S.circle(LX + k * CW + CW / 2, y + 5, 3.4, fill=C["blue"] if on else C["pink"], stroke=INK, sw=0.6, opacity=1 if on else 0.3)
bit_strip(y, "011010011")
S.text(LX, y + 24, "promotion: challenger wins a disagreement", size=9.4, fill=C["gtxt"])
S.arrow([(LX + 9 * CW + 4, y), (STRIP_X - 4, y)], sw=0.9)
# converge to one bit stream (individual cells kept); the count sequence runs down the empty right-hand column
BUS = 342
XM = 358
CW2 = 13.0
YM = (rows[0] + rows[3]) / 2
for yr in rows:
    S.path("M%g,%g L%g,%g L%g,%g" % (STRIP_X + 9 * CW + 4, yr, BUS, yr, BUS, YM), stroke=INK, sw=0.9)
S.arrow([(BUS, YM), (XM - 3, YM)], sw=0.9)
S.text(XM + 4 * CW2, YM - 18, "one bit stream", size=10, weight="bold", fill=GT, anchor="middle")
S.tokens(XM, YM - 7.5, list("01101001"), CW2, 15, [fill_y[b] for b in "01101001"], size=9.6)
# the screen as a flow of gates (no counts): bit stream -> four gates -> supporting datasets -> panel settings
BXL, BXW, BHT = 482, 136, 26
gates = [["enough rounds to fit"], ["two-state fit passes", "<i>G</i><sub>1</sub> and <i>G</i><sub>2</sub>"], ["premium > 0 and", "VoI ≥ 0.1 in some cell"],
         ["time-shuffle control"]]
ys_ = [34 + 50 * i for i in range(4)]
S.text(BXL + BXW / 2, 12, "screen", size=10, weight="bold", fill=GT, anchor="middle")
S.path("M%g,%g L%g,%g L%g,%g" % (XM + 8 * CW2 + 2, YM, BXL - 10, YM, BXL - 10, ys_[0]), stroke=INK, sw=1)
S.arrow([(BXL - 8, ys_[0]), (BXL - 2, ys_[0])], sw=1)
for i, g in enumerate(gates):
    S.rect(BXL, ys_[i] - BHT / 2, BXW, BHT, fill="#FFFFFF", stroke=OL, sw=1.1, rx=6)
    y0 = ys_[i] + 3.3 - (len(g) - 1) * 5.25
    for j, ln in enumerate(g):
        S.text(BXL + BXW / 2, y0 + j * 10.5, ln, size=9.4, anchor="middle", fill=GT)
    yb = ys_[i + 1] - BHT / 2 if i < 3 else ys_[3] + 36
    S.arrow([(BXL + BXW / 2, ys_[i] + BHT / 2), (BXL + BXW / 2, yb - 2)], sw=1)
YS = ys_[3] + 36
S.rect(BXL, YS, BXW, 30, fill=C["blue"], stroke=C["blue_main"], sw=1.3, rx=6)
S.text(BXL + BXW / 2, YS + 19.5, "%d supporting datasets" % N_SUP, size=10.5, weight="bold", fill=C["blue_main"], anchor="middle")
S.text(BXL + BXW / 2, YS + 48, "\u00d7 12 settings = %d" % N_SET, size=10.5, weight="bold", fill=GT, anchor="middle")
S.save(HERE / "fig_screen")
print("wrote fig_screen", N_SUP, N_SET)
