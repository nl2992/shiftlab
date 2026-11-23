"""Data panels for the hand-assembled composites (Python makes only the plots, as in the figures4papers miscellaneous set).

Writes transparent-background PNGs to assets_raw/: panel_exceedance.png (overview, panel b) and motif_1..4.png
(pipeline cards). Every value is read from the result files and asserted against tables/numbers.tex.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_hex
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from schematic import MONO, OUTLINE, macros
from shiftlab.paper3.riskbudget.real_streams import STREAMS
from style import CONFIGS, OUT, PALETTE as P, RES, apply_style, load_json

HERE = Path(__file__).resolve().parent
RAW = HERE / "assets_raw"
M = macros(HERE.parent / "tables/numbers.tex", HERE.parent / "tables/screen_numbers.tex")
apply_style(8)
DPI = 400


def save(fig, name):
    fig.savefig(RAW / name, dpi=DPI, transparent=True)
    plt.close(fig)


# ------------------------------------------------------------------ overview panel b: exceedance bars
conf = load_json(RES / "confirm_summary.json")
c3, c1, c2 = conf["C3"]["arms"], conf["C1"]["arms"], conf["C2"]["arms"]
bars = [("Wald cutoff", c3["wald_cut"], "r"), ("CUSUM", c3["cusum"], "r"), ("e-process gate", c3["gate_wald"], "r"),
        ("CUSUM rollback", c3["cusum_rb_h8"], "r"), ("stop-loss (told R)", c3["stoploss_R20"], "r"),
        ("shield, full", c1["f3_pi1_R20"], "b"), ("shield, paced", c2["f3v2d_R20"], "b")]
vals = [max(r["rate"] for r in a["per_regime"].values()) for _, a, _ in bars]
assert abs(vals[0] - float(M["WorstWald"])) < 1e-3 and abs(vals[4] - float(M["WorstStop"])) < 1e-3
fig = plt.figure(figsize=(1.97, 2.45))
ax = fig.add_axes([0.5, 0.15, 0.42, 0.62])
yy = list(range(len(bars)))[::-1]
for yi, (lab, a, k), v in zip(yy, bars, vals):
    col = P["red_strong"] if k == "r" else P["blue_main"]
    ax.barh(yi, v, color=col, height=0.62, edgecolor=OUTLINE, linewidth=0.6)
    ax.text(v + 0.04, yi, f"{v:.3f}".lstrip("0") if v else "0", va="center", fontsize=7.2, color=col, fontweight="bold" if k == "b" else "normal")
ax.set_yticks(yy)
ax.set_yticklabels([b[0] for b in bars], fontsize=7.2)
ax.set_xlim(0, 1.45)
ax.set_ylim(-0.6, len(bars) - 0.4)
ax.set_xticks([0, .5, 1])
ax.tick_params(axis="x", labelsize=7, length=3)
ax.tick_params(axis="y", length=0)
ax.text(0.85, 1.0, "never above R", fontsize=6.8, color=P["blue_main"], fontweight="bold", ha="center", va="center")
fig.text(0.03, 0.93, "budget exceedance", family=MONO, fontsize=8.4, fontweight="bold", va="center")
fig.text(0.03, 0.855, "share of runs above R=20,\nworst regime", fontsize=6.8, color=P["grey"], style="italic", va="center")
save(fig, "panel_exceedance.png")

# ------------------------------------------------------------------ pipeline motifs
SZ = (1.3, 1.0)
# 1: 30 regime tiles coloured by Wald exceedance
stress = [r["id"] for r in load_json(CONFIGS / "regimes_f3_v1.json")["regimes"]]
regs = list(c3["wald_cut"]["per_regime"])
order = [r for r in regs if r not in stress] + stress
rate = [c3["wald_cut"]["per_regime"][g]["rate"] for g in order]
cm = LinearSegmentedColormap.from_list("r", ["#FFFFFF", "#F2B8B2", "#B64342", "#5E1F1E"])
fig = plt.figure(figsize=SZ)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1.3); ax.set_ylim(0, 1.0); ax.axis("off")
tw, th, tg = 0.185, 0.12, 0.024
x0 = (1.3 - (6 * tw + 5 * tg)) / 2
for i, v in enumerate(rate):
    r_, c_ = divmod(i, 6)
    ax.add_patch(FancyBboxPatch((x0 + c_ * (tw + tg), 0.75 - r_ * (th + tg)), tw, th, boxstyle="round,pad=0,rounding_size=0.025",
                                fc=to_hex(cm(min(1, v / 0.9))), ec=OUTLINE, lw=0.6))
ax.text(x0 + 6 * (tw + tg) - tg, 0.75 - 4 * (th + tg) - 0.055, "stress regimes", fontsize=7.2, color=P["red_strong"], ha="right", va="center", style="italic")
ax.text(x0, 0.985, "Wald share above R", fontsize=6.6, family=MONO, color=P["grey"], va="top")
save(fig, "motif_1.png")

# 2: stop-loss margin line
Rv, kv, cs = 20.0, 3.0, float(M["CalStopCB"])
fig = plt.figure(figsize=SZ)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1.3); ax.set_ylim(0, 1.0); ax.axis("off")
lx0, lx1, ly = 0.1, 1.2, 0.45
fx = lambda c: lx0 + (lx1 - lx0) * c / Rv
ax.add_patch(Polygon([(fx(0), ly - .08), (fx(Rv - 2 * kv), ly - .08), (fx(Rv - 2 * kv), ly + .08), (fx(0), ly + .08)], fc="#DFF1DF", ec=OUTLINE, lw=0.7))
ax.add_patch(Polygon([(fx(Rv - 2 * kv), ly - .08), (fx(Rv), ly - .08), (fx(Rv), ly + .08), (fx(Rv - 2 * kv), ly + .08)], fc="#F6D5D2", ec=OUTLINE, lw=0.7))
ax.text((fx(0) + fx(Rv - 2 * kv)) / 2, ly, "possible", fontsize=7, ha="center", va="center", color="#3F7F3B")
ax.text((fx(Rv - 2 * kv) + fx(Rv)) / 2, ly, "none", fontsize=7, ha="center", va="center", color=P["red_strong"])
for c, lab in ((0, "0"), (Rv - 2 * kv, "R$-$2k"), (Rv, "R")):
    ax.plot([fx(c)] * 2, [ly - .08, ly - .14], color=OUTLINE, lw=0.7)
    ax.text(fx(c), ly - .22, lab, fontsize=7.2, ha="center", va="center")
ax.add_patch(Polygon([(fx(cs), ly + .11), (fx(cs) - .05, ly + .22), (fx(cs) + .05, ly + .22)], fc=P["red_strong"], ec=OUTLINE, lw=0.6))
ax.text(lx0, 0.93, "stop-loss margin c", fontsize=6.6, family=MONO, color=P["grey"], va="center")
ax.text(fx(cs) + .02, ly + .33, "first c that\nmeets .05", fontsize=7, color=P["red_strong"], fontweight="bold", style="italic", ha="right", va="center", linespacing=1.1)
save(fig, "motif_2.png")

# 3: per-stream shield cost vs never (h = 14, clean)
rs = json.loads((HERE.parent.parents[1] / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget/real_summary.json").read_text())
st = rs["results"]["clean"]["streams"]
gains = sorted([(-st[s]["arms"]["f3_pi1_h14"]["d_never"]["delta"], s) for s in STREAMS], reverse=True)
mx = max(abs(g) for g, _ in gains)
fig = plt.figure(figsize=SZ)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1.3); ax.set_ylim(0, 1.0); ax.axis("off")
bw_, bg_ = 0.07, 0.019
bx0 = (1.3 - (12 * bw_ + 11 * bg_)) / 2
by0 = 0.38
ax.plot([bx0 - 0.03, bx0 + 12 * bw_ + 11 * bg_ + 0.03], [by0, by0], color=OUTLINE, lw=0.8)
for i, (g, s) in enumerate(gains):
    h = 0.5 * g / mx
    ax.add_patch(FancyBboxPatch((bx0 + i * (bw_ + bg_), min(by0, by0 + h)), bw_, abs(h), boxstyle="round,pad=0,rounding_size=0.012",
                                fc="#5C93D1" if g > 0 else "#E08A84", ec=OUTLINE, lw=0.55))
ax.text(bx0, 0.96, "shield cost vs never", fontsize=6.6, family=MONO, color=P["grey"], va="center")
ax.text(bx0 + 12 * bw_ + 11 * bg_, 0.14, "airlines, bank: harmful", fontsize=6.8, color=P["red_strong"], style="italic", va="center", ha="right")
save(fig, "motif_3.png")

# 4: 100 dots, S2 met vs not
tally = json.loads((OUT / "screen100/tally.json").read_text())["rows"]
sup = sorted([r for r in tally if r["status"] == "supported"], key=lambda r: -r["shield_gain_vs_never"])
non = [r for r in tally if r["status"] != "supported"]
fig = plt.figure(figsize=SZ)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1.3); ax.set_ylim(0, 1.0); ax.axis("off")
dsp, dr = 0.113, 0.043
dx0 = (1.3 - 9 * dsp) / 2
for i, r in enumerate(sup + non):
    rr, cc = divmod(i, 10)
    ok = r["status"] == "supported"
    ax.add_patch(Circle((dx0 + cc * dsp, 0.9 - rr * 0.085), dr * 0.8, fc="#4A82C4" if ok else "#E6E6E6",
                        ec=P["red_strong"] if not r["S1"] else (OUTLINE if ok else "#BDBDBD"), lw=1.2 if not r["S1"] else 0.5))
save(fig, "motif_4.png")
print("wrote panels", [round(v, 3) for v in vals])
