"""Figure (main text): where the budget is exceeded. (a) one dot per registered regime: exceedance rate of R=20, by arm;
(b) real streams: share of runs above R=24. The full heatmap and all-arm counts are in fig_violations_full.py (appendix)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from style import PALETTE as P, WIDTH, apply_style, panel_label, save
from viol_data import M, cols, order, stress, cnt, tot, rarms

NAMES = {"wald_cut": "Wald cutoff", "cusum": "CUSUM", "gate_wald": "e-process gate", "cusum_rb_h8": "CUSUM rollback",
         "stoploss_R20": "stop-loss", "f3_pi1_R20": "shield (full)", "f3v2d_R20": "shield (paced)"}
COLOR = {"wald_cut": P["red_strong"], "cusum": "#D98880", "gate_wald": "#C97B76", "cusum_rb_h8": "#D98880",
         "stoploss_R20": "#E08E45", "f3_pi1_R20": P["blue_main"], "f3v2d_R20": P["teal"]}
keys = [c[0] for c in cols]
is_stress = np.array([g in stress for g in order])
rng = np.random.default_rng(3)

apply_style(8.5)
fig = plt.figure(figsize=(WIDTH, 2.9))
gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1], wspace=0.42, left=0.2, right=0.99, top=0.9, bottom=0.17)
ax, bx = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

# (a) strip plot
ny = len(keys)
ax.axhspan(-0.5, 1.5, color=P["green_1"], alpha=0.6, lw=0)
for r, k in enumerate(keys):
    y = ny - 1 - r
    v = M[:, r]
    jit = rng.uniform(-0.2, 0.2, len(v))
    ax.scatter(v[~is_stress], y + jit[~is_stress], s=11, color=COLOR[k], alpha=0.45, linewidths=0, zorder=3)
    ax.scatter(v[is_stress], y + jit[is_stress], s=22, color=COLOR[k], edgecolor="white", linewidths=0.4, zorder=4)
    ax.plot([v.mean()] * 2, [y - 0.32, y + 0.32], color=P["dark"], lw=1.6, zorder=5)
    j = int(np.argmax(v))
    if v[j] >= 0.1 or k.startswith("f3"):
        ax.text(v[j] + 0.03, y, f"{v[j]:.2f}".lstrip("0") if v[j] > 0.0095 else ("max .001" if v[j] > 0 else "none"), va="center", fontsize=7, color=COLOR[k])
ax.set_yticks(range(ny)); ax.set_yticklabels([NAMES[k] for k in keys][::-1])
for t, k in zip(ax.get_yticklabels(), keys[::-1]):
    t.set_color(COLOR[k] if not k.startswith("f3") else P["blue_main"])
ax.set_ylim(-0.6, ny - 0.4); ax.set_xlim(-0.03, 1.12)
ax.set_xlabel("exceedance rate of $R$=20 (one dot per regime)")
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
ax.plot([], [], color=P["dark"], lw=1.6, label="mean over regimes")
ax.legend(loc="lower right", fontsize=7, bbox_to_anchor=(1.0, 0.0), handlelength=1.0, borderaxespad=0)
panel_label(ax, "a", -0.52, 1.1)
ax.set_title("registered simulation", loc="left", fontsize=8, pad=6, family=["Courier New","Menlo","DejaVu Sans Mono"], fontweight="bold")

# (b) real streams, share of runs
conds = ["clean", "adverse\ndropout", "adverse\ndelay"]
show = ["wald_cut", "cusum_rb_h8", "stoploss_h14", "f3_pi1_h14"]
lab = {a: (l, c, m) for a, l, c, m in rarms}
x = np.arange(3); w = 0.19
for i, a in enumerate(show):
    pct = 100 * np.array(cnt[a]) / np.array(tot)
    xs = x + (i - 1.5) * w
    bx.bar(xs, pct, width=w * 0.92, color=lab[a][1], label=lab[a][0].replace("shield (full)", "shield"))
    if a.startswith("f3"):
        for xi, v in zip(xs, pct):
            bx.text(xi, v + 0.8, "0", ha="center", va="bottom", fontsize=7.5, color=lab[a][1])
bx.set_xticks(x); bx.set_xticklabels(conds)
bx.set_ylabel("runs above $R$=24 (%)"); bx.set_ylim(0, 34)
bx.legend(loc="upper left", ncol=2, fontsize=7, columnspacing=0.8, handlelength=0.9, handletextpad=0.4, borderaxespad=0, bbox_to_anchor=(0.0, 1.02))
panel_label(bx, "b", -0.3, 1.1)
bx.set_title("real streams", loc="left", fontsize=8, pad=6, family=["Courier New","Menlo","DejaVu Sans Mono"], fontweight="bold")
save(fig, "violations")
print({a: [round(100 * c / n, 1) for c, n in zip(cnt[a], tot)] for a in show}, tot)
