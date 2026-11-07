"""Unit tests for sprint-2 Family T (evidence-module transfer to published hosts)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import fam_d
import fam_t
from fam_t import EXTRA, CondMeanEB
from regimes import REGIMES
from simulator import policy_rng, run_episode
from suite import stream_from_losses

REP = [
    "T:mp/a5b+ad",
    "T:cams/a5b",
    "T:cams/cmean",
    "T:ms/env8",
    "T:mp/a5b+ad+rb",
    "T2:gated/a5b",
    "T2:gatedAND/a5b+front",
    "T3:discern/a5b+front",
    "T3:discernAND/env8",
    "T6:a5bxC2",
    "T6:env8xC6",
]


def _run(name, regime="F0_null", seed=0, T=2000, B=200, delay=None, extra=EXTRA):
    R = REGIMES[regime]
    losses = R.sample(np.random.default_rng(seed), T)
    preds, labels = stream_from_losses(losses, np.random.default_rng(seed + 1))
    d = R.delay if delay is None else delay
    pol = extra[name](T, B, 5.0, 0.05, 0.05, d, lambda n: policy_rng(11, seed, n))
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


def test_registry_loads_and_every_candidate_has_a_null():
    assert len(EXTRA) >= 40
    assert set(EXTRA) == set(fam_t.NULL_TESTED)
    assert fam_t.NULL_TESTED["T:cams/a5b"] == "V2"
    assert fam_t.NULL_TESTED["T:cams/qsg"] == "V1"
    assert fam_t.NULL_TESTED["T2:gatedAND/a5b"].startswith("union(")


@pytest.mark.parametrize("name", REP)
def test_budget_never_exceeded(name):
    for B in (25, 200):
        _, res = _run(name, "F9_highdis_better", T=1200, B=B, delay=20)
        assert res.requested_labels <= B
        assert res.refused_requests == 0


@pytest.mark.parametrize("name", REP)
def test_no_promotion_on_short_null(name):
    promoted = 0
    for seed in range(8):
        _, res = _run(name, "F0_null", seed=seed, T=300, B=60, delay=10)
        promoted += any(r["deployed_model"] == 1 for r in res.records)
    assert promoted == 0


def test_tgate_with_qsg_reproduces_d2_exactly():
    # the pluggable interface with the QSG module is D2 (same host, generator names, decisions)
    for seed in range(3):
        _, a = _run("T:cams/qsg", "F0_better", seed=seed, T=800, delay=20)
        _, b = _run("D2", "F0_better", seed=seed, T=800, delay=20, extra=fam_d.EXTRA)
        assert a.net_cost == b.net_cost
        assert [r["requested"] for r in a.records] == [r["requested"] for r in b.records]


def test_and_mode_promotes_no_earlier_than_either_component():
    for seed in range(4):
        _, r_and = _run("T2:gatedAND/a5b+front", "F0_better", seed=seed, T=1500, delay=20)
        _, r_rep = _run("T2:gated/a5b+front", "F0_better", seed=seed, T=1500, delay=20)
        _, r_host = _run(
            "gated_adaptive_range+front",
            "F0_better",
            seed=seed,
            T=1500,
            delay=20,
            extra=__import__("strong_hosts").EXTRA,
        )

        def first(res):
            dep = [r["deployed_model"] for r in res.records]
            return dep.index(1) if 1 in dep else 10**9

        assert first(r_and) >= max(first(r_rep), first(r_host)) or first(r_and) == 10**9


def test_adaptive_density_spaces_gate_queries_under_persistence():
    pol, _res = _run("T:cams/a5b+ad", "F5_dep_better_r8", seed=1, T=2000, delay=20)
    assert pol.rho_hat is not None and pol.rho_hat > 0
    assert pol.n_gap_skips > 0
    pol0, _ = _run("T:cams/a5b", "F5_dep_better_r8", seed=1, T=2000, delay=20)
    assert pol0.n_gap_skips == 0


def test_condmean_eb_null_and_power():
    rng = np.random.default_rng(0)
    # null p = .5: the one-sided e-process rarely crosses 1/alpha (Ville: <= alpha)
    cross = 0
    for _ in range(300):
        e = CondMeanEB(+1)
        cross += any(e.update(int(z)) >= 20 for z in rng.random(200) < 0.5)
    assert cross / 300 <= 0.06
    # alternative p = .7: grows
    e = CondMeanEB(+1)
    v = [e.update(int(z)) for z in rng.random(200) < 0.7]
    assert max(v) >= 20
    # mirror side does not grow under the alternative
    e = CondMeanEB(-1)
    assert max(e.update(int(z)) for z in rng.random(200) < 0.7) < 20


def test_condmean_eb_time_averaged_null():
    # better then worse with average conditional mean exactly 1/2: single-start test stays valid
    rng = np.random.default_rng(1)
    cross = 0
    for _ in range(200):
        e = CondMeanEB(+1)
        ps = np.r_[np.full(100, 0.4), np.full(100, 0.6)]
        cross += any(e.update(int(rng.random() < p)) >= 20 for p in ps)
    assert cross / 200 <= 0.06


def test_condmean_started_is_a_mixture_value():
    e = CondMeanEB(+1, started=True)
    for z in [1, 1, 0, 1]:
        v = e.update(z)
    assert 0 < v < 2.0  # sum_j w_j E_j with sum w_j < 1 and small E_j after 4 outcomes


def test_dep_mixin_feeds_only_queried_disagreements():
    pol, res = _run("T2:gated/a5b", "F0_null", seed=2, T=1500, delay=20)
    n_dis_lab = sum(1 for r in res.records if r["requested"])
    assert pol.dep_n <= n_dis_lab
    assert pol.dep_n > 0


def test_single_cycle_threshold_is_one_over_alpha_and_never_later():
    pol, _ = _run("T:cams/a5b1", "F0_null", seed=0, T=200, B=20, delay=5)
    assert pol.cycle == 0  # 2**0 / alpha
    for name in ("T:cams/qsg1", "T:mp/a5b1"):
        for seed in range(3):
            _, r1 = _run(name, "F0_better", seed=seed, T=1000, delay=20)
            _, r2 = _run(name.replace("1", ""), "F0_better", seed=seed, T=1000, delay=20)
            f = lambda res: next(
                (i for i, r in enumerate(res.records) if r["deployed_model"]), 10**9
            )
            assert f(r1) <= f(r2)


@pytest.mark.parametrize("name", ["T:mp/H2", "T:ms/H4", "T6:iidxshadow"])
def test_fam_h_transfers_budget_and_short_null(name):
    _, res = _run(name, "F9_highdis_better", T=1200, B=25, delay=20)
    assert res.requested_labels <= 25
    for seed in range(5):
        _, res = _run(name, "F0_null", seed=seed, T=300, B=60, delay=10)
        assert not any(r["deployed_model"] == 1 for r in res.records)
