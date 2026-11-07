"""Unit tests for Family D (deploy-or-abstain wrapper over fast selectors)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import fam_d
from fam_d import EXTRA, DeployGate, make_host
from regimes import REGIMES
from simulator import policy_rng, run_episode
from suite import stream_from_losses

CANDIDATES = ["D1", "D2", "D3", "D4", "D5", "D6:mp", "D6:cams", "D6:ms"]


def _run(name, regime="F0_null", seed=0, T=2000, B=200, delay=None):
    R = REGIMES[regime]
    losses = R.sample(np.random.default_rng(seed), T)
    preds, labels = stream_from_losses(losses, np.random.default_rng(seed + 1))
    d = R.delay if delay is None else delay
    pol = EXTRA[name](T, B, 5.0, 0.05, 0.05, d, lambda n: policy_rng(11, seed, n))
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=d,
        budget=B,
        label_price=0.05,
        switch_cost=5.0,
        trace=True,
    )
    return pol, res


@pytest.mark.parametrize("name", CANDIDATES)
@pytest.mark.parametrize("regime", ["F9_highdis_better", "F0_null"])
def test_budget_respected(name, regime):
    for B in (30, 200):
        _, res = _run(name, regime, B=B)
        assert res.requested_labels <= B
        assert res.refused_requests == 0  # the policy never asks beyond the cap


@pytest.mark.parametrize("name", ["D1", "D2", "D4", "D5", "D6:mp", "D6:cams", "D6:ms"])
def test_gate_blocks_promotion_on_short_null(name):
    # short null streams: the native hosts promote often here; the gate must not
    promoted = 0
    for seed in range(15):
        _, res = _run(name, "F0_null", seed=seed, T=300, B=60, delay=10)
        promoted += any(r["deployed_model"] == 1 for r in res.records)
    assert promoted == 0


def test_native_hosts_do_promote_on_short_null():
    # sanity: the property above is non-trivial (the hosts alone would promote)
    from suite import build_suite

    n = 0
    for seed in range(15):
        R = REGIMES["F0_null"]
        losses = R.sample(np.random.default_rng(seed), 300)
        preds, labels = stream_from_losses(losses, np.random.default_rng(seed + 1))
        pol = build_suite(300, 60, 5.0, 0.05, 0.05, 10, seed, 11, names=["model_picker_adapter"])[0]
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=10,
            budget=60,
            label_price=0.05,
            switch_cost=5.0,
        )
        n += res.deployment_switches > 0
    assert n >= 3


@pytest.mark.parametrize("kind", ["mp", "cams", "ms"])
def test_wrapper_runs_on_every_host_and_promotes_on_clear_advantage(kind):
    T, B = 2000, 200
    R = REGIMES["F0_better"]
    wins = 0
    for seed in range(4):
        losses = R.sample(np.random.default_rng(seed), T)
        preds, labels = stream_from_losses(losses, np.random.default_rng(seed + 1))
        r = lambda n, s=seed: policy_rng(5, s, n)
        pol = DeployGate(make_host(kind, r), T, B, 0.05, rng=r("D_gate"), **fam_d.D6_PARAMS)
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=R.delay,
            budget=B,
            label_price=0.05,
            switch_cost=5.0,
        )
        assert res.requested_labels <= B
        wins += res.records[-1]["deployed_model"] == 1
    assert wins >= 2


def test_reserve_is_kept_until_promotion():
    pol, res = _run("D4", "F0_null", seed=3)
    if not any(r["deployed_model"] == 1 for r in res.records):
        assert res.requested_labels <= 200 - pol.reserve


def test_propensity_frozen_and_combined():
    # every granted request carries a positive issue-time propensity in (0, 1]
    _, res = _run("D6:cams", "F0_better", seed=2)
    qs = [r["query_probability"] for r in res.records if r["requested"]]
    assert qs and all(0 < q <= 1 for q in qs)


def test_promotion_requires_certificate():
    # with no evidence the gate never deploys the challenger even if the host ranks it first
    class Host:
        def predict(self, e):
            return 1

        def request_labels(self, e, rem):
            from simulator import QueryRequest

            return QueryRequest(False)

        def observe(self, fb):
            pass

    from simulator import Event

    g = DeployGate(Host(), 100, 10, 0.05, rng=np.random.default_rng(0), acq="host_only")
    for t in range(100):
        ev = Event(t, t, 100, np.array([0, 0]))
        assert g.predict(ev) == 0
        g.request_labels(ev, 10)
