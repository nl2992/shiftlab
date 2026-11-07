"""Failure Atlas v2: QCE correction and regime generator checks (CPU-sized)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/failure_atlas_v2_flq"))

from qce import SMCSQCE, DiscernQCE, GatedQCE, XuQCE
from regimes import REGIMES, expected_oracle_path, hindsight_oracle_cost
from simulator import check_budget_feasible, run_episode


def _stream(p, T=600, dis=0.3, seed=0):
    rng = np.random.default_rng(seed)
    on = rng.random(T) < dis
    chal = rng.random(T) < p
    labels = np.zeros(T, dtype=int)
    # with label 0, prediction == loss; challenger correct => l0 = 1, l1 = 0
    preds = np.stack([np.where(on, chal, 0), np.where(on, ~chal, 0)], 1).astype(int)
    return preds, labels


def test_regime_gain_matches_truth():
    R = REGIMES["F1_late_800"]
    L = np.stack([R.sample(np.random.default_rng(s)) for s in range(40)])
    d = (L[:, :, 0].astype(int) - L[:, :, 1]).mean(0)
    g = R.truth_gain()
    assert abs(d[:800].mean() - g[:800].mean()) < 0.01
    assert abs(d[800:].mean() - g[800:].mean()) < 0.01


def test_oracles_are_bounds():
    R = REGIMES["F0_better"]
    L = R.sample(np.random.default_rng(1))
    oc = hindsight_oracle_cost(L, 5.0)
    assert oc <= min(L[:, 0].sum(), L[:, 1].sum() + 5.0) + 1e-9
    path = expected_oracle_path(R.truth_gain(), 5.0)
    assert path[0] == 1 and (path == 1).all()


@pytest.mark.parametrize("cls", [GatedQCE, DiscernQCE])
def test_qce_ingests_only_queried_with_unit_weight(cls):
    preds, labels = _stream(0.8)
    pol = cls(600, 60, 0.05, rng=np.random.default_rng(0))
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=5,
        budget=60,
        label_price=0.05,
        switch_cost=5,
        trace=False,
    )
    assert not check_budget_feasible(res, 60)
    assert pol.n_ingested <= res.requested_labels
    assert all(r.w == 1.0 for r in pol._queue)
    assert pol.verdict == "deploy" or pol.verdict == "safe"


def test_qce_null_false_promotion_small():
    fp = 0
    for s in range(60):
        preds, labels = _stream(0.5, T=800, seed=100 + s)
        pol = GatedQCE(800, 200, 0.05, rng=np.random.default_rng(s), front=True)
        run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=3,
            budget=200,
            label_price=0.05,
            switch_cost=5,
            trace=False,
        )
        fp += int(pol.deployed == 1)
    assert fp / 60 <= 0.1  # nominal .05; loose bound for 60 reps


def test_smcs_and_xu_qce_run_and_keep_wealth_positive():
    preds, labels = _stream(0.75, T=800)
    for pol in (SMCSQCE(2, np.random.default_rng(0)), XuQCE(np.random.default_rng(0), delay=4)):
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=4,
            budget=150,
            label_price=0.05,
            switch_cost=5,
            trace=False,
        )
        assert res.requested_labels <= 150
    assert pol.min_factor > 0


def test_strong_hosts_and_qsg_null_and_power():
    from qsg import QSG, QSGEnvelope
    from strong_hosts import DiscernDesignFloor, GatedAdaptiveRange

    makers = [
        lambda s: GatedAdaptiveRange(800, 120, 0.05, rng=np.random.default_rng(s)),
        lambda s: DiscernDesignFloor(800, 120, 0.05, rng=np.random.default_rng(s)),
        lambda s: QSG(800, 120, 0.05, rng=np.random.default_rng(s)),
        lambda s: QSGEnvelope(800, 120, 0.05, rng=np.random.default_rng(s)),
    ]
    for mk in makers:
        fp = 0
        for s in range(30):
            preds, labels = _stream(0.5, T=800, seed=500 + s)
            pol = mk(s)
            res = run_episode(
                pol,
                model_predictions=preds,
                labels=labels,
                delay=3,
                budget=120,
                label_price=0.05,
                switch_cost=5,
                trace=False,
            )
            assert res.requested_labels <= 120
            fp += int(res.deployment_switches > 0)
        assert fp <= 4  # nominal .05 over 30 reps; loose
    preds, labels = _stream(0.85, T=800, seed=7)
    pol = QSG(800, 200, 0.05, rng=np.random.default_rng(0))
    run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=3,
        budget=200,
        label_price=0.05,
        switch_cost=5,
        trace=False,
    )
    assert pol.deployed == 1
