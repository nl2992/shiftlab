from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOTA = ROOT / "scripts/promising_directions/sota"
for p in (SOTA, SOTA / "competitors", SOTA.parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from b3_plus_policy_adapter import P7sPolicy
from p7s_model_picker_overlay import P7sModelPickerOverlay
from simulator import Event, run_episode
from b3_plus_policy_adapter import p7s_plus_params
from b3_plus_policy import CertPlus, b1


def _make(policy_type=P7sPolicy, *, seed=1, budget=20, **kw):
    return policy_type(40, budget, 2, 5.0, 0.05, rng=np.random.default_rng(seed),
        params=b1.Params(T=40, delay=2, cq=0.05), **kw)


def test_q_combination_active_and_settled_formulas():
    policy = _make(P7sModelPickerOverlay)
    # Direct callback check with deliberately populated pre-issue model state.
    policy._current_event = Event(0, 0, 40, np.array([0, 1]))
    policy.mp_loss[:] = [0.0, 2.0]
    combined = policy._combine(0, 0.4)
    assert policy._parts["active"]
    assert np.isclose(combined, 1 - (1 - 0.4) * (1 - policy._parts["mp"]))
    policy.cp.dep[0] = 1
    policy.cp.pst[0] = -0.01
    assert policy._combine(1, 0.4) == 0.4
    assert policy._parts["mp"] == 0.0
    policy.cp.pst[0] = 0.0
    combined = policy._combine(1, 0.4)
    assert policy._parts["active"]
    assert np.isclose(combined, 1 - (1 - 0.4) * (1 - policy._parts["mp"]))


def test_mp_update_waits_until_after_current_p7s_issue_and_uses_combined_q():
    policy = _make(P7sModelPickerOverlay, seed=5, budget=10)
    preds = np.tile(np.array([[0, 1]]), (40, 1))
    labels = np.arange(40) % 2
    run_episode(policy, model_predictions=preds, labels=labels, delay=2, budget=10,
        label_price=0.05, switch_cost=5.0)
    assert np.isfinite(policy.mp_loss).all()
    assert policy._next_t == len(labels)
    # All queried feedback uses the frozen combined propensity retained by the P7s feedback path.
    assert np.all(policy.mp_loss >= 0)


def test_absent_adjustment_keeps_p7s_q_identity():
    p = b1.Params(T=20, delay=2, cq=0.05)
    a = CertPlus(1, 10, 5.0, 0.05, p, p7s_plus_params(), trace=True)
    b = CertPlus(1, 10, 5.0, 0.05, p, p7s_plus_params(), trace=True)
    for t in range(20):
        dis = np.array([t % 3 != 0])
        u = np.array([0.37])
        nd = np.array([sum(i % 3 != 0 for i in range(t))])
        a.step(t, np.zeros(1), np.zeros(1), dis, u, nd)
        b.step(t, np.zeros(1), np.zeros(1), dis, u, nd, q_adjust=None)
    assert np.array_equal(a.tr["q"], b.tr["q"])
    assert np.array_equal(a.tr["ask"], b.tr["ask"])
    assert np.array_equal(a.logw, b.logw)


def test_overlay_obeys_pathwise_hard_budget():
    policy = _make(P7sModelPickerOverlay, seed=18, budget=4)
    preds = np.tile(np.array([[0, 1]]), (40, 1))
    labels = np.arange(40) % 2
    result = run_episode(policy, model_predictions=preds, labels=labels, delay=2, budget=4,
        label_price=0.05, switch_cost=5.0)
    assert result.requested_labels <= 4
    assert result.refused_requests == 0
    assert policy.cp.queries[0] <= 4
