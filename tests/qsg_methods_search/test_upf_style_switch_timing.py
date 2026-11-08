"""Tests for the T3 UPF-style switch-timing adapter (not UPF / not Regol et al.'s algorithm)."""
# Ported from origin/claude/shiftlab-methods-strategy-dba13e:tests/sota_fidelity/test_upf_style_switch_timing.py (adds scripts/qsg_methods_search to sys.path).

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (
    ROOT / "scripts/failure_atlas_v2_flq",
    ROOT / "scripts/promising_directions/sota",
    ROOT / "scripts/promising_directions/sota/competitors",
    ROOT / "src",
    ROOT / "scripts/qsg_methods_search",
):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from regimes import ALL_REGIMES, _r
from simulator import (
    ReleasedFeedback,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)
from upf_style_switch_timing import (
    UPFStyleSwitchTimingT3,
    beta_parameters,
    plan_switch,
)

BIG = 1e6  # concentration: Beta(mu*BIG, (1-mu)*BIG) is effectively a point mass at mu


def point_mass(mus):
    mu = np.asarray(mus, dtype=float)
    return mu * BIG, (1 - mu) * BIG


def plan(mus, arm=0, cs=0.05, **kw):
    a, b = point_mass(mus)
    return plan_switch(
        a, b, arm, cs, draws=kw.pop("draws", 200), rng=np.random.default_rng(0), **kw
    )


# --------------------------------------------------------------------------- quantile rule
def test_hand_built_two_period_cases():
    # arm0 costs .3 per period, arm1 .1: keep 0.6 vs switch .05+.1+.1 = .25 -> switch
    assert plan([[0.3, 0.3], [0.1, 0.1]])[0] is True
    # arm1 .29: switch .05+.29+.29 = .63 > keep .60 -> stay
    assert plan([[0.3, 0.3], [0.29, 0.29]])[0] is False
    # reversible: from arm 1 with arm0 much better, switching back pays
    assert plan([[0.1, 0.1], [0.3, 0.3]], arm=1)[0] is True
    # exact margin: keep branch is .3 + V(arm0, period 1) = .3 + min(.3, .05+.1) = .45 (it can
    # still switch next period); switch branch .05 + .1 + .1 = .25
    _, margin = plan([[0.3, 0.3], [0.1, 0.1]])
    assert margin == pytest.approx(0.45 - 0.25, abs=1e-3)


def test_switch_can_be_deferred():
    # arm1 slightly worse in period 0, much better in period 1. Keep branch defers the switch to
    # period 1: .3 + min(.3, .05 + .1) = .45. Switching now: .05 + .32 + .1 = .47. So stay now.
    sw, margin = plan([[0.3, 0.3], [0.32, 0.1]])
    assert sw is False and margin == pytest.approx(0.45 - 0.47, abs=1e-3)


def test_delta_quantile_is_risk_averse():
    # one period, no cost: arm1 has lower mean but much higher variance
    a = np.array([[0.3 * BIG], [4.0 * 0.25]])
    b = np.array([[0.7 * BIG], [4.0 * 0.75]])  # arm1 Beta(1, 3): mean .25, wide
    kw = {"draws": 20000, "rng": np.random.default_rng(1)}
    assert plan_switch(a, b, 0, 0.0, delta=0.5, **kw)[0] is True
    assert plan_switch(a, b, 0, 0.0, delta=0.95, **kw)[0] is False


def test_one_period_matches_t2_port_retraining_rule():
    pytest.importorskip("torch")  # the T2 port imports torch; absent in some environments
    from shiftlab.dive.upf_retraining import upf_retraining_schedule

    rng = np.random.default_rng(3)
    for _ in range(8):
        mu0, mu1 = rng.uniform(0.05, 0.6, 2)
        cs = float(rng.uniform(0.0, 0.2))
        mine = plan([[mu0], [mu1]], cs=cs)[0]
        # T2 port: model 0 = incumbent, model 1 = retrained at t=1; alpha = cost
        a = np.array([[mu0 * BIG], [mu1 * BIG]])
        b = np.array([[(1 - mu0) * BIG], [(1 - mu1) * BIG]])
        sched, _ = upf_retraining_schedule(a, b, retraining_cost=cs, monte_carlo_draws=200)
        assert mine == bool(sched[1, 0]) or abs((mu0) - (mu1 + cs)) < 1e-3


def test_beta_conversion_matches_t2_port():
    pytest.importorskip("torch")
    from shiftlab.dive.upf_retraining import BetaPerformanceForecaster

    class Stub:
        def predict(self, x):
            return np.array([0.0, 0.2, 0.5, 1.0])

    for var in (1e-12, 0.01, 0.3):
        port = BetaPerformanceForecaster(Stub(), var, 5)
        pa, pb = port.predict_beta_parameters(np.zeros((4, 4)))
        ma, mb = beta_parameters(Stub().predict(None), var)
        np.testing.assert_allclose(ma, pa)
        np.testing.assert_allclose(mb, pb)


def test_null_cells_stay_across_seeds():
    a, b = point_mass(np.full((2, 15), 0.1))
    for s in range(10):
        assert plan_switch(a, b, 0, 0.05, draws=300, rng=np.random.default_rng(s))[0] is False


# --------------------------------------------------------------------------- IPW cells
def test_ipw_cells_unbiased_monte_carlo():
    m, reps = 100, 3000
    gen = np.random.default_rng(5)
    dis = gen.random(m) < 0.3  # fixed disagreement pattern for the period
    sign = gen.random(m) < 0.6  # True: arm1 correct on a disagreement
    l0 = np.where(dis, sign, 0).astype(np.int8)
    l1 = np.where(dis, ~sign, 0).astype(np.int8)
    truth = np.array([l0.sum(), l1.sum()]) / m
    q = np.where(dis, 0.4, 0.0)
    est = np.zeros((reps, 2))
    for r in range(reps):
        pol = UPFStyleSwitchTimingT3(m, 10, 5.0, 1, rng=np.random.default_rng(r), m=m)
        fb = [
            ReleasedFeedback(t, t, t + 1, 0, np.array([l0[t], l1[t]]), float(q[t]))
            for t in np.flatnonzero(dis)
            if gen.random() < q[t]
        ]
        pol.observe(fb)
        est[r] = pol.cell_estimates()[0]
    se = est.std(axis=0) / np.sqrt(reps)
    assert np.all(np.abs(est.mean(axis=0) - truth) < 4 * se)
    # HT variance estimator is itself unbiased for the cell variance
    assert est.std(axis=0)[0] > 0


# --------------------------------------------------------------------------- adapter on streams
def episode(regime, seed, *, T=2000, budget=200, m=100, draws=400):
    reg = ALL_REGIMES[regime] if isinstance(regime, str) else regime
    rng = np.random.default_rng(1000 + seed)
    losses = reg.sample(rng, T)
    labels = rng.integers(0, 2, T)
    preds = labels[:, None] ^ losses.astype(int)
    pol = UPFStyleSwitchTimingT3(
        T, budget, 5.0, reg.delay, rng=policy_rng(11, seed, "upf"), m=m, draws=draws
    )
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=reg.delay,
        budget=budget,
        label_price=0.05,
        switch_cost=5.0,
    )
    return pol, res, reg


def test_no_disagreement_stream_never_switches():
    reg = _r("identical", "null", [(0, 0.5)], dis=((0, 0.0),))
    for s in range(3):
        _, res, _ = episode(reg, s)
        assert res.deployment_switches == 0


def test_switches_when_challenger_much_better():
    reg = _r("strong", "alt", [(0, 0.9)], dis=((0, 0.3),), delay=50)
    for s in range(3):
        pol, res, _ = episode(reg, s)
        dep = [r["deployed_model"] for r in res.records]
        assert dep[-1] == 1 and res.deployment_switches == 1
        assert min(i for i, d in enumerate(dep) if d == 1) >= 100 * pol.min_periods


@pytest.mark.parametrize("regime", ["F0_null", "F0_better", "F3_reversal_800"])
def test_adapter_contract_budget_determinism_released_only(regime):
    pol, res, reg = episode(regime, 0)
    assert check_budget_feasible(res, 200) == []
    assert check_no_future_access(res, reg.delay) == []
    assert res.refused_requests == 0 and res.requested_labels <= 200
    _pol2, res2, _ = episode(regime, 0)
    assert [r["deployed_model"] for r in res.records] == [r["deployed_model"] for r in res2.records]
    assert [r["requested"] for r in res.records] == [r["requested"] for r in res2.records]
    assert res.net_cost == res2.net_cost
    # every cell used at a planning step is over and fully released by that step
    rel = {r["event_id"]: r["release_time"] for r in res.records if r["requested"]}
    for e in pol.fit_log:
        if e["action"] == "warmup":
            continue
        assert e["max_release_used"] <= e["t"]
        for j in e["used_periods"]:
            assert (j + 1) * pol.m - 1 + reg.delay <= e["t"]
            assert all(rel[i] <= e["t"] for i in rel if i // pol.m == j)
    # switches only at period boundaries, never before min_periods usable periods
    dep = np.array([r["deployed_model"] for r in res.records])
    for t in np.flatnonzero(np.diff(dep)) + 1:
        assert t % pol.m == 0
        assert pol.fit_log and any(e["t"] == t and e["action"] == "switch" for e in pol.fit_log)


def test_state_dict_roundtrip():
    pol, _, _ = episode("F0_better", 0)
    s = pol.state_dict()
    other = UPFStyleSwitchTimingT3(2000, 200, 5.0, 100, rng=np.random.default_rng(0))
    other.load_state_dict(s)
    np.testing.assert_array_equal(other.cell_estimates(), pol.cell_estimates())
    assert other.deployed == pol.deployed
