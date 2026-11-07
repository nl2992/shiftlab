"""Unit tests for SOTA sprint family A (dependence-aware certification)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import fam_a
from fam_a import EXTRA, MarkovSUI, PostZeroMixture
from simulator import check_budget_feasible, check_no_future_access, policy_rng, run_episode


def markov_stream(rng, n_events, p, rho, dis=0.2):
    """Event-time Markov sign chain (regimes.py construction) -> (T, 2) losses."""
    s = rng.random() < p
    l0 = np.zeros(n_events, np.int8)
    l1 = np.zeros(n_events, np.int8)
    for t in range(n_events):
        if t and rng.random() >= rho:
            s = rng.random() < p
        if rng.random() < dis:
            l0[t], l1[t] = int(s), int(not s)
    return np.stack([l0, l1], 1)


def queried(rng, n, p, rho, dis=0.2):
    s = rng.random() < p
    z, ts, t = [], [], 0
    while len(z) < n:
        t += 1
        if rng.random() >= rho:
            s = rng.random() < p
        if rng.random() < dis:
            z.append(int(s))
            ts.append(t)
    return np.array(z), np.array(ts)


def run_e(ev, z, ts):
    vals, prev = [], None
    for k in range(len(z)):
        vals.append(ev.update(int(z[k]), int(ts[k] - ts[k - 1]) if k else 0, prev))
        prev = int(z[k])
    return np.array(vals)


def exact_ll(z, ts, p, rho):
    a = rho ** np.diff(ts)
    m = a * z[:-1] + (1 - a) * p
    return np.log(p if z[0] else 1 - p) + np.sum(np.log(np.where(z[1:] == 1, m, 1 - m)))


@pytest.mark.parametrize("name", ["A1", "A2", "A3", "A4", "A5", "A6"])
def test_budget_never_exceeded_and_no_future_access(name):
    rng = np.random.default_rng(0)
    losses = markov_stream(rng, 600, 0.65, 0.8, dis=0.4)
    labels = rng.integers(0, 2, 600)
    preds = labels[:, None] ^ losses.astype(int)
    for budget in (5, 30):
        pol = EXTRA[name](600, budget, 5.0, 0.05, 0.05, 20, lambda n: policy_rng(0, 0, n))
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=20,
            budget=budget,
            label_price=0.05,
            switch_cost=5.0,
        )
        assert res.requested_labels <= budget
        assert not check_budget_feasible(res, budget)
        assert not check_no_future_access(res, 20)
        assert all(0.0 <= r["query_probability"] <= 1.0 for r in res.records)


def test_null_upper_bound_dominates_every_null_member():
    """U (max over cells of the corner bound) >= exact likelihood at any null (p, rho)."""
    rng = np.random.default_rng(1)
    for p0, rho0 in ((0.5, 0.0), (0.5, 0.9), (0.4, 0.5), (0.65, 0.3)):
        z, ts = queried(rng, 80, p0, rho0)
        ev = MarkovSUI(started=False, n_rho=60, n_p=20)  # coarse grid: must still dominate
        run_e(ev, z, ts)
        ub = float(ev.cum.max())
        for p in np.linspace(0.01, 0.5, 25):
            for rho in np.r_[0.0, np.linspace(0.05, 0.999, 30), 1.0 - 1e-6]:
                assert exact_ll(z, ts, p, rho) <= ub + 1e-9


def test_eprocess_nonnegative_and_finite():
    rng = np.random.default_rng(2)
    z, ts = queried(rng, 60, 0.5, 0.95)
    for ev in (MarkovSUI(), PostZeroMixture(+1)):
        v = run_e(ev, z, ts)
        assert np.all(v >= 0) and np.all(np.isfinite(v))


@pytest.mark.parametrize("rho", [0.0, 0.8, 0.95])
def test_sui_null_false_rejection_small(rho):
    """Short null streams (p = 1/2): crossing frequency of 1/alpha well below alpha."""
    rng = np.random.default_rng(3 + int(rho * 100))
    n_rep, hits = 60, 0
    for _ in range(n_rep):
        z, ts = queried(rng, 50, 0.5, rho)
        hits += int(run_e(MarkovSUI(n_rho=80, n_p=30), z, ts).max() >= 20.0)
    assert hits / n_rep <= 0.05 + 2 * np.sqrt(0.05 * 0.95 / n_rep)


@pytest.mark.parametrize("rho", [0.0, 0.95])
def test_post_zero_null_false_rejection_small(rho):
    rng = np.random.default_rng(11)
    n_rep, hits = 300, 0
    for _ in range(n_rep):
        z, ts = queried(rng, 100, 0.5, rho)
        hits += int(run_e(PostZeroMixture(+1), z, ts).max() >= 20.0)
    assert hits / n_rep <= 0.05 + 2 * np.sqrt(0.05 * 0.95 / n_rep)


def test_post_zero_factor_conditional_mean():
    """After an unfavourable outcome, E[LR | past] <= 1 for every null (p, rho, gap)."""
    lr1, lr0 = np.log(2 * fam_a.GRID), np.log(2 * (1 - fam_a.GRID))
    for p in np.linspace(0, 0.5, 11):
        for rho in np.linspace(0, 1, 11):
            for g in (1, 3, 20):
                q = (1 - rho**g) * p  # P(z=1 | prev=0)
                assert np.all(q * np.exp(lr1) + (1 - q) * np.exp(lr0) <= 1 + 1e-12)


def test_sui_has_power_on_iid_alternative():
    rng = np.random.default_rng(4)
    z, ts = queried(rng, 200, 0.75, 0.0)
    assert run_e(MarkovSUI(), z, ts).max() >= 40.0


def test_rho_mle_recovers_persistence():
    rng = np.random.default_rng(5)
    z, ts = queried(rng, 150, 0.5, 0.9)
    assert fam_a.rho_mle(z, ts) >= 0.8
    z, ts = queried(rng, 150, 0.5, 0.0)
    assert fam_a.rho_mle(z, ts) <= 0.3
