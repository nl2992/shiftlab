"""Figure 1 teaser, rebuilt after the figures4papers "Miscellaneous" examples (VIGIL teaser: same scene twice, banners,
robots + scales, check/cross marks; Dispersion: on-plot bold annotation and block-arrow takeaway).
Strips and curves are one registered boundary_local_harm stream at r = 0.05 (make_overview.run). Run from the worktree root:
  PYTHONPATH=. .venv/bin/python papers/paper1_decision_drift/manuscript/figures/compose_teaser.py
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
from glyphs import SEM, brace_down, check, cross, doc, pill_banner, purse, robot, scales, banner_arrow  # noqa: E402
from make_overview import ALPHA, R, alarm, pick_seed  # noqa: E402
from svgkit import C, MONO, Svg  # noqa: E402

seed, act, out = pick_seed()
N, ONSET, WIN = 2400, 800, 100
q_g = np.zeros(N, bool)
q_g[: len(out["gated_ht_fixed"][1])] = out["gated_ht_fixed"][1]
q_u = out["uniform"][1]
assert not (q_g & ~act).any()
start = next(s for s in range(ONSET + 100, N - WIN) if q_g[s:s + WIN].sum() >= 4 and q_u[s:s + WIN].sum() >= 4 and act[s:s + WIN].sum() >= 8)
sl = slice(start, start + WIN)
a_w, g_w, u_w = act[sl], q_g[sl], q_u[sl]
n_g, n_u, n_u_on = int(g_w.sum()), int(u_w.sum()), int((u_w & a_w).sum())
alarms = {k: alarm(out[k][0]) for k in out}
assert alarms["uniform"] is None and alarms["gated_ht_fixed"] and alarms["full"]
GT = "#3F3F3F"


def curve_asset(key, col, name, note, note_col):
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica", "Arial"], "svg.fonttype": "none",
                         "font.size": 9, "axes.linewidth": 1.0, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(3.85, 1.3))
    f = np.asarray(out["full"][0])
    ax.plot(np.arange(len(f)), f, color="#9A9A9A", lw=1.3, ls="--", label="full feedback")
    le = np.asarray(out[key][0])
    ax.plot(np.arange(len(le)), le, color=col, lw=2.0, label=name)
    a = alarm(le)
    if a is not None:
        ax.plot(a, le[a], "o", color=col, ms=5, zorder=6)
        ax.annotate(note, (a, le[a]), xytext=(40, 6.5), fontsize=9.5, fontweight="bold", color=note_col,
                    arrowprops=dict(arrowstyle="-", color=note_col, lw=1))
    else:
        ax.text(1450, 1.4, note, fontsize=9.5, fontweight="bold", color=note_col)
    ax.axhline(-np.log(ALPHA), color="#767676", lw=0.8, ls=":")
    ax.axvline(ONSET, color="#272727", lw=0.8, ls="--")
    ax.set_xlim(0, N)
    ax.set_ylim(-1, 12)
    ax.set_yticks([0, 6, 12])
    ax.set_xticks([0, 1000, 2000])
    ax.set_xlabel("monitored events", labelpad=1, fontsize=9)
    ax.set_ylabel("log-evidence", labelpad=1, fontsize=9)
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    t = buf.getvalue()
    return t[t.index("<svg"):]


W, H = 624, 372
S = Svg(W, H)
S.text(2, 24, "a", size=16, weight="bold")
pill_banner(S, 20, 8, 286, 28, "Uniform labelling pays for <b>events that cannot teach</b>.", "grey", size=10.2)
pill_banner(S, 318, 8, 300, 28, "Gating pays <b>only where the two policies disagree</b>.", "blue", size=10.2)


def scene(ox, tag, tcol):
    """Identical scene in both halves: events -> two policies -> paired cost, plus the label budget."""
    doc(S, ox + 4, 50, 26, 32, nlines=3)
    doc(S, ox + 8, 54, 26, 32, nlines=3)
    S.text(ox + 22, 102, "events", size=9.4, family=MONO, weight="bold", anchor="middle")
    S.arrow([(ox + 38, 62), (ox + 58, 56)], sw=1.1)
    S.arrow([(ox + 38, 91), (ox + 98, 91)], sw=1.1)
    robot(S, ox + 62, 44, 30, SEM["deployed"], "deployed", SEM["deployed"], size=9.2)
    robot(S, ox + 100, 64, 30, SEM["reference"], "reference", SEM["reference"], size=9.2)
    S.arrow([(ox + 134, 80), (ox + 156, 76)], sw=1.1)
    scales(S, ox + 158, 48, 34, SEM["cost"], "paired cost", size=9.2)
    S.block_arrow(ox + 200, 74, ox + 222, 14, "#E0A92B")
    purse(S, ox + 232, 56, 24)
    S.text(ox + 244, 98, "budget", size=9.2, family=MONO, weight="bold", fill="#8A6A12", anchor="middle")
    S.text(ox + 244, 109, "<i>r</i> = %g" % R, size=9.4, fill="#8A6A12", anchor="middle")


def strip(ox, y, queried, good):
    sx, sw = ox + 8, 286 / WIN
    for i in range(WIN):
        S.rect(sx + i * sw, y, sw + 0.15, 18, fill=C["pink"] if a_w[i] else "#EDECEC", stroke=None)
    for i in np.flatnonzero(queried):
        cx = sx + (i + .5) * sw
        S.path("M%g,%g L%g,%g" % (cx, y - 3, cx, y), stroke="#8A6A12", sw=0.7)
        S.coin(cx, y - 9, 5)
        (check if a_w[i] else cross)(S, cx, y + 31, 9)


scene(6, "std", SEM["uniform"])
scene(318, "ours", SEM["ours"])
S.text(2, 138, "b", size=16, weight="bold") if False else None
S.path("M312,44 L312,330", stroke="#CFCECE", sw=1, dash="2 3")
strip(6, 152, u_w, good=False)
strip(318, 152, g_w, good=True)
S.text(12, 196, "<b><c red>%d of %d labels land on agreements: wasted</c></b>" % (n_u - n_u_on, n_u), size=10)
S.text(324, 196, "<b><c #0F4D92>all %d labels land on disagreements</c></b>" % n_g, size=10)
S.rect(12, 205, 8, 8, fill=C["pink"])
S.text(24, 213, "policies disagree", size=9.2, fill=C["gtxt"])
S.rect(104, 205, 8, 8, fill="#EDECEC", stroke="#CFCECE", sw=0.5)
S.text(116, 213, "agree: cost is exactly 0", size=9.2, fill=C["gtxt"])
S.text(330, 213, "100 events of one stream, harm active", size=9.2, fill=C["gtxt"], style="italic")

S.text(2, 238, "b", size=16, weight="bold")
S.inline_svg(10, 238, 288, 96, curve_asset("uniform", SEM["uniform"], "uniform", "never alarms", SEM["uniform"]))
S.inline_svg(322, 238, 288, 96, curve_asset("gated_ht_fixed", SEM["ours"], "gated", "alarm at event %d" % alarms["gated_ht_fixed"], SEM["ours"]))
banner_arrow(S, 6, 340, 612, 28, "<b>7.2×</b> the evidence at equal spend (<i>r</i> = 0.20); 100 wins, 0 losses at <i>r</i> = 0.05", size=11)
S.save(HERE / "fig_teaser")
print("seed", seed, "window", start, "uniform", n_u, n_u_on, "gated", n_g, alarms)
