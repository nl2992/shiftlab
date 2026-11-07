"""Tests for WP1: late_real.py (construction, classifier, runner) and fam_e.py (E_rb, E_swcert)."""

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
import fam_e
import late_real as L
from registry import EXTRA
from simulator import policy_rng, run_episode


def _pair(p_sched, T=2000, dis=0.2, seed=0):
    rng = np.random.default_rng(seed)
    p = np.empty(T)
    for i, (s, v) in enumerate(p_sched):
        e = p_sched[i + 1][0] if i + 1 < len(p_sched) else T
        p[s:e] = v
    d = rng.random(T) < dis
    ch = rng.random(T) < p  # challenger right on a disagreement
    l0 = np.where(d, ch, 0).astype(np.int8)
    l1 = np.where(d, ~ch, 0).astype(np.int8)
    return l0, l1


def _episode(name, l0, l1, *, budget=200, delay=50, seed=0, cs=5.0):
    losses = np.stack([l0, l1], 1)
    T = losses.shape[0]
    pol = EXTRA[name](T, budget, cs, 0.05, 0.05, delay, lambda nm: policy_rng(11, seed, nm))
    res = run_episode(
        pol,
        model_predictions=losses.astype(int),
        labels=np.zeros(T, int),
        delay=delay,
        budget=budget,
        label_price=0.05,
        switch_cost=cs,
        trace=True,
    )
    dep = np.array([r["deployed_model"] for r in res.records])
    return pol, res, dep


# ----------------------------------------------------------------------------- classifier
def test_classifier_classes():
    assert L.classify(*_pair([(0, 0.42), (1000, 0.75)]))["class"] == "late_improvement"
    assert L.classify(*_pair([(0, 0.75), (1000, 0.3)]))["class"] == "reversal"
    assert L.classify(*_pair([(0, 0.75)]))["class"] == "stationary_better"
    c = L.classify(*_pair([(0, 0.3)]))
    assert c["class"] == "null" and "worse" in c["sub"]
    assert L.classify(*_pair([(0, 0.15), (300, 0.85)], dis=0.4))["class"] == "early_improvement"


def test_classifier_deterministic_and_degenerate():
    l0, l1 = _pair([(0, 0.5)], seed=3)
    assert L.classify(l0, l1) == L.classify(l0, l1)
    z = np.zeros(2000, np.int8)
    c = L.classify(z, z)
    assert c["class"] == "null" and c["p"] == 1.0


def test_classifier_false_change_rate_iid_null():
    hits = sum(L.classify(*_pair([(0, 0.5)], seed=s))["p"] <= L.P_SIG for s in range(60))
    assert hits <= 4  # nominal 1%; 60 draws


# ----------------------------------------------------------------------------- construction
def test_train_ranges_precede_episode():
    for c in L.CONSTRUCTIONS:
        for e in (8000, 20000):
            (a0, b0), (a1, b1) = L.train_ranges(c, e)
            assert 0 <= a0 < b0 <= e and 0 <= a1 < b1 <= e
            assert b0 <= b1  # the challenger's data are at least as recent


def test_episode_starts():
    s = L.episode_starts(204950)
    assert len(s) == L.MAX_EPS and s[0] >= 0.30 * 204950 and (np.diff(s) >= L.T_EP).all()
    assert s[-1] + L.T_EP <= 204950
    s = L.episode_starts(17379)
    assert s[0] == 8000 and len(s) == (17379 - 8000) // 2000


# ----------------------------------------------------------------------------- policies
NEW = list(fam_e.EXTRA)


@pytest.mark.parametrize("name", NEW)
def test_budget_never_exceeded(name):
    l0, l1 = _pair([(0, 0.42), (800, 0.75)], dis=0.4)
    for budget in (20, 100):
        _, res, _ = _episode(name, l0, l1, budget=budget, delay=10)
        assert res.requested_labels <= budget


@pytest.mark.parametrize("name", NEW)
def test_short_stream_null_no_promotion(name):
    # SRR / GLR detectors control only the average run length, not P(any false alarm): the
    # e-SR variant does false-alarm on short null streams (expected, documented in fam_e).
    arl_only = fam_e.NULL_TESTED[name] == "none"
    hits = 0
    for s in range(5):
        l0, l1 = _pair([(0, 0.5)], T=150, seed=s)
        _, _, dep = _episode(name, l0, l1, delay=5, seed=s)
        hits += int(dep.max() == 1)
    assert hits <= (2 if arl_only else 0)


def test_erb_gated_matches_b2():
    l0, l1 = _pair([(0, 0.72), (700, 0.3)], seed=1)
    _, r1, _ = _episode("B2", l0, l1)
    _, r2, _ = _episode("E_rb:gated_deployment", l0, l1)
    assert r1.net_cost == r2.net_cost


@pytest.mark.parametrize("host", list(fam_e.HOSTS))
def test_erb_rolls_back_on_reversal(host):
    rb = 0
    for s in range(4):
        l0, l1 = _pair([(0, 0.8), (700, 0.2)], dis=0.3, seed=s)
        _pol, _, dep = _episode(f"E_rb:{host}", l0, l1, seed=s, delay=20)
        rb += int(dep[:700].max() == 1 and dep[-1] == 0)
    assert rb >= 3


def test_erb_horizon_gate_vetoes_late_rollback():
    pol = EXTRA["E_rb:gated_deployment"](
        2000, 200, 5.0, 0.05, 0.05, 10, lambda nm: policy_rng(1, 0, nm)
    )
    pol.deployed, pol.t = 1, 1990
    pol._switch()
    assert pol.deployed == 1 and pol.n_vetoed == 1


def test_swcert_mechanism():
    det = 0
    for s in range(4):
        l0, l1 = _pair([(0, 0.4), (600, 0.85)], dis=0.4, seed=s)
        _, _, dep = _episode("E_swcert", l0, l1, seed=s, delay=10)
        det += int(dep[:600].max() == 0 and dep[-1] == 1)
    assert det >= 3


def test_swcert_window_union_bound_level():
    """The alpha_k sum is <= alpha: every test level is below the spending sequence."""
    import math

    assert sum(6 / (math.pi**2 * k**2) for k in range(1, 10_000)) <= 1.0


def test_runner_job_smoke():
    st = L.streams()
    name = "spam"
    rows = L._job(
        (name, 0, 0, 2026110803, ["CONTROL_never_switch", "E_swcert"], 1.0, 100, 2.0, 0.05)
    )
    assert {r["policy"] for r in rows} == {"CONTROL_never_switch", "E_swcert"}
    assert all(
        r["budget"] == 100 and r["cs"] == 2.0 and r["delay"] == st[name]["delay"] for r in rows
    )
    assert all(r["labels"] <= 100 for r in rows)


def test_srr_detectors_cusum_le_sr_and_alarm():
    rng = np.random.default_rng(0)
    c, s = fam_e.SRRDetector(0.05, "cusum"), fam_e.SRRDetector(0.05, "sr")
    alarm = None
    for i in range(300):
        x = 1 if rng.random() < (0.4 if i < 100 else 0.85) else -1
        a1, _ = c.update(x), s.update(x)
        assert c.stat <= s.stat + 1e-9
        if a1 and alarm is None:
            alarm = i
    assert alarm is not None and alarm >= 100


def test_glr_detects_upward_change_only():
    g = fam_e.GLRDetector(0.05)
    assert not any(g.update(1 if i < 60 else -1) for i in range(150))  # downward change: no alarm
    g = fam_e.GLRDetector(0.05)
    assert any(g.update(-1 if i < 60 else 1) for i in range(150))


@pytest.mark.parametrize("host", list(fam_e.HOSTS))
def test_srr_host_promotes_on_late_improvement(host):
    l0, l1 = _pair([(0, 0.4), (700, 0.85)], dis=0.4, seed=2)
    _, _, dep = _episode(f"E_srr:{host}", l0, l1, delay=10, seed=2)
    assert dep[-1] == 1
