"""Figures 2-4 in the composed figures4papers style (toolchain shared with compose_fig1.py).

fig_growth_c : gated/uniform growth ratio, with the two reasons for its size drawn as objects
fig_pacing_c : fixed vs paced gating (horizon, detection, delay)
fig_map_c    : detection over budget x intervention strength, native SVG heatmaps
Data: outputs/r7_sweep/streams.parquet and the validated tables (values asserted below).
Run from the worktree root:  PYTHONPATH=. .venv/bin/python papers/paper1_decision_drift/manuscript/figures/compose_data_figs.py
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
from svgkit import C, Svg  # noqa: E402

SWEEP = HERE.parents[3] / "outputs/r7_sweep/streams.parquet"
GT = "#3F3F3F"
SERIF = "'Times New Roman', Times, serif"


def mpl_style(font=8.5):
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica", "Arial"], "svg.fonttype": "none",
                         "font.size": font, "axes.labelsize": font, "xtick.labelsize": font - 0.5,
                         "ytick.labelsize": font - 0.5, "legend.fontsize": font - 0.5, "axes.linewidth": 1.1,
                         "axes.spines.top": False, "axes.spines.right": False, "xtick.major.width": 1.1,
                         "ytick.major.width": 1.1, "lines.linewidth": 1.7})


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    t = buf.getvalue()
    return t[t.index("<svg"):]


def load():
    d = pd.read_parquet(SWEEP)
    return d[d.onset.notna()]


# =============================================================================== growth
def growth():
    budgets = [0.02, 0.05, 0.10, 0.20]
    kelly = [20.0, 19.7, 15.5, 7.6]      # scripts/g1_kelly_check.py (20 seeds per budget, registered grid)
    uncapped = [12.4, 12.5, 10.1, 5.1]   # same script, continuous stake
    pred = [18, 18, 15, 7.5]             # registered prediction
    meas = [17.5, 20.6, 14.7, 7.2]       # docs/gated_monitor_comparison_results.md
    assert max(abs(k / m - 1) for k, m in zip(kelly, meas)) < 0.16  # "within 15%" (r=0.02: 14.3%, r=0.05: 4.4%)
    mpl_style(8.5)
    fig, ax = plt.subplots(figsize=(3.9, 2.55))
    x = np.arange(4)
    w = 0.26
    ec = dict(edgecolor="#272727", linewidth=1.1)
    ax.bar(x - w, uncapped, w, color=C["blue"], label="Variance ratio", **ec)
    ax.bar(x, kelly, w, color=C["blue2"], label="Growth calculation", **ec)
    ax.bar(x + w, meas, w, color=C["blue_main"], label="Measured", **ec)
    ax.scatter(x, pred, marker="D", s=24, color=C["red"], zorder=5, label="Registered prediction", edgecolor="white", lw=0.6)
    for xi, v in zip(x + w, meas):
        ax.text(xi, v + 0.5, "%g" % v, ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, ["%.2f" % b for b in budgets])
    ax.set_xlabel("label budget $r$")
    ax.set_ylabel("gated / uniform evidence growth")
    ax.set_ylim(0, 26)
    ax.legend(loc="upper right", frameon=False, handlelength=1.2, borderaxespad=0.1)
    asset = to_svg(fig)

    W, H = 624, 262
    S = Svg(W, H)
    S.text(2, 15, "a", size=16, weight="bold")
    S.text(20, 14, "Evidence growth at matched label spend", size=11.5, weight="bold", fill=GT)
    S.inline_svg(8, 28, 360, 226, asset)
    S.text(386, 15, "b", size=16, weight="bold")
    S.text(404, 14, "Why the ratio is that large", size=11.5, weight="bold", fill=GT)
    S.group_box(384, 38, 232, 214, "two effects", C["dsage"], tx=398, tsize=10)
    # effect 1: variance
    S.text(396, 66, "Variance", size=10.5, weight="bold", fill=C["dblue"])
    S.text(396, 80, "gain ≈ min(1/<i>ρ</i>, 1/<i>r</i>)", size=10, family=SERIF, fill=GT)
    S.text(396, 92, "<i>ρ</i> = 0.084: events where policies disagree", size=9.4, fill=C["gtxt"])
    # effect 2: range penalty drawn as bound bars (r = 0.20: 45.9 vs 5.1)
    S.text(396, 120, "Range", size=10.5, weight="bold", fill=C["dred"])
    S.text(396, 133, "uniform’s support bound caps its stake", size=9.4, fill=C["gtxt"])
    bu, bg = 45.9, 5.1
    L = 150
    S.rect(396, 142, L, 13, fill=C["pink"], stroke=C["dred"], sw=0.9, shadow=True)
    S.rect(396, 160, L * bg / bu, 13, fill=C["blue"], stroke=C["dblue"], sw=0.9, shadow=True)
    S.text(396 + L + 6, 152, "uniform: 45.9", size=9.4, fill=C["dred"], weight="bold")
    S.text(396 + L * bg / bu + 6, 170, "gated: 5.1", size=9.4, fill=C["dblue"], weight="bold")
    S.text(396, 187, "bounds at <i>r</i> = 0.20; 9–24× across budgets", size=9.2, fill=C["gtxt"])
    S.callout(396, 200, 208, 40, C["green_l"])
    S.text(500, 216, "<b><c green>Within 15%</c></b> of measured", size=10, anchor="middle")
    S.text(500, 230, "at every budget", size=10, anchor="middle")
    S.save(HERE / "fig_growth_c")


# =============================================================================== pacing
def pacing():
    d = load()
    base = d[d.arm.isin(["gated_ht_fixed", "gated_ht_paced"])]
    col = {"gated_ht_fixed": C["blue_main"], "gated_ht_paced": C["red"]}
    nm = {"gated_ht_fixed": "Fixed rate", "gated_ht_paced": "Past-paced"}
    mpl_style(8.5)
    PW, PH = 2.45, 2.0

    fig, ax = plt.subplots(figsize=(PW, PH))
    h = base[base.budget_rate == 0.05].groupby(["adaptation_strength", "arm"]).processed.mean().unstack()
    for a in h.columns:
        ax.plot(h.index, h[a], marker="o", ms=4, color=col[a], label=nm[a])
    assert abs(h.loc[1.0, "gated_ht_paced"] / h.loc[1.0, "gated_ht_fixed"] - 1.86) < 0.02  # 2,111 / 1,136
    ax.set_xlabel("intervention strength $s$")
    ax.set_ylabel("events processed")
    ax.set_ylim(0, 2550)
    ax.legend(loc="lower left", frameon=False, handlelength=1.2, borderaxespad=0.1)
    pa = to_svg(fig)

    fig, ax = plt.subplots(figsize=(PW, PH))
    dd = base[base.budget_rate.isin([0.05, 0.10]) & (base.adaptation_strength >= 0.5)]
    pv = dd.pivot_table(index=["adaptation_strength", "budget_rate", "seed"], columns="arm", values="detected").astype(float)
    ss = sorted(dd.adaptation_strength.unique())
    rng = np.random.default_rng(0)
    for k, s in enumerate(ss):
        diff = (pv.xs(s, level=0).gated_ht_fixed - pv.xs(s, level=0).gated_ht_paced).values
        bs = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        ax.errorbar(k, diff.mean(), yerr=[[diff.mean() - lo], [hi - diff.mean()]], fmt="o", color=C["blue_main"], capsize=3, ms=4.5)
        assert lo < 0 < hi  # every interval contains zero
    ax.axhline(0, color=C["gtxt"], lw=1, ls="--")
    ax.set_xticks(range(len(ss)), ["%g" % s for s in ss])
    ax.set_xlabel("intervention strength $s$")
    ax.set_ylabel("detection, fixed − paced")
    ax.set_ylim(-0.15, 0.15)
    pb = to_svg(fig)

    fig, ax = plt.subplots(figsize=(PW, PH))
    cells = [(0.75, 0.10), (0.75, 0.20), (1.0, 0.10), (1.0, 0.20)]
    x = np.arange(4)
    for j, a in enumerate(["gated_ht_fixed", "gated_ht_paced"]):
        v = [base[(base.arm == a) & (base.adaptation_strength == s) & (base.budget_rate == r)].censored_delay.mean()
             for s, r in cells]
        ax.bar(x + (j - 0.5) * 0.4, v, 0.4, color=col[a], edgecolor="#272727", linewidth=1.1, label=nm[a])
        for xi, vi in zip(x + (j - 0.5) * 0.4, v):
            ax.text(xi, vi + 25, "%.0f" % vi, ha="center", fontsize=7.5)
        if j == 0:
            fixed = v
        else:
            assert all(1.3 < p / f < 2.1 for p, f in zip(v, fixed))  # "1.5-2x" (1.38 to 1.95 here)
    ax.set_xticks(x, ["%g\n%g" % c for c in cells])
    ax.set_xlabel("$s$ (top), $r$ (bottom)")
    ax.set_ylabel("censored delay (events)")
    ax.set_ylim(0, 1550)
    pc = to_svg(fig)

    W, H = 624, 296
    S = Svg(W, H)
    S.group_box(4, 24, 616, 266, "Pacing buys horizon, not detection", GT, tx=18, tsize=11, rx=10)
    xs = (14, 220, 424)
    sub = ("a", "b", "c")
    ttl = ("Reserve horizon", "Detection", "Detection delay")
    for x0, s_, t_, asset in zip(xs, sub, ttl, (pa, pb, pc)):
        S.text(x0, 50, s_, size=15, weight="bold")
        S.text(x0 + 16, 50, t_, size=10.5, weight="bold", fill=GT)
        S.inline_svg(x0, 58, 188, 156, asset)
    S.callout(14, 228, 188, 50, C["green_l"])
    S.text(108, 244, "<b><c green>1.9× longer</c></b>", size=10.5, anchor="middle")
    S.text(108, 258, "1,136 → 2,111 events", size=9.6, anchor="middle")
    S.text(108, 270, "(<i>s</i> = 1, <i>r</i> = 0.05)", size=9.4, anchor="middle", fill=C["gtxt"])
    S.callout(220, 228, 188, 50, C["green_l"])
    S.text(314, 244, "<b><c green>Equally often</c></b>", size=10.5, anchor="middle")
    S.text(314, 258, "every 95% interval", size=9.6, anchor="middle")
    S.text(314, 270, "contains 0", size=9.6, anchor="middle")
    S.callout(424, 228, 188, 50, C["pink"])
    S.text(518, 244, "<b><c dred>1.4–1.9× later</c></b>", size=10.5, anchor="middle")
    S.text(518, 258, "query rate 0.58 → 0.14", size=9.6, anchor="middle")
    S.text(518, 270, "bound 5/<i>q</i> grows ≈4×", size=9.6, anchor="middle")
    S.save(HERE / "fig_pacing_c")


# =============================================================================== map
def lerp(c0, c1, t):
    a = [int(c0[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02X%02X%02X" % tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def dmap():
    d = load()
    t = d[d.arm == "gated_ht_fixed"].groupby(["adaptation_strength", "budget_rate"]).detected.mean().unstack()
    u = d[d.arm == "uniform_ppi"].groupby(["adaptation_strength", "budget_rate"]).detected.mean().unstack()
    assert t.loc[:, [0.02, 0.05]].values.max() <= 0.29 and u.loc[:, [0.02, 0.05]].values.max() == 0.0
    assert abs(t.loc[0.5, 0.2] - 0.95) < 0.005 and abs(u.loc[0.5, 0.2] - 0.11) < 0.005
    W, H = 624, 308
    S = Svg(W, H)
    CW, CH = 36, 28
    rows = list(t.index)[::-1]  # strongest intervention at the top
    cols = list(t.columns)

    def heat(x0, y0, m, title, letter, tcol):
        S.text(x0 - 40, y0 - 24, letter, size=15, weight="bold")
        S.text(x0 - 24, y0 - 24, title, size=10.5, weight="bold", fill=tcol)
        for i, s in enumerate(rows):
            S.text(x0 - 6, y0 + i * CH + CH / 2 + 3.5, "%g" % s, size=9.6, anchor="end", fill=C["mid"])
            for j, r in enumerate(cols):
                v = float(m.loc[s, r])
                S.rect(x0 + j * CW, y0 + i * CH, CW, CH, fill=lerp("#F3F8FD", C["blue_main"], v ** 0.85), stroke="#FFFFFF", sw=1.2)
                S.text(x0 + j * CW + CW / 2, y0 + i * CH + CH / 2 + 3.5, "%.2f" % v, size=9.4, anchor="middle",
                       fill="#FFFFFF" if v > 0.5 else C["ink"])
        for j, r in enumerate(cols):
            S.text(x0 + j * CW + CW / 2, y0 + len(rows) * CH + 13, "%.2f" % r, size=9.6, anchor="middle", fill=C["mid"])
        S.text(x0 + len(cols) * CW / 2, y0 + len(rows) * CH + 27, "label budget <i>r</i>", size=9.8, anchor="middle", fill=GT)

    X1, X2, Y0 = 70, 350, 58
    heat(X1, Y0, t, "Gated, fixed rate", "a", C["dblue"])
    heat(X2, Y0, u, "Uniform labelling", "b", C["dred"])
    S.text(14, Y0 + len(rows) * CH / 2, "intervention strength <i>s</i>", size=9.8, fill=GT, anchor="middle",
           extra='transform="rotate(-90 14 %g)"' % (Y0 + len(rows) * CH / 2))
    # red frame on the failure region (r <= 0.05), both panels
    for X in (X1, X2):
        S.rect(X - 3, Y0 - 3, 2 * CW + 6, len(rows) * CH + 6, fill="none", stroke=C["red"], sw=1.6, rx=6, dash="5 3")
    S.text(X1 + CW, Y0 + len(rows) * CH + 44, "<b><c red>≤ 0.29 at every strength</c></b>", size=10, anchor="middle")
    S.text(X2 + CW, Y0 + len(rows) * CH + 44, "<b><c red>0.00 at every strength</c></b>", size=10, anchor="middle")
    # colour key
    kx, ky = 540, Y0 + 6
    for k in range(10):
        S.rect(kx, ky + k * 11, 12, 11, fill=lerp("#F3F8FD", C["blue_main"], (9 - k) / 9 ** 1.0 ** 1 if False else (9 - k) / 9), stroke=None)
    S.text(kx + 18, ky + 9, "1.0", size=9.4, fill=C["mid"])
    S.text(kx + 18, ky + 108, "0.0", size=9.4, fill=C["mid"])
    S.text(kx, ky - 8, "detection", size=9.4, fill=GT)
    S.callout(200, 258, 224, 40, C["green_l"])
    S.text(312, 274, "<b><c green>r = 0.20, s = 0.50:</c></b> gated 0.95, uniform 0.11", size=10, anchor="middle")
    S.text(312, 288, "100 streams per cell", size=9.2, anchor="middle", fill=C["gtxt"])
    S.save(HERE / "fig_map_c")


if __name__ == "__main__":
    growth()
    pacing()
    dmap()
    print("ok")
