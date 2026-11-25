"""Growth figure after VIGIL (b): stacked equation boxes under a curly brace (changed terms in magenta), data panel with the
"ours" series bold and baselines pale, on-plot bold annotation. Values: scripts/g1_kelly_check.py and the results doc.
Run from the worktree root: PYTHONPATH=. .venv/bin/python papers/paper1_decision_drift/manuscript/figures/compose_growth2.py
"""
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from glyphs import SEM, brace_left  # noqa: E402
from svgkit import C, Svg  # noqa: E402

SERIF = "'Times New Roman', Times, serif"
budgets = [0.02, 0.05, 0.10, 0.20]
uncapped = [12.4, 12.5, 10.1, 5.1]
kelly = [20.0, 19.7, 15.5, 7.6]
pred = [18, 18, 15, 7.5]
meas = [17.5, 20.6, 14.7, 7.2]
assert max(abs(k / m - 1) for k, m in zip(kelly, meas)) < 0.16

# ---- data panel (pale baselines, bold ours, on-plot annotation, legend below with ours in bold)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica", "Arial"], "svg.fonttype": "none",
                     "font.size": 9, "axes.linewidth": 1.1, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(3.15, 2.45))
x = np.arange(4)
w = 0.26
ec = dict(edgecolor="#272727", linewidth=1.0)
ax.bar(x - w, uncapped, w, color="#DCE9F6", label="Variance ratio", **ec)
ax.bar(x, kelly, w, color="#9DBFE3", label="Growth calculation", **ec)
b3 = ax.bar(x + w, meas, w, color=SEM["ours"], label="Measured", **ec)
ax.scatter(x, pred, marker="D", s=22, color=SEM["uniform"], zorder=5, edgecolor="white", lw=0.6, label="Registered prediction")
for xi, v, p in zip(x + w, meas, pred):
    ax.text(xi + 0.02, max(v, p) + 1.1, "%g" % v, ha="center", fontsize=8.5)
ax.set_xticks(x, ["%.2f" % b for b in budgets])
ax.set_xlabel("label budget $r$")
ax.set_ylabel("gated / uniform evidence growth")
ax.set_ylim(0, 31)
ax.text(1.5, 27.2, "growth calculation within 15%", ha="center", fontsize=9.5, fontweight="bold", fontstyle="italic", color=SEM["ours"])
ax.text(1.5, 24.2, "of measured at every budget", ha="center", fontsize=9, fontstyle="italic", color=SEM["ours"])
leg = ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.27), ncol=2, frameon=False, fontsize=8.5, handlelength=1.1, columnspacing=1.0)
for t in leg.get_texts():
    if t.get_text() == "Measured":
        t.set_fontweight("bold")
buf = io.StringIO()
fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
asset = buf.getvalue()
asset = asset[asset.index("<svg"):]

W, H = 624, 232
S = Svg(W, H)
S.text(2, 17, "a", size=16, weight="bold")
S.text(392, 17, "b", size=16, weight="bold")
# left text column
LC = SEM["ours"]
S.text(10, 56, "Same label spend <i>r</i>.", size=10.5, fill=LC)
S.text(10, 71, "What changes is the", size=10.5, fill=LC)
S.text(10, 88, "<m>second moment</m>", size=10, fill=LC)
S.text(10, 103, "and the", size=10.5, fill=LC)
S.text(10, 120, "<m>support bound</m>", size=10, fill=LC)
S.text(10, 135, "<i>B</i> of the increment.", size=10.5, fill=LC)
brace_left(S, 128, 30, 214, w=8)
BX, BW = 140, 238
M = SEM["magenta"]
# green: growth definition
S.rect(BX, 30, BW, 44, fill=SEM["cost_l"], stroke=SEM["cost"], sw=1.5, rx=8)
S.text(BX + BW / 2, 49, "<i>G</i> = <i>E</i> log( 1 + <i>s</i> <i>Z</i> / <i>B</i> )", size=12, family=SERIF, anchor="middle")
S.text(BX + BW / 2, 65, "per-event log-growth of the betting e-process", size=9.2, anchor="middle", fill=C["mid"])
# pink: uniform
S.rect(BX, 82, BW, 64, fill=SEM["uniform_l"], stroke=SEM["uniform"], sw=1.5, rx=8)
S.text(BX + 10, 100, "<b><c #8B1E1E>Uniform</c></b>", size=9.8)
S.text(BX + BW / 2 + 22, 100, "<i>Z</i> = −ε + <i>L</i> <i>c</i> / <i>r</i>", size=11, family=SERIF, anchor="middle")
Lbar = 150.0
S.rect(BX + 10, 114, Lbar, 11, fill=SEM["uniform"], stroke=None, rx=2)
S.text(BX + 10 + Lbar + 5, 123, "<i>B</i> = 45.9", size=9.6, weight="bold", fill=C["dred"])
S.text(BX + 10, 140, "every event is a candidate for a label", size=9.2, fill=C["mid"])
# blue: gated (ours), changed terms in magenta
S.rect(BX, 154, BW, 64, fill="#DCE9F6", stroke=SEM["ours"], sw=1.5, rx=8)
S.text(BX + 10, 172, "<b><c #0F4D92>Gated (ours)</c></b>", size=9.8)
S.text(BX + BW / 2 + 22, 172, "<i>Z</i> = −ε + <c %s><i>A</i></c> <i>L</i> <i>c</i> / <c %s><i>q</i></c>" % (M, M), size=11, family=SERIF, anchor="middle")
S.rect(BX + 10, 186, Lbar * 5.1 / 45.9, 11, fill=SEM["ours"], stroke=None, rx=2)
S.text(BX + 10 + Lbar * 5.1 / 45.9 + 5, 195, "<i>B</i> = 5.1", size=9.6, weight="bold", fill=SEM["ours"])
S.text(BX + 10, 212, "only disagreements (<c %s><i>A</i> = 1</c>) are queried" % M, size=9.2, fill=C["mid"])
S.text(BX + BW - 6, 212, "<i>r</i> = 0.20", size=9.2, anchor="end", fill=C["gtxt"], style="italic")
S.inline_svg(394, 22, 224, 204, asset)
S.save(HERE / "fig_growth2")
print("ok")
