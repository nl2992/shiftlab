"""Paper 1 figures. Data: outputs/r7_sweep/streams.parquet and the validated tables in
docs/gated_monitor_comparison_results.md and scripts/g1_kelly_check.py output.
Palette and conventions follow figures4papers (blue = gated, red = uniform/ungated, neutral = reference).
Re-implemented; no code copied. PaperBanana was unavailable, so these are matplotlib figures.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SWEEP = ROOT / "outputs/r7_sweep/streams.parquet"
P = {"blue": "#0F4D92", "blue2": "#3775BA", "blue_l": "#CFE3F6", "red": "#B64342", "red_l": "#F6CFCB",
     "grey": "#767676", "neutral": "#CFCECE", "dark": "#272727", "green": "#8BCF8B"}
W = 6.5


def style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 8.5, "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "axes.linewidth": 1.25, "axes.spines.top": False, "axes.spines.right": False,
        "legend.frameon": False, "xtick.major.width": 1.25, "ytick.major.width": 1.25,
        "lines.linewidth": 1.8, "pdf.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 300,
    })


def label(ax, s):
    ax.text(-0.14, 1.05, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(HERE / f"fig_{name}.{ext}", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)


def fig_growth():
    budgets = [0.02, 0.05, 0.10, 0.20]
    kelly = [20.0, 19.7, 15.5, 7.6]       # scripts/g1_kelly_check.py, 20 seeds per budget
    uncapped = [12.4, 12.5, 10.1, 5.1]    # same script, continuous stake
    pred = [18, 18, 15, 7.5]              # registered G1 prediction
    meas = [17.5, 20.6, 14.7, 7.2]        # docs/gated_monitor_comparison_results.md
    x = np.arange(4)
    fig, ax = plt.subplots(figsize=(W * 0.62, 2.7))
    w = 0.26
    ax.bar(x - w, uncapped, w, color=P["blue_l"], edgecolor=P["dark"], linewidth=1, label="Variance ratio (uncapped stake)")
    ax.bar(x, kelly, w, color=P["blue2"], edgecolor=P["dark"], linewidth=1, label="Growth calculation, registered grid")
    ax.bar(x + w, meas, w, color=P["blue"], edgecolor=P["dark"], linewidth=1, label="Measured (100 streams)")
    ax.scatter(x, pred, marker="D", s=22, color=P["red"], zorder=5, label="Registered prediction")
    for xi, v in zip(x + w, meas):
        ax.text(xi, v + 0.5, f"{v:g}", ha="center", va="bottom", fontsize=7.5)
    ax.set_xticks(x, [f"{b:.2f}" for b in budgets])
    ax.set_xlabel("Label budget $r$ (fraction of full labelling cost)")
    ax.set_ylabel("Gated / uniform evidence growth")
    ax.set_ylim(0, 24)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, handlelength=1.2, columnspacing=1.2)
    save(fig, "growth")


def load():
    d = pd.read_parquet(SWEEP)
    return d[d.onset.notna()]


def fig_pacing():
    d = load()
    base = d[d.arm.isin(["gated_ht_fixed", "gated_ht_paced"])]
    fig, axs = plt.subplots(1, 3, figsize=(W, 2.35))
    col = {"gated_ht_fixed": P["blue"], "gated_ht_paced": P["red"]}
    nm = {"gated_ht_fixed": "Fixed rate", "gated_ht_paced": "Past-paced"}

    ax = axs[0]
    h = base[base.budget_rate == 0.05].groupby(["adaptation_strength", "arm"]).processed.mean().unstack()
    for a in h.columns:
        ax.plot(h.index, h[a], marker="o", ms=4, color=col[a], label=nm[a])
    ax.set_xlabel("Intervention strength $s$")
    ax.set_ylabel("Events processed before reserve stops")
    ax.set_ylim(0, 2500)
    ax.legend(loc="lower left")
    label(ax, "a")

    ax = axs[1]
    dd = base[base.budget_rate.isin([0.05, 0.10]) & (base.adaptation_strength >= 0.5)]
    pv = dd.pivot_table(index=["adaptation_strength", "budget_rate", "seed"], columns="arm", values="detected").astype(float)
    ss = sorted(dd.adaptation_strength.unique())
    rng = np.random.default_rng(0)
    for k, s in enumerate(ss):
        diff = (pv.xs(s, level=0).gated_ht_fixed - pv.xs(s, level=0).gated_ht_paced).values
        bs = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        ax.errorbar(k, diff.mean(), yerr=[[diff.mean() - lo], [hi - diff.mean()]], fmt="o", color=P["blue"], capsize=3, ms=4)
    ax.axhline(0, color=P["grey"], lw=1, ls="--")
    ax.set_xticks(range(len(ss)), [f"{s:g}" for s in ss])
    ax.set_xlabel("Intervention strength $s$")
    ax.set_ylabel("Detection, fixed $-$ paced")
    ax.set_ylim(-0.15, 0.15)
    ax.text(0.5, 0.93, "$r\\in\\{0.05,0.10\\}$", transform=ax.transAxes, ha="center", fontsize=7.5, color=P["grey"])
    label(ax, "b")

    ax = axs[2]
    cells = [(0.75, 0.10), (0.75, 0.20), (1.0, 0.10), (1.0, 0.20)]
    x = np.arange(len(cells))
    for j, a in enumerate(["gated_ht_fixed", "gated_ht_paced"]):
        v = [base[(base.arm == a) & (base.adaptation_strength == s) & (base.budget_rate == r)].censored_delay.mean()
             for s, r in cells]
        ax.bar(x + (j - 0.5) * 0.38, v, 0.38, color=col[a], edgecolor=P["dark"], linewidth=1, label=nm[a])
        for xi, vi in zip(x + (j - 0.5) * 0.38, v):
            ax.text(xi, vi + 20, f"{vi:.0f}", ha="center", fontsize=7)
    ax.set_xticks(x, [f"{s:g}\n{r:g}" for s, r in cells])
    ax.set_xlabel("$s$ (top), $r$ (bottom)")
    ax.set_ylabel("Censored detection delay (events)")
    ax.set_ylim(0, 1800)
    ax.legend(loc="upper right", handlelength=1.0, fontsize=7.5)
    label(ax, "c")
    fig.tight_layout(w_pad=1.6)
    save(fig, "pacing")


def fig_map():
    d = load()
    t = d[d.arm == "gated_ht_fixed"].groupby(["adaptation_strength", "budget_rate"]).detected.mean().unstack()
    u = d[d.arm == "uniform_ppi"].groupby(["adaptation_strength", "budget_rate"]).detected.mean().unstack()
    f = d[d.arm == "full_feedback"].groupby("adaptation_strength").detected.mean()
    fig, axs = plt.subplots(1, 2, figsize=(W, 2.5), gridspec_kw={"width_ratios": [1, 1], "wspace": 0.35})
    for ax, m, title, tag in ((axs[0], t, "Gated HT, fixed rate", "a"), (axs[1], u, "Uniform labelling (PPI)", "b")):
        im = ax.imshow(m.values, origin="lower", cmap="Blues", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(m.shape[1]), [f"{c:.2f}" for c in m.columns])
        ax.set_yticks(range(m.shape[0]), [f"{s:g}" for s in m.index])
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                v = m.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5, color="white" if v > 0.55 else P["dark"])
        ax.set_xlabel("Label budget $r$")
        ax.set_title(title, fontsize=8.5, pad=4)
        ax.spines[:].set_visible(False)
        label(ax, tag)
    axs[0].set_ylabel("Intervention strength $s$")
    cb = fig.colorbar(im, ax=axs, fraction=0.025, pad=0.02)
    cb.set_label("Detection probability")
    cb.outline.set_visible(False)
    save(fig, "map")
    print("full feedback detection by strength:", f.round(2).to_dict())


if __name__ == "__main__":
    style()
    fig_growth()
    fig_pacing()
    fig_map()
