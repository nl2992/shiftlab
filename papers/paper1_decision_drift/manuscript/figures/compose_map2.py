"""Detectability figure after Dispersion observation/distillation: heatmap with a dashed frontier and bold on-plot labels,
direct-labelled lines, curly brace + pale blue note. Data: outputs/r7_sweep/streams.parquet.
Run from the worktree root: PYTHONPATH=. .venv/bin/python papers/paper1_decision_drift/manuscript/figures/compose_map2.py
"""
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from glyphs import SEM, brace_down  # noqa: E402
from svgkit import C, MONO, Svg  # noqa: E402

d = pd.read_parquet(HERE.parents[3] / "outputs/r7_sweep/streams.parquet")
d = d[d.onset.notna()]
g = d[d.arm == "gated_ht_fixed"].groupby(["adaptation_strength", "budget_rate"]).detected.mean().unstack()
u = d[d.arm == "uniform_ppi"].groupby(["adaptation_strength", "budget_rate"]).detected.mean().unstack()
assert g.loc[:, [0.02, 0.05]].values.max() <= 0.29 and u.loc[:, [0.02, 0.05]].values.max() == 0.0
rows = list(g.index)[::-1]
cols = list(g.columns)


def lerp(c0, c1, t):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


W, H = 624, 300
S = Svg(W, H)
S.text(2, 20, "a", size=16, weight="bold")
S.text(22, 19, "Gated, fixed rate", size=11.5, family=MONO, weight="bold", fill=SEM["ours"])
CW, CH, X0, Y0 = 42, 30, 52, 36
for i, s_ in enumerate(rows):
    S.text(X0 - 8, Y0 + i * CH + CH / 2 + 3.5, "%g" % s_, size=9.6, anchor="end", fill=C["mid"])
    for j, r in enumerate(cols):
        v = float(g.loc[s_, r])
        S.rect(X0 + j * CW, Y0 + i * CH, CW, CH, fill=lerp("#FBF3EF", "#7FB0DC", v) if False else lerp("#F3F8FD", "#0F4D92", v ** 0.85),
               stroke="#FFFFFF", sw=1.2)
        S.text(X0 + j * CW + CW / 2, Y0 + i * CH + CH / 2 + 3.5, "%.2f" % v, size=9.4, anchor="middle", fill="#FFFFFF" if v > 0.5 else C["ink"])
for j, r in enumerate(cols):
    S.text(X0 + j * CW + CW / 2, Y0 + len(rows) * CH + 13, "%.2f" % r, size=9.6, anchor="middle", fill=C["mid"])
S.text(X0 + len(cols) * CW / 2, Y0 + len(rows) * CH + 27, "label budget <i>r</i>", size=9.8, anchor="middle", fill="#3F3F3F")
S.text(12, Y0 + len(rows) * CH / 2, "intervention strength <i>s</i>", size=9.8, anchor="middle", fill="#3F3F3F",
       extra='transform="rotate(-90 12 %g)"' % (Y0 + len(rows) * CH / 2))
# dashed frontier at detection 0.5 (edges between detected and undetected cells)
m = g.loc[rows].values >= 0.5
for i in range(m.shape[0]):
    for j in range(m.shape[1]):
        if not m[i, j]:
            continue
        x, y = X0 + j * CW, Y0 + i * CH
        for di, dj, seg in ((-1, 0, (x, y, x + CW, y)), (1, 0, (x, y + CH, x + CW, y + CH)),
                            (0, -1, (x, y, x, y + CH)), (0, 1, (x + CW, y, x + CW, y + CH))):
            ni, nj = i + di, j + dj
            if 0 <= ni < m.shape[0] and 0 <= nj < m.shape[1] and not m[ni, nj]:
                S.path("M%g,%g L%g,%g" % seg, stroke=C["dblue"] if "dblue" in C else "#1B3A6B", sw=2.4, dash="6 3")
# on-plot labels, right margin
S.text(X0 + len(cols) * CW + 10, Y0 + 20, "<b><i><c #0F4D92>detectable</c></i></b>", size=11.5)
S.text(X0 + len(cols) * CW + 10, Y0 + 34, "<i><c #0F4D92>(≥ 0.5)</c></i>", size=9.6)
S.text(X0 + len(cols) * CW + 10, Y0 + 5 * CH - 14, "<b><i><c #B64342>not detectable</c></i></b>", size=11.5)
S.text(X0 + len(cols) * CW + 10, Y0 + 5 * CH, "<i><c #B64342>at this budget</c></i>", size=9.6)
# curly brace under r <= 0.05 and the pale blue note
bx0, bx1, by = X0 + 2, X0 + 2 * CW - 2, Y0 + len(rows) * CH + 33
brace_down(S, bx0, bx1, by, h=6)
S.text((bx0 + bx1) / 2, by + 26, "<b>r ≤ 0.05</b>", size=10.5, anchor="middle")
S.rect(8, 250, 288, 44, fill="#E3EFFB", rx=12)
S.text(152, 266, "Gated monitors stay <b>≤ 0.29</b> at every strength", size=10, anchor="middle")
S.text(152, 282, "when <i>r</i> ≤ 0.05; uniform labelling detects <b>0.00</b>.", size=10, anchor="middle")

# ---- b: direct-labelled lines
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica", "Arial"], "svg.fonttype": "none", "font.size": 9,
                     "axes.linewidth": 1.1, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(3.45, 2.7))
ss = list(g.index)
shades = {0.05: "#9DBFE3", 0.10: "#3775BA", 0.20: "#0F4D92"}
for r, col in shades.items():
    ax.plot(ss, g[r].values, marker="o", ms=4, color=col, lw=2.0)
    ax.text(ss[-1] + 0.03, g[r].values[-1] + {0.10: -0.03, 0.20: 0.025}.get(r, 0), "gated, $r$=%g" % r, color=col, fontsize=8.5, va="center", fontweight="bold")
ax.plot(ss, u[0.20].values, marker="o", ms=4, color=SEM["uniform"], lw=2.0, ls="--")
ax.text(ss[-1] + 0.03, u[0.20].values[-1] + 0.0, "uniform, $r$=0.20", color=SEM["uniform"], fontsize=8.5, va="center", fontweight="bold")
ax.set_xlim(0.08, 1.42)
ax.set_ylim(-0.02, 1.1)
ax.set_xticks(ss, ["%g" % s_ for s_ in ss])
ax.set_xlabel("intervention strength $s$")
ax.set_ylabel("detection probability")
buf = io.StringIO()
fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
t = buf.getvalue()
S.text(318, 20, "b", size=16, weight="bold")
S.inline_svg(326, 28, 292, 252, t[t.index("<svg"):])
S.save(HERE / "fig_map2")
print("ok")
