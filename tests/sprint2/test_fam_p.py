"""Family P (sprint 2) unit tests: budget, short-stream null behaviour, and each mechanism."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import fam_p
import registry
from bench import SPRINT_REGIMES
from simulator import policy_rng, run_episode
from suite import stream_from_losses

NAMES = [k for k in fam_p.EXTRA]


def _run(name, losses, budget=200, delay=100, seed=0):
    r = lambda nm: policy_rng(7, seed, nm)
    pol = fam_p.EXTRA[name](losses.shape[0], budget, 5.0, 0.05, 0.05, delay, r)
    preds, labels = stream_from_losses(losses, np.random.default_rng(seed))
    return run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=delay,
        budget=budget,
        label_price=0.05,
        switch_cost=5.0,
        trace=True,
    )


def test_registered_and_import_clean():
    assert not registry.IMPORT_ERRORS
    for n in NAMES:
        assert n in registry.EXTRA
    for n in fam_p.P_REGIMES:
        assert n in SPRINT_REGIMES
    import importlib

    importlib.reload(fam_p)  # idempotent registration
    assert all(n in SPRINT_REGIMES for n in fam_p.P_REGIMES)


@pytest.mark.parametrize("name", NAMES)
def test_budget_never_exceeded(name):
    reg = SPRINT_REGIMES["F0_better"]
    losses = reg.sample(np.random.default_rng(3), 600)
    res = _run(name, losses, budget=30, delay=5)
    assert res.requested_labels <= 30
    assert all(r["budget_remaining"] >= 0 for r in res.records)


@pytest.mark.parametrize("name", [n for n in NAMES if n != "P3_follow"])
def test_short_null_stream_no_promotion(name):
    # 150 events of a null stream: no certified method may promote on so little evidence
    reg = SPRINT_REGIMES["F0_null"]
    for s in range(3):
        losses = reg.sample(np.random.default_rng(100 + s), 150)
        res = _run(name, losses, delay=5, seed=s)
        assert all(r["deployed_model"] == 0 for r in res.records)


def test_p4_generators_marginal_and_dependence():
    rng = np.random.default_rng(0)
    for nm, reg in fam_p.P_REGIMES.items():
        if not isinstance(reg, fam_p.PRegime):
            continue
        s = np.concatenate([reg.signs(rng, 2000) for _ in range(20)])
        assert abs(s.mean() - reg.marginal()) < 0.06, nm
        lag1 = np.corrcoef(s[:-1], s[1:])[0, 1]
        assert lag1 > 0.15, nm  # every misspecified class is serially dependent
        ll = reg.sample(rng)
        assert ll.shape == (2000, 2) and set(np.unique(ll)) <= {0, 1}
        assert np.allclose(reg.truth_gain(), reg.dis * (2 * reg.marginal() - 1))


def test_renewal_factor_mean_le_one_under_null_any_r():
    ev = fam_p.RenewalEvidence()
    for n in range(2, 30):
        ls = np.arange(1, n)
        for r in (0.3, 0.7, 1.0):
            w = r**ls / np.sum(r**ls)  # P(L1 = l | n) under the null, r <= 1
            m = np.array([ev.factor(int(li), n - int(li)) for li in ls])  # (n-1, grid)
            assert np.all(w @ m <= 1.0 + 1e-9)
        # under the alternative (r > 1) the factor has mean > 1 for n >= 3
        if n >= 3:
            w = 2.0**ls / np.sum(2.0**ls)
            m = np.array([ev.factor(int(li), n - int(li)) for li in ls])
            assert np.all(w @ m > 1.0)


def test_renewal_cycle_bookkeeping():
    ev = fam_p.RenewalEvidence()
    for h in [1, 1, 0, 1, 1, 1, 0, 0, 1]:  # leading partial run ignored; cycles (3,2) closed
        ev.update(h)
    assert ev.k == 1 and ev.l1 == 1 and ev.l0 == 0


def test_renewal_bruteforce_null_any_persistence():
    """Exact Markov null with i.i.d. gaps: P(sup E >= 1/a) <= a at a = .2 for rho up to .98."""
    rng = np.random.default_rng(11)
    for rho in (0.0, 0.8, 0.98):
        hits = 0
        for _ in range(300):
            z, _ = fam_p._chain_queries(rng, 0.5, rho, 0.2, 4, 200)
            ev = fam_p.RenewalEvidence()
            mx = 0.0
            for zi in z:
                mx = max(mx, ev.update(int(zi)))
            hits += mx >= 5.0
        assert hits / 300 <= 0.2 + 0.07, rho


def test_uniform_start_sui_weights_sum_to_one_and_late_start_cheaper():
    u = fam_p.UniformStartSUI(n_starts=20, stride=10, rho_prior=fam_p.fam_a._B["rho_prior"])
    b = fam_p.fam_a.MarkovSUI(**fam_p.fam_a._B)
    # 150 unfavourable then 50 favourable outcomes: a late start must carry more evidence in U
    seq = [0, 0, 1] * 50 + [1, 1, 1, 0] * 12
    prev = None
    for h in seq:
        u.update(h, 1, prev)
        b.update(h, 1, prev)
        prev = h
    assert len(u.starts) <= 20
    assert u.log_value > b.log_value


def test_capmix_invalid_component_documented():
    # a cap-.5 component on a rho=.98 null stream is not a supermartingale: it explodes
    rng = np.random.default_rng(1)
    exploded = 0
    for _ in range(20):
        z, t = fam_p._chain_queries(rng, 0.5, 0.98, 0.2, 1, 150)
        m = fam_p.fam_a.MarkovSUI(rho_max=0.5, **fam_p.fam_a._B)
        prev, lt, mx = None, None, 0.0
        for zi, ti in zip(z, t):
            mx = max(mx, m.update(int(zi), 0 if lt is None else int(ti - lt), prev))
            prev, lt = int(zi), ti
        exploded += mx >= 20
    assert exploded >= 5


def test_kgate_k3_budget_and_null():
    reg = fam_p.K_REGIMES["K3_null"]
    for s in range(3):
        losses = reg.sample(np.random.default_rng(s), 800)
        r = lambda nm: policy_rng(5, s, nm)  # noqa: B023
        pol = fam_p.KGate(3, 800, 40, 0.05, rng=r("D_gate"), host_rng=r("cams"))
        preds, labels = stream_from_losses(losses, np.random.default_rng(s))
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=10,
            budget=40,
            label_price=0.05,
            switch_cost=5.0,
        )
        assert res.requested_labels <= 40


def test_kgate_promotes_clear_winner():
    reg = fam_p.KRegime("Kclear", (((0, 0.5),), ((0, 0.95),)), dis=0.3)
    losses = reg.sample(np.random.default_rng(0), 2000)
    r = lambda nm: policy_rng(5, 0, nm)
    pol = fam_p.KGate(3, 2000, 200, 0.05, rng=r("D_gate"), host_rng=r("cams"))
    preds, labels = stream_from_losses(losses, np.random.default_rng(0))
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=10,
        budget=200,
        label_price=0.05,
        switch_cost=5.0,
    )
    dep = [rec["deployed_model"] for rec in res.records]
    assert dep[-1] == 2


def test_k_regime_truth():
    reg = fam_p.K_REGIMES["K4_mixed"]
    L = np.concatenate([reg.sample(np.random.default_rng(s)) for s in range(10)])
    g = (L[:, [0]].astype(float) - L).mean(axis=0)
    assert np.allclose(g, reg.truth_gain()[0], atol=0.02)


def test_p6_reserve_kept_for_detector():
    reg = SPRINT_REGIMES["F0_null"]
    losses = reg.sample(np.random.default_rng(2), 2000)
    r = lambda nm: policy_rng(9, 0, nm)
    pol = fam_p.EXTRA["P6_RRD"](2000, 200, 5.0, 0.05, 0.05, 100, r)
    preds, labels = stream_from_losses(losses, np.random.default_rng(2))
    run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=100,
        budget=200,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert pol.n_own >= 40  # at least most of the 50-label reserve went to the detector


def test_fisher_efficiency_drops_with_persistence():
    r = [
        fam_p.fisher_efficiency(0.6, a)[1] / fam_p.fisher_efficiency(0.6, a)[0]
        for a in (0.1, 0.5, 0.9)
    ]
    assert r[0] > r[1] > r[2]
    assert math.isfinite(r[2])


def test_p6_no_reserve_detector_still_acquires():
    # regression: with reserve=0 the detector must pace the whole remaining budget (as RMM)
    reg = SPRINT_REGIMES["F0_null"]
    losses = reg.sample(np.random.default_rng(4), 2000)
    r = lambda nm: policy_rng(9, 1, nm)
    pol = fam_p.EXTRA["P6_LRMD_U"](2000, 200, 5.0, 0.05, 0.05, 100, r)
    preds, labels = stream_from_losses(losses, np.random.default_rng(4))
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=100,
        budget=200,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert res.requested_labels >= 150
