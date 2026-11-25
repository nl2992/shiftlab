"""Figure 1: the mechanism on one real synthetic stream (boundary_local_harm, r = 0.05).

Panel a: which events are agreements, where each monitor buys labels. Panel b: log-evidence of each monitor.
All values come from running the repository's replay code on one stream; nothing is drawn by hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import ndtr

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
from make_figures import P, W, label, style  # noqa: E402

from shiftlab.decision_harm_experiment import SCENARIOS, ExperimentConfig, _generate, _source_action  # noqa: E402
from shiftlab.dive.experiment import _binary_cost, _synthetic_label_costs  # noqa: E402
from shiftlab.dive.gated_monitor_comparison import replay_gated  # noqa: E402
from shiftlab.dive.predictable_bound_replay import replay_mixture_log_e  # noqa: E402

R, EPS, ALPHA = 0.05, 0.1, 0.05


def stream(seed: int):
    scen = next(s for s in SCENARIOS if s.name == "boundary_local_harm")
    cfg = ExperimentConfig(n=3200, d=16, evaluation_seeds=1, calibration_seeds=2, calibration_start=800, window=64,
                           stride=32, alpha=ALPHA, eprocess_epsilon=EPS, seed_offset=seed, change_fraction=0.5,
                           device="cpu")
    _, frame, oracle, timing = _generate(scen, seed, cfg)
    x = np.stack(frame.features.to_numpy()).astype(float)
    y = frame.target.to_numpy(dtype=float) > 0
    deployed = (ndtr((x[:, 0] - 0.9 * x[:, 1]) / 0.3) >= 0.5).astype(int)
    ref = _source_action(x, scen)
    c = _binary_cost(deployed, y, scen.fn_cost, scen.fp_cost) - _binary_cost(ref, y, scen.fn_cost, scen.fp_cost)
    return x, deployed != ref, c, _synthetic_label_costs(x)


def run(seed: int):
    x, act, c, tar = stream(seed)
    coins = np.random.default_rng(seed + 9_173).random(3200)
    kw = dict(x=x[800:], paired_cost=c[800:], disagreement=act[800:], tariffs=tar[800:], uniforms=coins[:2400],
              validation_disagreement=act[400:800], validation_tariffs=tar[400:800], budget_rate=R)
    out = {}
    for arm in ("gated_ht_fixed", "gated_ht_paced"):
        res = replay_gated(arm=arm, **kw)
        out[arm] = (res.log_e, res.queried)
    # uniform labelling at rate R on every event, prediction-powered bound
    q_u = coins[:2400] < R
    vals = -EPS + np.where(q_u, c[800:] / R, 0.0)
    out["uniform"] = (replay_mixture_log_e(vals, 5.1 * (2 / R - 1), alpha=ALPHA), q_u)
    out["full"] = (replay_mixture_log_e(c[800:] - EPS, 5.1, alpha=ALPHA), np.ones(2400, bool))
    return act[800:], out


def alarm(log_e):
    hit = np.flatnonzero(np.asarray(log_e) >= -np.log(ALPHA))
    return int(hit[0]) if len(hit) else None


def pick_seed():
    """First registered seed where full feedback and gated HT alarm and uniform does not (the typical cell at r=0.05)."""
    for seed in range(58400000, 58400100):
        a, out = run(seed)
        if alarm(out["full"][0]) and alarm(out["gated_ht_fixed"][0]) and alarm(out["gated_ht_paced"][0]) \
                and alarm(out["uniform"][0]) is None:
            return seed, a, out
    raise RuntimeError("no typical seed")


def main():
    style()
    seed, act, out = pick_seed()
    n = 2400
    onset = 800
    fig = plt.figure(figsize=(W, 3.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 2.1], hspace=0.28)

    ax = fig.add_subplot(gs[0])
    t = np.arange(n)
    ax.vlines(t[act], 0.55, 1.0, color=P["red"], lw=0.5, label="Policies disagree")
    qg = out["gated_ht_fixed"][1]
    ax.vlines(t[:len(qg)][qg], 0.05, 0.45, color=P["blue"], lw=0.9, label="Gated: label bought")
    qu = out["uniform"][1]
    ax.vlines(t[qu], -0.45, -0.05, color=P["grey"], lw=0.9, label="Uniform: label bought")
    ax.axvline(onset, color=P["dark"], ls="--", lw=1)
    ax.text(onset + 25, 1.05, "harm onset", fontsize=7.5, va="bottom")
    ax.set_xlim(0, n)
    ax.set_ylim(-0.5, 1.05)
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.spines["left"].set_visible(False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.12), ncol=3, handlelength=1.0, columnspacing=1.2)
    label(ax, "a")

    ax = fig.add_subplot(gs[1])
    spec = [("full", "Full feedback (all labels)", P["dark"], "--"),
            ("gated_ht_fixed", "Gated, fixed rate", P["blue"], "-"),
            ("gated_ht_paced", "Gated, past-paced", P["blue2"] if "blue2" in P else P["blue"], "-"),
            ("uniform", "Uniform labelling", P["red"], "-")]
    for key, name, col, ls in spec:
        le = np.asarray(out[key][0])
        ax.plot(np.arange(len(le)), le, color=col, ls=ls, lw=1.8, label=name)
        a = alarm(le)
        if a is not None:
            ax.plot(a, le[a], "o", color=col, ms=4.5, zorder=5)
    ax.axhline(-np.log(ALPHA), color=P["grey"], lw=1, ls=":")
    ax.text(n - 10, -np.log(ALPHA) + 0.12, "alarm threshold $\\log(1/\\alpha)$", ha="right", va="bottom", fontsize=7.5,
            color=P["grey"])
    ax.axvline(onset, color=P["dark"], ls="--", lw=1)
    ax.set_xlim(0, n)
    ax.set_ylim(-1, 9)
    ax.set_xlabel("Monitored events (monitor starts at event 800)")
    ax.set_ylabel("Log-evidence against the null")
    ax.legend(loc="upper left", handlelength=1.6)
    label(ax, "b")
    fig.savefig(HERE / "fig_overview.pdf", bbox_inches="tight", pad_inches=0.05)
    fig.savefig(HERE / "fig_overview.png", bbox_inches="tight", pad_inches=0.05, dpi=300)
    print("seed", seed, {k: alarm(v[0]) for k, v in out.items()}, "labels:",
          {k: int(np.asarray(v[1]).sum()) for k, v in out.items()}, "disagree rate", round(float(act.mean()), 3))


if __name__ == "__main__":
    main()
