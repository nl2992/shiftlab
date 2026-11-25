"""Pacing figure after RNAGenScape teaser (same scene twice, monospace titles, pale green notes, bold on-plot phrases) and the
ImmunoStruct mosaic (uneven panel sizes). Top: one registered harmful_adaptation stream (s = 1, r = 0.10): label reserve and
log-evidence for fixed-rate vs past-paced gating. Bottom: pooled sweep (outputs/r7_sweep) detection difference and delay.
Run from the worktree root: PYTHONPATH=. .venv/bin/python papers/paper1_decision_drift/manuscript/figures/compose_pacing2.py
"""
import io
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import ndtr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3] / "src"))
from glyphs import SEM  # noqa: E402
from svgkit import C, MONO, Svg  # noqa: E402

from shiftlab.decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action  # noqa: E402
from shiftlab.dive.experiment import _binary_cost, _synthetic_label_costs  # noqa: E402
from shiftlab.dive.gated_monitor_comparison import replay_gated  # noqa: E402

R, S_STR, ALPHA = 0.10, 1.0, 0.05
SWEEP = HERE.parents[3] / "outputs/r7_sweep/streams.parquet"


def hstream(seed):
    scen = next(s for s in SCENARIOS if s.name == "harmful_adaptation")
    cfg = ExperimentConfig(n=3200, d=16, evaluation_seeds=1, calibration_seeds=2, calibration_start=800, window=64, stride=32,
                           alpha=ALPHA, eprocess_epsilon=0.1, seed_offset=seed, change_fraction=0.5, device="cpu")
    _, frame, _, _ = _generate(scen, seed, cfg)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    dep = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    dep[1600:] = 1
    ref = _source_action(x, scen)
    act = dep != ref
    c = _binary_cost(dep, y, scen.fn_cost, scen.fp_cost) - _binary_cost(ref, y, scen.fn_cost, scen.fp_cost)
    return x, act, c, _synthetic_label_costs(x)


def run(seed):
    x, act, c, tar = hstream(seed)
    coins = np.random.default_rng(seed + 9_173).random(3200)
    kw = dict(x=x[800:], paired_cost=c[800:], disagreement=act[800:], tariffs=tar[800:], uniforms=coins[:2400],
              validation_disagreement=act[400:800], validation_tariffs=tar[400:800], budget_rate=R)
    out = {}
    for arm in ("gated_ht_fixed", "gated_ht_paced"):
        res = replay_gated(arm=arm, **kw)
        n = len(res.increments)
        reserve = 1 - np.cumsum(res.queried * tar[800:800 + n]) / res.budget
        out[arm] = dict(log_e=np.asarray(res.log_e), reserve=reserve, alarm=res.first_alarm, n=n, labels=int(res.queried.sum()))
    return out


for seed in range(61000000, 61000100):
    out = run(seed)
    f, p = out["gated_ht_fixed"], out["gated_ht_paced"]
    if f["alarm"] is not None and p["alarm"] is not None and f["n"] < 2400 and f["alarm"] < f["n"]:
        break
else:
    raise RuntimeError("no seed")
assert f["n"] < p["n"]

plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Helvetica", "Arial"], "svg.fonttype": "none",
                     "font.size": 8.5, "axes.linewidth": 1.0, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8})


def to_svg(fig):
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    t = buf.getvalue()
    return t[t.index("<svg"):]


def side(d, col, note_alarm, note_stop):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(3.9, 1.95), sharex=True, gridspec_kw=dict(height_ratios=[1, 2.3], hspace=0.12))
    n = d["n"]
    t = np.arange(n)
    a1.fill_between(t, d["reserve"], color="#F3D88A", alpha=0.9)
    a1.plot(t, d["reserve"], color="#B58A1B", lw=1.3)
    a1.set_ylim(0, 1.05)
    a1.set_yticks([0, 1])
    a1.set_yticklabels(["0", "full"])
    a1.set_ylabel("reserve", labelpad=0)
    a1.axvline(800, color="#272727", lw=0.8, ls="--")
    if n < 2400:
        a1.plot(n - 1, 0, "X", color=SEM["alarm"], ms=7, zorder=6)
        a1.text(n + 40, 0.38, note_stop, color=SEM["alarm"], fontsize=9, fontweight="bold")
    a2.plot(t, d["log_e"], color=col, lw=2.0)
    a2.axhline(-np.log(ALPHA), color="#767676", lw=0.8, ls=":")
    a2.axvline(800, color="#272727", lw=0.8, ls="--")
    al = d["alarm"]
    a2.plot(al, d["log_e"][al], "o", color=col, ms=5, zorder=6)
    a2.annotate(note_alarm, (al, d["log_e"][al]), xytext=(al - 760 if al > 1000 else al + 60, d["log_e"][al] + 4.8), fontsize=9,
                fontweight="bold", color=col, arrowprops=dict(arrowstyle="-", color=col, lw=0.9))
    a2.set_xlim(0, 2400)
    a2.set_ylim(-1, 12)
    a2.set_yticks([0, 6, 12])
    a2.set_xticks([0, 1000, 2000])
    a2.set_xlabel("monitored events", labelpad=1)
    a2.set_ylabel("log-evidence", labelpad=1)
    return to_svg(fig)


svg_f = side(f, SEM["ours"], "alarm at event %d" % f["alarm"], "reserve empty: monitor stops")
svg_p = side(p, SEM["uniform"], "alarm at event %d" % p["alarm"], "")

# ---- bottom: pooled sweep
d = pd.read_parquet(SWEEP)
d = d[d.onset.notna()]
base = d[d.arm.isin(["gated_ht_fixed", "gated_ht_paced"])]
fig, ax = plt.subplots(figsize=(2.5, 1.75))
dd = base[base.budget_rate.isin([0.05, 0.10]) & (base.adaptation_strength >= 0.5)]
pv = dd.pivot_table(index=["adaptation_strength", "budget_rate", "seed"], columns="arm", values="detected").astype(float)
ss = sorted(dd.adaptation_strength.unique())
rng = np.random.default_rng(0)
for k, s in enumerate(ss):
    diff = (pv.xs(s, level=0).gated_ht_fixed - pv.xs(s, level=0).gated_ht_paced).values
    bs = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    assert lo < 0 < hi
    ax.errorbar(k, diff.mean(), yerr=[[diff.mean() - lo], [hi - diff.mean()]], fmt="o", color=SEM["ours"], capsize=3, ms=4.5)
ax.axhline(0, color="#767676", lw=1, ls="--")
ax.set_xticks(range(len(ss)), ["%g" % s for s in ss])
ax.set_xlabel("intervention strength $s$")
ax.set_ylabel("detection, fixed − paced")
ax.set_ylim(-0.16, 0.2)
ax.text(1, 0.15, "equal detection", ha="center", fontsize=9.5, fontweight="bold", fontstyle="italic", color=SEM["ours"])
svg_b = to_svg(fig)

fig, ax = plt.subplots(figsize=(4.4, 1.75))
cells = [(0.75, 0.10), (0.75, 0.20), (1.0, 0.10), (1.0, 0.20)]
x = np.arange(4)
vals = {}
for j, a in enumerate(["gated_ht_fixed", "gated_ht_paced"]):
    v = [base[(base.arm == a) & (base.adaptation_strength == s) & (base.budget_rate == r)].censored_delay.mean() for s, r in cells]
    vals[a] = v
    ax.bar(x + (j - 0.5) * 0.4, v, 0.4, color=SEM["ours"] if j == 0 else SEM["uniform"], edgecolor="#272727", linewidth=1.0,
           label=["Fixed rate", "Past-paced"][j])
    for xi, vi in zip(x + (j - 0.5) * 0.4, v):
        ax.text(xi, vi + 25, "%.0f" % vi, ha="center", fontsize=8)
assert all(1.3 < p / f_ < 2.1 for p, f_ in zip(vals["gated_ht_paced"], vals["gated_ht_fixed"]))
ax.set_xticks(x, ["$s$=%g\n$r$=%g" % c for c in cells])
ax.set_ylabel("censored delay (events)")
ax.set_ylim(0, 1800)
ax.text(1.5, 1620, "paced alarms 1.4–2× later", ha="center", fontsize=10, fontweight="bold", fontstyle="italic", color=SEM["uniform"])
svg_c = to_svg(fig)

W, H = 624, 392
S = Svg(W, H)
S.text(2, 20, "a", size=16, weight="bold")
S.text(22, 20, "fixed-rate gating", size=12, family=MONO, weight="bold", fill=SEM["ours"])
S.text(332, 20, "past-paced gating", size=12, family=MONO, weight="bold", fill=SEM["uniform"])
S.inline_svg(8, 28, 296, 150, svg_f)
S.inline_svg(318, 28, 296, 150, svg_p)
S.rect(8, 184, 296, 34, fill=C["green_l"], rx=9)
S.text(18, 198, "Spends labels as disagreements arrive: the", size=9.8, fill="#4E6B3E")
S.text(18, 211, "<b>reserve runs dry at event %d</b>, then the monitor stops." % f["n"], size=9.8, fill="#4E6B3E")
S.rect(318, 184, 296, 34, fill=C["green_l"], rx=9)
S.text(328, 198, "Slows its query rate: <b>still watching at event %d</b>," % p["n"], size=9.8, fill="#4E6B3E")
S.text(328, 211, "but each label carries less evidence (bound 5/<i>q</i>).", size=9.8, fill="#4E6B3E")
S.text(2, 244, "b", size=16, weight="bold")
S.text(232, 244, "c", size=16, weight="bold")
S.inline_svg(8, 250, 196, 134, svg_b)
S.inline_svg(238, 250, 372, 134, svg_c)
S.save(HERE / "fig_pacing2")
print("seed", seed, "fixed n/alarm/labels", f["n"], f["alarm"], f["labels"], "paced", p["n"], p["alarm"], p["labels"])
