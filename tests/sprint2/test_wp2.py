"""Tests for WP2 (sprint 2, Agent F): generators, DM/HAC monitor, runner economics, scoring."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import screen  # noqa: E402,F401
import wp2_analyze  # noqa: E402
import wp2_run  # noqa: E402
import wp2_score  # noqa: E402
import wp2_twins  # noqa: E402
from fam_f import WP2_REGIMES, DMHACMonitor, DepTwin, newey_west_var  # noqa: E402
from simulator import policy_rng, run_episode  # noqa: E402
from suite import stream_from_losses  # noqa: E402


def test_xu_acquisition_adapter_is_not_labeled_as_a_published_certificate():
    label = wp2_analyze.NULL_LABEL["xu_acquisition_only"]
    assert label == "V1 composite (ShiftLab certificate; Xu acquisition adapter)"
    assert "no Xu certificate" not in label and "ShiftLab certificate" in label


def _run(pol, losses, delay=24, budget=200, seed=0):
    preds, labels = stream_from_losses(losses, np.random.default_rng(seed))
    return run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=budget,
                       label_price=0.05, switch_cost=5.0, trace=True)


# ---------------------------------------------------------------- generators
def test_generators_marginal_and_exchangeable():
    """*_null / *_twin regimes have marginal challenger-win rate 1/2 on disagreements."""
    for name, R in WP2_REGIMES.items():
        if R.p_base != 0.5:
            continue
        wins = dis = 0
        for s in range(300):
            x = R.sample(np.random.default_rng(s))
            d = x[:, 0].astype(int) - x[:, 1]
            wins += (d > 0).sum()
            dis += (d != 0).sum()
        assert abs(wins / dis - 0.5) < 0.03, (name, wins / dis)


def test_twin_regime_has_episode_effect_and_dependence():
    tw, nl = WP2_REGIMES["WP2_iid_twin"], DepTwin("x", "iid")
    sd = lambda R: np.std([np.mean(R.sample(np.random.default_rng(s))[:, 0].astype(int)  # noqa: E731
                                   - R.sample(np.random.default_rng(s))[:, 1]) for s in range(200)])
    assert sd(tw) > 1.5 * sd(nl)  # episode-level fixed effect inflates across-episode spread
    s = WP2_REGIMES["WP2_o2_null"].signs(np.random.default_rng(0), 0.5, 20000)
    assert np.mean(s[1:] == s[:-1]) > 0.7  # strong second-order persistence
    better = WP2_REGIMES["WP2_sm_better"]
    x = np.concatenate([better.sample(np.random.default_rng(s)) for s in range(200)])
    d = x[:, 0].astype(int) - x[:, 1]
    assert abs((d > 0).sum() / (d != 0).sum() - 0.65) < 0.03


# ---------------------------------------------------------------- DM/HAC monitor
def test_newey_west_inflates_under_persistence():
    rng = np.random.default_rng(1)
    iid = rng.choice([-1.0, 1.0], 400)
    pers = np.repeat(rng.choice([-1.0, 1.0], 40), 10)
    assert newey_west_var(pers) > 3 * newey_west_var(iid)
    assert abs(newey_west_var(iid, lag=0) - iid.var()) < 1e-9


def test_dm_monitor_budget_and_short_null():
    rng = np.random.default_rng(3)
    for T in (50, 2000):
        losses = np.stack([rng.random(T) < 0.3, rng.random(T) < 0.3], axis=1).astype(np.int8)
        pol = DMHACMonitor(T, 200, 0.05, rng=policy_rng(1, 0, "DM"))
        res = _run(pol, losses)
        assert res.requested_labels <= 200
        if T == 50:  # fewer than burn-in evidence points -> never promotes
            assert res.deployment_switches == 0


def test_dm_monitor_promotes_on_clear_alternative_only():
    R = WP2_REGIMES["WP2_o2_better"].__class__("b", "iid", p_base=0.8)
    prom = [_run(DMHACMonitor(2000, 200, 0.05, rng=policy_rng(2, s, "DM")),
                 R.sample(np.random.default_rng(s))).deployment_switches > 0 for s in range(10)]
    assert sum(prom) >= 9
    N = DepTwin("n", "iid")
    prom = [_run(DMHACMonitor(2000, 200, 0.05, rng=policy_rng(2, s, "DM")),
                 N.sample(np.random.default_rng(s))).deployment_switches > 0 for s in range(40)]
    assert sum(prom) <= 6


def test_dm_monitor_only_queries_disagreements():
    T = 500
    l0 = np.zeros(T, np.int8)
    losses = np.stack([l0, l0], axis=1)  # never disagree
    res = _run(DMHACMonitor(T, 200, 0.05, rng=policy_rng(0, 0, "DM")), losses)
    assert res.requested_labels == 0


# ---------------------------------------------------------------- runner economics
def test_promo_stats_and_ei():
    T = 1000
    l0 = np.zeros(T, np.int8)
    l1 = np.zeros(T, np.int8)
    l0[600:610] = 1  # challenger better by 10 after t=600
    dep = np.r_[np.zeros(500, int), np.ones(500, int)]
    p = wp2_run.promo_stats(l0, l1, dep, 5.0)
    assert len(p) == 1 and p[0]["t"] == 500 and p[0]["rest_sum"] == 10 and p[0]["ei"] == 0
    assert p[0]["adv_100"] == 0.0 and p[0]["adv_500"] == 10 / 500
    l0[600:610] = 0
    l0[600:603] = 1  # benefit 3 < switch cost 5 -> EI
    assert wp2_run.promo_stats(l0, l1, dep, 5.0)[0]["ei"] == 1


def test_promo_stats_decision_flags_for_multiple_promotions_and_truncated_horizons():
    # Promotion at 2 has exactly the switch-cost benefit threshold (EI by <= convention);
    # promotion at 8 has only two events left, so its H=100/500 windows are truncated.
    l0 = np.zeros(10, np.int8)
    l1 = np.zeros(10, np.int8)
    l0[2] = 5
    dep = np.array([0, 0, 1, 1, 0, 0, 0, 0, 1, 1])
    promos = wp2_run.promo_stats(l0, l1, dep, 5.0)
    assert [p["t"] for p in promos] == [2, 8]
    assert [p["ei"] for p in promos] == [1, 1]
    assert [(p["n_100"], p["n_500"]) for p in promos] == [(8, 8), (2, 2)]
    assert [p["adv_100"] for p in promos] == [5 / 8, 0.0]


def test_runner_matches_screen_job():
    names = ["QSG", "DM_HAC_monitor", "CONTROL_never_switch"]
    a = screen._job(("synthetic", "F5_dep_null_r8", 0, 2, 99, names, 0.05))
    b = wp2_run._job(("synthetic", "F5_dep_null_r8", None, 0, 2, 99, names, 0.05, 1.0))
    assert [r["net"] for r in a] == [r["net"] for r in b]
    for r in b:
        assert r["labels"] <= r["budget"]
        assert abs(r["harm"] - (r["net"] - [x for x in b if x["policy"] == "CONTROL_never_switch"][0]["net"])) < 1e-9


def test_rewindow_preserves_events():
    l0 = np.arange(2 * 3 * 4).reshape(6, 4) % 2
    z = {"l0": l0, "l1": 1 - l0, "split": np.array([0, 0, 0, 1, 1, 1]), "ep": np.array([0, 1, 2] * 2)}
    v = wp2_twins.rewindow(z, 8)
    assert v["l0"].shape == (2, 8) and list(v["split"]) == [0, 1]
    assert np.array_equal(v["l0"][0], l0[:2].reshape(-1))


# ---------------------------------------------------------------- scoring
def test_score_bootstrap_ratio_and_rates():
    rows = []
    for c in range(10):
        for prom, ei in ((1, 1), (1, 0), (0, 0), (0, 0)):
            rows.append({"kind": "synthetic", "regime": "R", "split": -1, "ep": 0, "seed": c,
                         "policy": "p", "T": 2000, "delay_mult": 1.0, "ever_promote": prom, "ei": ei,
                         "db": -1.0 if ei else 3.0, "adv_100": 0.0, "adv_500": 0.1, "adv_rest": 0.01,
                         "first_deploy": 5 if prom else -1, "harm": 1.0, "labels": 10, "net": 3.0,
                         "runtime_s": 0.1})
    s = wp2_score.score(wp2_score.derive(pd.DataFrame(rows))).iloc[0]
    assert s.ever_promote == 0.5 and s.hp == 0.25 and s.pi_ei == 0.5 and s.v1_err_100 == 0.5
    assert s.v1_err_500 == 0.0 and s.clusters == 10
