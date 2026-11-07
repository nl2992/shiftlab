"""Unit tests for sprint-2 Family H (A5b x D2 hybrids)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import fam_d
import fam_h
import registry  # noqa: F401  (pins module paths as the runner does)
from simulator import policy_rng, run_episode
from suite import stream_from_losses

CANDS = ["H1", "H2", "H2-iid_space", "H2-gateonly", "H3", "H4", "H5", "H5-dc", "H6-r10", "H6-r25"]


def _losses(regime, seed, T):
    import bench

    R = bench.SPRINT_REGIMES[regime]
    return R, R.sample(np.random.default_rng(seed), T)


def _run(name, regime="F0_null", seed=0, T=2000, B=200, delay=None, losses=None, extra=None):
    R, L = _losses(regime, seed, T)
    if losses is not None:
        L = losses
    preds, labels = stream_from_losses(L, np.random.default_rng(seed + 1))
    d = R.delay if delay is None else delay
    pol = (extra or fam_h.EXTRA)[name](T, B, 5.0, 0.05, 0.05, d, lambda n: policy_rng(11, seed, n))
    pol.trace = getattr(pol, "trace", False) or hasattr(pol, "tr")
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


@pytest.mark.parametrize("name", CANDS)
@pytest.mark.parametrize("regime", ["F9_highdis_better", "F0_null"])
def test_budget_respected(name, regime):
    for B in (30, 200):
        _, res = _run(name, regime, B=B)
        assert res.requested_labels <= B
        assert res.refused_requests == 0


@pytest.mark.parametrize("name", ["Hchk:D2", "Hchk:D5"])
def test_exact_reimplementation_of_d2_d5(name):
    ref = name.split(":")[1]
    for regime, seed in (("F0_better", 0), ("F5_dep_better_r8", 1), ("F3_reversal_800", 2)):
        _, a = _run(name, regime, seed)
        _, b = _run(ref, regime, seed, extra=fam_d.EXTRA)
        assert a.net_cost == b.net_cost
        assert [r["deployed_model"] for r in a.records] == [r["deployed_model"] for r in b.records]


@pytest.mark.parametrize("name", ["H1", "H2", "H3", "H4", "H5", "H6-r25"])
@pytest.mark.parametrize("regime", ["F0_null", "F5_dep_null_r8", "F5_dep_null_r95"])
def test_short_stream_null_no_promotion(name, regime):
    for seed in range(4):
        for T in (60, 300):
            _, res = _run(name, regime, seed, T=T, B=min(200, T // 2), delay=20)
            assert res.requested_labels <= min(200, T // 2)
            assert all(r["deployed_model"] == 0 for r in res.records)


def test_threshold_single_cycle_vs_rollback():
    p1, _ = _run("H1", T=50, B=10, delay=5)
    assert math.isclose(p1._thr_up(), 1.0 / 0.05)
    p5, _ = _run("H5", T=50, B=10, delay=5)
    assert math.isclose(p5._thr_up(), 2.0 / 0.05)
    p5.cycle = 3
    assert math.isclose(p5._thr_up(), 8.0 / 0.05)


def test_sui_evidence_is_a5b_kwargs():
    p, _ = _run("H1", T=50, B=10, delay=5)
    m = p.e_up.m
    assert m.w_first == fam_h.fam_a._B["w_first"]


def test_spacing_gap_rule():
    p, _ = _run("H2", T=50, B=10, delay=5)
    p.rho_hat = 0.8
    assert p._gmin() == math.ceil(math.log(0.25) / math.log(0.8))
    p.rho_hat = 0.0
    assert p._gmin() == 0


def test_spacing_enforced_on_dependent_stream():
    pol, _ = _run("H2", "F5_dep_better_r8", seed=3)
    assert pol.n_veto["spacing"] > 0
    # once rho_hat is set, pre-certificate queries respect the gap (gmin is recomputed only at
    # releases, so check gaps >= 1 + a lower bound from the final estimate is too strict; instead
    # check that no two open-test queries share an event and that spacing vetoes happened)
    t = [r[0] for r in pol.tr["req"]]
    assert len(t) == len(set(t))


def test_spacing_gap_holds_while_open():
    """Every open-test query issued while gmin>0 is at least gmin events after the previous one."""
    _R, L = _losses("F5_dep_better_r8", 5, 2000)
    preds, labels = stream_from_losses(L, np.random.default_rng(6))
    pol = fam_h.EXTRA["H2"](2000, 200, 5.0, 0.05, 0.05, 100, lambda n: policy_rng(11, 5, n))
    pol.trace = True
    gaps_ok = []
    orig = pol.request_labels

    def wrapped(event, rem):
        g, last, open_ = pol._gmin(), pol.last_issue, pol.deployed == 0 and not pol.cert_ok
        req = orig(event, rem)
        if req.requested and open_ and g > 0:
            gaps_ok.append(event.t - last >= g)
        return req

    pol.request_labels = wrapped
    run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=100,
        budget=200,
        label_price=0.05,
        switch_cost=5.0,
        trace=False,
    )
    assert gaps_ok and all(gaps_ok)


def test_shadow_price_refuses_when_challenger_looks_worse():
    p = fam_h.EXTRA["H3"](2000, 200, 5.0, 0.05, 0.05, 100, lambda n: policy_rng(11, 0, n))
    p.pacer.n_disagree = 20
    p.seg_k, p.seg_hits = 40, 10
    assert not p._shadow_ok(500, 150)
    p.seg_k, p.seg_hits = 40, 32
    assert p._shadow_ok(100, 190)


def test_dualclock_never_requests_unreleasable_labels():
    pol, res = _run("H4", "F0_better", seed=0, delay=800)
    assert all(r[0] + 800 < 2000 for r in pol.tr["req"])
    _, base = _run("H2", "F0_better", seed=0, delay=800)
    assert res.requested_labels <= base.requested_labels


def test_reserve_withheld_before_promotion():
    pol, _ = _run("H6-r25", "F0_null", seed=1)
    pre = [r for r in pol.tr["req"] if r[2] == 0]
    assert len(pre) <= 200 - 50


def test_rollback_increments_cycle_on_reversal():
    cycles = []
    for s in range(6):
        pol, res = _run("H5", "F3_reversal_800", seed=s)
        dep = [r["deployed_model"] for r in res.records]
        cycles.append(pol.cycle)
        if pol.cycle > 1:
            assert 1 in dep and dep[-1] in (0, 1)
    assert max(cycles) >= 2  # at least one rollback on a strong reversal


def test_query_decisions_are_predictable():
    """Changing labels released after t0 cannot change any query decision issued before t0."""
    _R, L = _losses("F0_better", 7, 2000)
    L2 = L.copy()
    t0 = 900
    L2[t0:] = L2[t0:, ::-1]  # flip the sign of every outcome from t0 on
    for name in ("H2", "H3", "H4", "H5"):
        p1, _ = _run(name, "F0_better", 7, losses=L)
        p2, _ = _run(name, "F0_better", 7, losses=L2)
        a = [r for r in p1.tr["req"] if r[0] < t0]
        b = [r for r in p2.tr["req"] if r[0] < t0]
        assert a == b, name
