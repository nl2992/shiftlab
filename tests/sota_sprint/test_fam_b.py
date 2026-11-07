"""Unit tests for SOTA sprint family B (scripts/sota_sprint/fam_b.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "scripts/failure_atlas_v2_flq", ROOT / "scripts/sota_sprint"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import bench  # noqa: F401  (pins FLQ regimes before the RMM path)
import fam_b
from registry import EXTRA
from simulator import policy_rng, run_episode

B_NAMES = [k for k in fam_b.EXTRA]


def _episode(name, losses, *, budget=200, delay=100, seed=0, cs=5.0):
    T = losses.shape[0]
    pol = EXTRA[name](T, budget, cs, 0.05, 0.05, delay, lambda nm: policy_rng(11, seed, nm))
    labels = np.zeros(T, dtype=int)
    preds = losses.astype(int)  # prediction = label XOR loss with label 0
    res = run_episode(
        pol,
        model_predictions=preds,
        labels=labels,
        delay=delay,
        budget=budget,
        label_price=0.05,
        switch_cost=cs,
        trace=True,
    )
    return pol, res


def _stream(p_sched, T, dis=0.2, seed=0):
    rng = np.random.default_rng(seed)
    p = np.empty(T)
    for i, (s, v) in enumerate(p_sched):
        e = p_sched[i + 1][0] if i + 1 < len(p_sched) else T
        p[s:e] = v
    on = rng.random(T) < dis
    sign = rng.random(T) < p
    both = rng.random(T) < 0.1
    l0 = np.where(on, sign, both)
    l1 = np.where(on, ~sign, both)
    return np.stack([l0, l1], 1).astype(np.int8)


@pytest.mark.parametrize("name", B_NAMES)
def test_budget_respected_and_never_refused(name):
    losses = _stream([(0, 0.7), (600, 0.3)], 1500, dis=0.5, seed=3)
    _, res = _episode(name, losses, budget=60, delay=20)
    assert res.requested_labels <= 60
    assert res.refused_requests == 0
    assert all(r["budget_remaining"] >= 0 for r in res.records)


def test_b0_reproduces_host_exactly():
    for seed in range(3):
        losses = _stream([(0, 0.4), (500, 0.75)], 1500, seed=seed)
        _, a = _episode("B0_host", losses, seed=seed)
        _, b = _episode("rmm:gated_deployment+RMM", losses, seed=seed)
        assert a.net_cost == b.net_cost
        assert [r["deployed_model"] for r in a.records] == [r["deployed_model"] for r in b.records]


def test_grid_detector_matches_host_detector_and_bound():
    rng = np.random.default_rng(0)
    xs = rng.choice([-1, 1], 150)
    host = fam_b._rmm.MixtureSRDetector(0.025, 200, 10)
    mine = fam_b.host_detector(0.025, 200, 10)
    for x in xs:
        host.update(int(x))
        mine.update(int(x))
        assert mine.stat == pytest.approx(host.stat, rel=1e-12)
    ms = fam_b.multiscale_detector(0.05, 200)
    for x in xs[:40]:
        ms.update(int(x))
    bound = ms.max_reachable(15)
    for _ in range(15):
        ms.update(1)
    assert ms.stat <= bound * (1 + 1e-12)


@pytest.mark.parametrize("name", ["B2", "B3", "B5", "B6"])
def test_null_promotion_small_on_short_streams(name):
    n, prom = 120, 0
    for s in range(n):
        losses = _stream([(0, 0.5)], 600, dis=0.3, seed=1000 + s)
        _, res = _episode(name, losses, budget=100, delay=10, seed=s)
        prom += any(r["deployed_model"] == 1 for r in res.records)
    # nominal .05; generous screening tolerance (binomial 99.9% upper point at n=120 is ~.12)
    assert prom / n <= 0.12


def test_rollback_fires_on_planted_reversal():
    T = 1500
    l0 = np.zeros(T, np.int8)
    l1 = np.zeros(T, np.int8)
    dis = np.arange(T) % 2 == 0  # every other event is a disagreement
    l0[dis & (np.arange(T) < 400)] = 1  # challenger right before 400
    l1[dis & (np.arange(T) >= 400)] = 1  # challenger wrong from 400 on
    losses = np.stack([l0, l1], 1)
    for name in ("B2", "B5", "B6"):
        _pol, res = _episode(name, losses, budget=200, delay=10)
        dep = np.array([r["deployed_model"] for r in res.records])
        assert dep[:400].max() == 1, name  # promoted during the advantage
        t1 = int(np.argmax(dep == 1))
        back = np.flatnonzero((dep[1:] == 0) & (dep[:-1] == 1)) + 1
        assert len(back) and back[0] > t1 and back[0] < 900, name
        assert dep[-1] == 0, name


def test_rollback_vetoed_when_too_late():
    pol = EXTRA["B2"](2000, 200, 5.0, 0.05, 0.05, 100, lambda nm: policy_rng(1, 0, nm))
    pol.deployed, pol.t = 1, 2000 - pol.h_min  # fewer than h_min events left
    pol._switch()
    assert pol.deployed == 1 and pol.n_vetoed == 1


def test_deadline_stops_acquisition():
    losses = _stream([(0, 0.5)], 2000, dis=0.5, seed=5)
    pol, res = _episode("B4", losses, budget=400, delay=100)
    req_t = [r["event_id"] for r in res.records if r["requested"]]
    assert req_t and max(req_t) < pol.t_dead


def test_reserve_held_before_decision():
    losses = _stream([(0, 0.5)], 2000, dis=0.5, seed=6)
    pol, res = _episode("B1_r25", losses, budget=200, delay=100)
    if not pol.decided:
        assert res.requested_labels <= 150
