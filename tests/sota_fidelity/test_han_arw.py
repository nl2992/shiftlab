"""Tests for the Han et al. ARW port (T2 core) and the label-clock adapter (T3).

Hand-computed numbers use L = log(2/d') with d' = 0.1, i.e. L = log 20 = 2.995732...
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SOTA = ROOT / "scripts/promising_directions/sota"
for p in (SOTA, SOTA / "competitors", ROOT / "scripts/failure_atlas_v2_flq"):
    sys.path.insert(0, str(p))

import han_arw as h
from regimes import Regime
from simulator import (
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)

L = math.log(20.0)


# ------------------------------------------------------------------ hand-computed core
def test_hand_computed_three_points_both_constant_sets():
    u = np.array([1.0, -1.0, -1.0])  # oldest to newest
    # windows: k=1 {-1}, k=2 {-1,-1}, k=3 {1,-1,-1}
    # mu = -1, -1, -1/3 ; v3^2 = (16/9 + 8/9)/2 = 4/3
    v3 = math.sqrt(4.0 / 3.0)
    # paper_experiments: M=0, d'=0.1 -> psi = (0, 0, v3 sqrt(2L/3))
    r = h.arw_window_from_samples(u, constants="paper_experiments")
    np.testing.assert_allclose(r.mu, [-1.0, -1.0, -1.0 / 3.0])
    np.testing.assert_allclose(r.psi, [0.0, 0.0, v3 * math.sqrt(2 * L / 3)])
    np.testing.assert_allclose(r.phi, [0.0, 0.0, 0.0])  # |-1/3+1| = .667 < psi3 = 1.632
    assert r.k_hat == 1  # crit = (0, 0, 1.63): first minimiser

    # theory with delta=0.9, t=3 -> d' = 0.9/(3*3) = 0.1 (same L), M = b-a = 2
    r = h.arw_window_from_samples(u, constants="theory", delta=0.9, value_range=2.0)
    assert r.d_prime == pytest.approx(0.1)
    psi2 = 8 * 2 * L / (3 * 1)  # v=0, B-1 = 1
    psi3 = v3 * math.sqrt(2 * L / 3) + 8 * 2 * L / (3 * 2)
    np.testing.assert_allclose(r.psi, [2.0, psi2, psi3])  # psi(B=1) = M
    np.testing.assert_allclose(r.phi, [0.0, 0.0, 0.0])
    assert r.k_hat == 1  # crit = (2, 15.98, 9.62)


def test_bias_proxy_positive_part_hand_computed():
    # 10 old zeros then 10 new ones, M=0, d'=0.1: psi_k = 0 for k <= 10 (constant windows)
    u = np.r_[np.zeros(10), np.ones(10)]
    r = h.arw_window_from_samples(u, constants="paper_experiments")
    v20 = math.sqrt(20.0 / 19.0 * (0.5 - 0.25))
    psi20 = v20 * math.sqrt(2 * L / 20)
    assert r.psi[19] == pytest.approx(psi20)
    assert r.phi[19] == pytest.approx(0.5 - psi20)  # max_i |0.5 - 1| - (psi20 + 0)
    assert r.phi[19] > 0
    assert r.k_hat == 1  # crit(k<=10) = 0 and the first minimiser wins


def test_theory_vs_experiments_constants_differ():
    assert h.resolve_constants("theory", 10, 0.05, 2.0) == (2.0, 0.05 / 30)
    assert h.resolve_constants("paper_experiments", 10) == (0.0, 0.1)
    with pytest.raises(ValueError):
        h.resolve_constants("nonsense", 3)


def test_vectorised_matches_scalar_reference():
    rng = np.random.default_rng(0)
    periods = [rng.integers(0, 2, rng.integers(2, 5)).astype(float) for _ in range(15)]
    B, m, o = h.period_summaries(periods)
    M, dp = 1.0, 0.1
    res = h.arw_window(B, m, o, M=M, d_prime=dp)
    t = len(periods)

    def stats(k):  # direct Eq. (3.1)-(3.3) on the pooled raw samples
        x = np.concatenate(periods[t - k :])
        n = len(x)
        mu = x.mean()
        v = math.sqrt(((x - mu) ** 2).sum() / (n - 1)) if n > 1 else 0.0
        psi = M if n == 1 else v * math.sqrt(2 * L / n) + 8 * M * L / (3 * (n - 1))
        return mu, psi

    mus, psis = zip(*[stats(k) for k in range(1, t + 1)], strict=True)
    np.testing.assert_allclose(res.mu, mus)
    np.testing.assert_allclose(res.psi, psis)
    phi = [
        max(0.0, max(abs(mus[k] - mus[i]) - psis[k] - psis[i] for i in range(k + 1)))
        for k in range(t)
    ]
    np.testing.assert_allclose(res.phi, phi)
    assert res.k_hat == int(np.argmin(np.array(phi) + np.array(psis))) + 1


def test_zero_size_period_rejected():
    with pytest.raises(ValueError):
        h.period_summaries([np.array([1.0]), np.array([])])


# ------------------------------------------------------------------ statistical behaviour
def _batches(spec, rng, size=100):
    return [(rng.random(size) < p).astype(float) for n, p in spec for _ in range(n)]


@pytest.mark.parametrize("constants", h.CONSTANT_SETS)
def test_stationary_iid_selects_longest_window(constants):
    full = 0
    for s in range(50):
        per = _batches([(20, 0.5)], np.random.default_rng(s))
        B, m, o = h.period_summaries(per)
        M, dp = h.resolve_constants(constants, 20, 0.05, 1.0)
        full += h.arw_window(B, m, o, M=M, d_prime=dp).k_hat == 20
    assert full >= 47


def test_stationary_label_clock_theory_selects_longest():
    full = 0
    for s in range(50):
        u = np.where(np.random.default_rng(s).random(60) < 0.5, 1.0, -1.0)
        full += h.arw_window_from_samples(u, constants="theory").k_hat == 60
    assert full >= 47


def test_paper_experiments_degenerate_on_label_clock():
    # M=0 and B=1 give psi(1) = 0, hence crit(1) = 0 = global minimum: always the newest label.
    u = np.where(np.random.default_rng(0).random(60) < 0.5, 1.0, -1.0)
    assert h.arw_window_from_samples(u, constants="paper_experiments").k_hat == 1


@pytest.mark.parametrize("constants,lo,hi", [("paper_experiments", 10, 10), ("theory", 10, 16)])
def test_abrupt_change_shrinks_to_post_change_data(constants, lo, hi):
    ks = []
    for s in range(40):
        per = _batches([(20, 0.2), (10, 0.8)], np.random.default_rng(s))
        B, m, o = h.period_summaries(per)
        M, dp = h.resolve_constants(constants, 30, 0.05, 1.0)
        ks.append(h.arw_window(B, m, o, M=M, d_prime=dp).k_hat)
    ks = np.array(ks)
    assert (ks < 30).all()  # never the stale full window
    assert np.mean((ks >= lo) & (ks <= hi)) >= 0.9


# ------------------------------------------------------------------ tie rule
def test_tie_rule_paper_vs_code():
    zeros = np.zeros(6)  # every gap 0, Delta_hat = 0 exactly
    assert h.pairwise_compare(zeros, tie_rule="paper")[0] == 0  # Alg. 2: <= 0 -> f1
    assert h.pairwise_compare(zeros, tie_rule="code")[0] == 1  # code: < 0 -> f1 else f2
    pos, neg = np.ones(6), -np.ones(6)
    assert h.pairwise_compare(pos, tie_rule="paper")[0] == 1
    assert h.pairwise_compare(pos, tie_rule="code")[0] == 1
    assert h.pairwise_compare(neg, tie_rule="paper")[0] == 0
    assert h.pairwise_compare(neg, tie_rule="code")[0] == 0
    # margin extension: needs a gap above the margin
    assert h.pairwise_compare(pos, margin=1.5)[0] == 0
    assert h.pairwise_compare(pos, margin=0.5)[0] == 1
    with pytest.raises(ValueError):
        h.pairwise_compare(pos, tie_rule="x")


# ------------------------------------------------------------------ adapter through the simulator
T, BUDGET, DELAY = 800, 80, 40


def _losses(p, seed, horizon=T):
    reg = Regime("t", "t", tuple(p), delay=DELAY)
    return reg.sample(np.random.default_rng(seed), horizon)


def _run(losses, seed, **kw):
    s = np.random.default_rng([seed, 7])
    labels = s.integers(0, 2, losses.shape[0])
    preds = labels[:, None].astype(int) ^ losses.astype(int)
    pol = h.HanARWDeploymentAdapter(losses.shape[0], BUDGET, rng=policy_rng(1, seed, "han"), **kw)
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=DELAY,
        budget=BUDGET,
        label_price=0.05,
        switch_cost=5.0,
    )
    return pol, res


@pytest.mark.parametrize("name,p", [("null", [(0, 0.5)]), ("reversal", [(0, 0.7), (400, 0.3)])])
@pytest.mark.parametrize("constants", h.CONSTANT_SETS)
def test_adapter_smoke_budget_delay_determinism(name, p, constants):
    losses = _losses(p, 3)
    pol, res = _run(losses, 3, constants=constants)
    assert res.requested_labels <= BUDGET
    assert check_budget_feasible(res, BUDGET) == []
    assert check_no_future_access(res, DELAY) == []
    assert len(pol.u) <= res.requested_labels
    _, res2 = _run(losses, 3, constants=constants)
    a = [(r["deployed_model"], r["requested"]) for r in res.records]
    b = [(r["deployed_model"], r["requested"]) for r in res2.records]
    assert a == b


def test_adapter_promotes_then_rolls_back_on_reversal():
    losses = _losses([(0, 0.8), (400, 0.2)], 5)
    _, res = _run(losses, 5, constants="paper_experiments")
    dep = np.array([r["deployed_model"] for r in res.records])
    assert dep[100:350].mean() > 0.5  # candidate while it is better
    assert dep[-100:].mean() < 0.5  # rolled back after the reversal and the label delay


def test_adapter_incumbent_before_any_label():
    losses = _losses([(0, 0.9)], 1)
    _, res = _run(losses, 1)
    dep = [r["deployed_model"] for r in res.records]
    first_release = min(r["release_time"] for r in res.records if r["release_time"] is not None)
    assert set(dep[:first_release]) == {0}


def test_adapter_uses_no_future_information():
    tau = 500
    a = _losses([(0, 0.6)], 11)
    b = a.copy()
    b[tau + 1 :] = _losses([(0, 0.05)], 99)[tau + 1 :]  # different future
    _, ra = _run(a, 11)
    _, rb = _run(b, 11)
    key = lambda r: (r["deployed_model"], r["requested"], r["decision_state"])
    assert [key(r) for r in ra.records[: tau + 1]] == [key(r) for r in rb.records[: tau + 1]]


def test_adapter_state_roundtrip():
    losses = _losses([(0, 0.7)], 2)
    pol, _ = _run(losses, 2)
    other = h.HanARWDeploymentAdapter(T, BUDGET, rng=np.random.default_rng(0))
    other.load_state_dict(pol.state_dict())
    assert other.deployed == pol.deployed and other.u == pol.u
