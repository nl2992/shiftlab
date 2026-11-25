"""Figure 1 (composed schematic, figures4papers "Miscellaneous" look; toolchain copied from the Paper 4 figures).

(a) the monitoring problem, (b) standard vs ours on one real stream, (c) real log-evidence curves.
Panel b strips and label purchases and panel c curves come from running the repository's replay code on one
boundary_local_harm stream at r = 0.05 (make_overview.run); (a) is a schematic. Numbers are asserted below.
Run from the worktree root:  PYTHONPATH=. .venv/bin/python papers/paper1_decision_drift/manuscript/figures/compose_fig1.py
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
sys.path.insert(0, str(HERE.parents[3] / "src"))
from make_overview import ALPHA, R, alarm, pick_seed  # noqa: E402
from svgkit import C, MONO, Svg  # noqa: E402

# ------------------------------------------------------------------ data
seed, act, out = pick_seed()
N = 2400
ONSET = 800
q_g = np.zeros(N, bool)
q_g[: len(out["gated_ht_fixed"][1])] = out["gated_ht_fixed"][1]
q_u = out["uniform"][1]
assert not (q_g & ~act).any(), "gated labels must sit on disagreements"
# a 100-event post-onset window with at least four labels for each rule (cosmetic choice, not tuned to a result)
WIN = 100
start = next(s for s in range(ONSET + 100, N - WIN) if q_g[s:s + WIN].sum() >= 4 and q_u[s:s + WIN].sum() >= 4
             and act[s:s + WIN].sum() >= 8)
sl = slice(start, start + WIN)
a_w, g_w, u_w = act[sl], q_g[sl], q_u[sl]
n_g, n_u, n_u_on = int(g_w.sum()), int(u_w.sum()), int((u_w & a_w).sum())
assert n_g == int((g_w & a_w).sum())
alarms = {k: alarm(out[k][0]) for k in out}
assert alarms["uniform"] is None and all(alarms[k] is not None for k in ("full", "gated_ht_fixed", "gated_ht_paced"))
DIS = float(act[ONSET:].mean())

# ------------------------------------------------------------------ real evidence curves as a vector asset
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica", "Arial"], "svg.fonttype": "none",
                     "font.size": 7.5, "axes.linewidth": 1.0, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(3.2, 2.05))
spec = [("full", "Full feedback", C["ink"], "--"), ("gated_ht_fixed", "Gated, fixed rate", C["blue_main"], "-"),
        ("gated_ht_paced", "Gated, paced", C["blue2"], "-"), ("uniform", "Uniform", C["red"], "-")]
for key, name, col, ls in spec:
    le = np.asarray(out[key][0])
    ax.plot(np.arange(len(le)), le, color=col, ls=ls, lw=1.6, label=name)
    a = alarm(le)
    if a is not None:
        ax.plot(a, le[a], "o", color=col, ms=4, zorder=5)
ax.axhline(-np.log(ALPHA), color=C["gtxt"], lw=0.8, ls=":")
ax.text(N - 20, -np.log(ALPHA) + 0.15, "alarm: log(1/α)", ha="right", va="bottom", fontsize=7, color=C["gtxt"])
ax.axvline(ONSET, color=C["ink"], lw=0.8, ls="--")
ax.set_xlim(0, N)
ax.set_ylim(-1, 12)
ax.set_xlabel("monitored events", labelpad=1)
ax.set_ylabel("log-evidence", labelpad=1)
leg = ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="none", framealpha=1, fontsize=7, handlelength=1.6, borderaxespad=0.1)
leg.set_zorder(10)
buf = io.StringIO()
fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
curves_svg = buf.getvalue()
curves_svg = curves_svg[curves_svg.index("<svg"):]

# ------------------------------------------------------------------ canvas
W, H = 624, 392
S = Svg(W, H)
GT = "#3F3F3F"
INK = C["ink"]

# ================================================================= a  the monitoring problem
S.text(2, 15, "a", size=16, weight="bold")
S.text(20, 14, "The monitoring problem", size=11.5, weight="bold", fill=GT)
for k in range(3):
    S.rect(10 + k * 3, 46 + k * 3, 30, 36, fill="#FFFFFF", stroke=INK, sw=0.9, rx=3, shadow=(k == 2))
S.text(28, 70, "<i>x<sub>t</sub></i>", size=11, anchor="middle")
S.text(28, 108, "events", size=9.6, fill=C["gtxt"], anchor="middle")
S.text(82, 30, "deployed", size=9.8, weight="bold", fill=C["dred"], anchor="middle")
S.trapezoid(54, 34, 56, 34, C["pink"], letter="<i>π</i>", size=13)
S.text(82, 98, "reference", size=9.8, weight="bold", fill=C["dblue"], anchor="middle")
S.trapezoid(54, 102, 56, 34, C["blue"], letter="<i>π</i><sub>ref</sub>", size=12)
S.arrow([(46, 62), (50, 62), (50, 51), (53, 51)], sw=0.9)
S.arrow([(46, 72), (50, 72), (50, 119), (53, 119)], sw=0.9)

x0, pitch, K = 124, 11.2, 14
agree_k = {1, 2, 4, 5, 6, 8, 9, 11, 12}  # most events agree
rowpred = [(1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 0), (0, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0)]
fillc = {0: C["pink"], 1: C["blue"]}
S.text(x0 + K * pitch / 2, 30, "decision of each policy", size=9.8, weight="bold", fill=GT, anchor="middle")
for k in range(K):
    cx = x0 + k * pitch + 5
    p = list(rowpred[0][k:k + 1] + rowpred[1][k:k + 1])
    if k in agree_k:
        p[1] = p[0]
    op = 0.32 if k in agree_k else 1
    for rr, yy in ((0, 50), (1, 120)):
        S.circle(cx, yy, 4.6, fill=fillc[p[rr]], stroke=INK, sw=0.8, opacity=op)
    if k in agree_k:
        S.path("M%g,57 L%g,113" % (cx, cx), stroke="#9A9A9A", sw=0.8, dash="2 2")
        S.text(cx, 89, "=", size=10, anchor="middle", fill="#9A9A9A")
    else:
        S.path("M%g,57 L%g,113" % (cx, cx), stroke="#272727", sw=0.8)
        S.text(cx, 89, "≠", size=10, anchor="middle", fill=C["dred"], weight="bold")
S.arrow([(111, 51), (119, 51)], sw=0.9)
S.arrow([(111, 119), (119, 119)], sw=0.9)
S.text(x0 + K * pitch / 2, 141, "agreement: paired cost is exactly 0", size=9.5, fill=C["gtxt"], anchor="middle")

S.block_arrow(292, 85, 322, 22, C["blue2"])
# the kept events become cost labels bought with coins
KX, KW = 334, 17
cost_tok = ["+5", "?", "?", "−1", "?"]
fills = [C["pink"], C["grey"], C["grey"], C["blue"], C["grey"]]
S.tokens(KX, 76, cost_tok, KW, 22, fills, size=9.6)
for k in (0, 3):
    S.coin(KX + (k + .5) * KW, 65, 6)
S.text(KX + 2.5 * KW, 50, "label bought only", size=9.8, weight="bold", fill=GT, anchor="middle")
S.text(KX + 2.5 * KW, 113, "on a disagreement", size=9.6, fill=C["gtxt"], anchor="middle")
S.block_arrow(432, 85, 462, 22, C["blue2"])
S.text(472, 62, "evidence", size=9.8, weight="bold", fill=GT)
S.text(472, 74, "≥ 1/α ?", size=10.5, family="'Times New Roman', Times, serif", fill=GT, style="italic")
x_, y_, s_ = 580, 62, 30
S.path("M%g,%g L%g,%g L%g,%g Q%g,%g %g,%g Q%g,%g %g,%g L%g,%g Z" % (x_, y_, x_ + s_, y_, x_ + s_, y_ + s_ * .55, x_ + s_, y_ + s_ * 1.05,
       x_ + s_ / 2, y_ + s_ * 1.3, x_, y_ + s_ * 1.05, x_, y_ + s_ * .55, x_, y_), fill=C["pink"], stroke=C["dred"], sw=1.2)
S.text(x_ + s_ / 2, y_ + s_ * 0.72, "!", size=19, weight="bold", fill=C["dred"], anchor="middle")
S.text(595, 113, "harm alarm", size=9.8, weight="bold", fill=C["dred"], anchor="middle")
S.arrow([(520, 84), (574, 84)], sw=1.2, col=GT)

# ================================================================= b  standard vs ours on one real stream
BX, BY, BW, BH = 6, 178, 298, 206
S.text(2, 166, "b", size=16, weight="bold")
S.group_box(BX, BY, BW, BH, "Equal budget, different use", GT, tx=BX + 14, tsize=10.5)
SX, SWD = BX + 12, (BW - 24) / WIN


def strip(y, queried, tag, tcol, phrase, pcol):
    S.text(SX, y - 22, tag, size=10.5, weight="bold", fill=tcol)
    for i in range(WIN):
        S.rect(SX + i * SWD, y, SWD + 0.15, 18, fill=C["pink"] if a_w[i] else "#F1F0F0", stroke=None)
    for i in np.flatnonzero(queried):
        S.coin(SX + (i + .5) * SWD, y - 8, 4.6)
        S.path("M%g,%g L%g,%g" % (SX + (i + .5) * SWD, y - 3, SX + (i + .5) * SWD, y), stroke="#8A6A12", sw=0.6)
    S.text(SX, y + 33, phrase, size=10, weight="bold", fill=pcol)


strip(BY + 46, u_w, "Uniform labelling (standard)", C["red"],
      "%d of %d labels land on agreements" % (n_u - n_u_on, n_u), C["red"])
strip(BY + 128, g_w, "Gated on disagreement (ours)", C["blue_main"],
      "all %d labels land on disagreements" % n_g, C["blue_main"])
S.rect(SX, BY + 168, 8, 8, fill=C["pink"])
S.text(SX + 12, BY + 176, "policies disagree", size=9.4, fill=C["gtxt"])
S.rect(SX + 98, BY + 168, 8, 8, fill="#F1F0F0", stroke="#CFCECE", sw=0.5)
S.text(SX + 110, BY + 176, "agree", size=9.4, fill=C["gtxt"])
S.coin(SX + 150, BY + 172, 4.6)
S.text(SX + 158, BY + 176, "label bought, budget r = %g" % R, size=9.4, fill=C["gtxt"])
S.text(SX + BW - 24, BY + 196, "100 events of one stream, harm active", size=9.2, fill=C["gtxt"], anchor="end", style="italic")

# ================================================================= c  real evidence curves
CX, CY = 322, 178
S.text(318, 166, "c", size=16, weight="bold")
S.text(336, 165, "Evidence against the null, same stream", size=11, weight="bold", fill=GT)
S.inline_svg(CX, CY + 6, 296, 158, curves_svg)
S.callout(CX + 4, CY + 170, 288, 34, C["green_l"])
S.text(CX + 148, CY + 185, "<b><c green>7.2×</c></b> evidence growth at equal spend (r = 0.20);", size=10, anchor="middle")
S.text(CX + 148, CY + 198, "100 wins, 0 losses at r = 0.05", size=10, anchor="middle")

S.save(HERE / "fig_overview1")
print("seed", seed, "window", start, "uniform labels", n_u, "on agreements", n_u - n_u_on, "gated labels", n_g,
      "alarms", alarms, "post-onset disagreement", round(DIS, 3))
