"""Figure 3: budget violations. (a) registered simulation, per-regime exceedance of R=20; (b) real streams, runs above R=24."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from style import CONFIGS, OUT, PALETTE as P, RES, WIDTH, apply_style, load_json, panel_label, save

conf = load_json(RES / "confirm_summary.json")
c3, c1, c2 = conf["C3"]["arms"], conf["C1"]["arms"], conf["C2"]["arms"]
cols = [("wald_cut", c3, "Wald\ncutoff"), ("cusum", c3, "CUSUM"), ("gate_wald", c3, "e-proc.\ngate"),
        ("cusum_rb_h8", c3, "CUSUM\nrb"), ("stoploss_R20", c3, "stop-\nloss"),
        ("f3f_pi1_R20", None, None), ("f3_pi1_R20", c1, "shield\nfull"), ("f3v2d_R20", c2, "shield\npaced")]
cols = [c for c in cols if c[1] is not None]
stress = [r["id"] for r in load_json(CONFIGS / "regimes_f3_v1.json")["regimes"]]
regs = list(c3["wald_cut"]["per_regime"])
orig = [r for r in regs if r not in stress]
order = orig + stress
M = np.array([[src[a]["per_regime"][g]["rate"] for a, src, _ in cols] for g in order])

# real streams: runs with sup_harm above R=24 (budget arms: above own R = 24 at h=14)
conds = ["clean", "delay_adverse", "dropout_adverse"]
rarms = [("wald_cut", "Wald cutoff", P["red_strong"], "o"), ("cusum_rb_h8", "CUSUM rollback", "#D98880", "D"),
         ("stoploss_h14", "stop-loss", "#E08E45", "v"), ("f3_pi1_h14", "shield (full)", P["blue_main"], "s"),
         ("f3v2d_h14", "shield (paced)", P["teal"], "^")]
cnt = {a: [] for a, *_ in rarms}; tot = []
for c in conds:
    n = {a: 0 for a in cnt}; N = 0
    for f in sorted((OUT / "real" / c).glob("*.json")):
        d = load_json(f); sh = np.array(d["fields"]["sup_harm"], float)
        N += sh[0].size
        for a in cnt:
            n[a] += int((sh[d["arms"].index(a)] > 24).sum())
    for a in cnt: cnt[a].append(n[a])
    tot.append(N)

apply_style(8)
fig = plt.figure(figsize=(WIDTH, 5.2))
gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], wspace=0.42, left=0.14, right=0.985, top=0.93, bottom=0.2)
ax = fig.add_subplot(gs[0]); bx = fig.add_subplot(gs[1])
cmap = LinearSegmentedColormap.from_list("w2r", ["#FFFFFF", P["red_1"], P["red_strong"], "#5E1B1A"])
im = ax.imshow(M, aspect="auto", cmap=cmap, vmin=0, vmax=1, interpolation="nearest")
ax.set_xticks(range(len(cols))); ax.set_xticklabels([c[2] for c in cols], fontsize=7)
ax.xaxis.tick_top(); ax.tick_params(axis="x", length=0)
lab = lambda g: g.replace("_", " ")
ax.set_yticks(range(len(order))); ax.set_yticklabels([("* " if g in stress else "") + lab(g) for g in order], fontsize=5.8)
for t, g in zip(ax.get_yticklabels(), order):
    if g in stress: t.set_color(P["red_strong"]); t.set_fontweight("bold")
ax.tick_params(axis="y", length=0, pad=2)
for s in ax.spines.values(): s.set_visible(False)
ax.axhline(len(orig) - 0.5, color=P["dark"], lw=0.8)
ax.axvline(4.5, color=P["dark"], lw=0.8)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        v = M[i, j]
        if v >= 0.2: ax.text(j, i, f"{v:.2f}".lstrip("0"), ha="center", va="center", fontsize=5, color="white" if v > 0.45 else P["dark"])
        elif j >= 5: ax.text(j, i, f"{v:.3f}".lstrip("0") if v > 0 else "0", ha="center", va="center", fontsize=5, color=P["dark"])
cax = fig.add_axes([0.14, 0.09, 0.3, 0.012])
cb = fig.colorbar(im, cax=cax, orientation="horizontal"); cb.set_label("exceedance rate of $R$=20 (runs above $R$ / 1000)", fontsize=7)
cb.outline.set_visible(False); cb.ax.tick_params(labelsize=6.5, length=2)
panel_label(ax, "(a)", -0.55, 1.08)
ax.text(0.5, -0.045, "", transform=ax.transAxes)

# (b)
x = np.arange(len(conds)); w = 0.16
for i, (a, lbl, col, mk) in enumerate(rarms):
    xs = x + (i - 2) * w
    bx.vlines(xs, 0, cnt[a], color=col, lw=1.2)
    bx.scatter(xs, cnt[a], color=col, marker=mk, s=26, zorder=3, label=lbl)
    for xi, v in zip(xs, cnt[a]):
        bx.text(xi, v + 15 if v else 55, f"{v}", ha="center", va="bottom", fontsize=6, color=col, rotation=90 if v else 0)
bx.set_xticks(x); bx.set_xticklabels(["clean", "adverse\ndelay", "adverse\ndropout"])
bx.set_ylabel(f"runs with harm above $R$=24 (of {tot[0]:,})")
bx.set_ylim(0, 1400); bx.set_yticks(range(0, 1201, 200)); bx.set_xlim(-0.55, 2.55)
bx.legend(loc="upper left", ncol=2, fontsize=7, bbox_to_anchor=(-0.02, 1.0), columnspacing=0.8, handletextpad=0.2, borderaxespad=0)
panel_label(bx, "(b)", -0.28, 1.06)
bx.set_title("Real streams ($R$=24)", loc="center", fontsize=8, y=1.0, pad=6)
ax.text(0.5, 1.07, "Simulation, registered run ($R$=20)", transform=ax.transAxes, ha="center", fontsize=8)
save(fig, "violations")
print("tot runs", tot); print({a: v for a, v in cnt.items()})
print("worst per col", dict(zip([c[0] for c in cols], M.max(0).round(3))), "pooled", dict(zip([c[0] for c in cols], M.mean(0).round(4))))
