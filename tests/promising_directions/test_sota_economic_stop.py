"""Tests for the economic stopping trigger.

The claim under test is that the *only* difference from gated deployment is the threshold. These
tests pin that: same acquisition, same confidence sequence, and identical behaviour whenever the
threshold is zero.
"""

import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest

SOTA = Path(__file__).resolve().parents[2] / "scripts/promising_directions/sota"
sys.path.insert(0, str(SOTA))
sys.path.insert(0, str(SOTA / "competitors"))

from certificate_stops import GatedDeploymentStop
from economic_stop import EconomicStop
from simulator import check_budget_feasible, run_episode


def _stream(T=2000, seed=0, acc=(0.70, 0.85)):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, T)
    p0 = np.where(rng.random(T) < acc[0], y, 1 - y)
    p1 = np.where(rng.random(T) < acc[1], y, 1 - y)
    return np.stack([p0, p1], axis=1), y


def test_threshold_is_switch_cost_over_remaining_horizon():
    p = EconomicStop(1000, 100, 0.05, switch_cost=5.0, rng=np.random.default_rng(0))
    p._t = 0
    assert p.threshold == pytest.approx(5.0 / 1000)
    p._t = 500
    assert p.threshold == pytest.approx(5.0 / 500)
    p._t = 999
    assert p.threshold == pytest.approx(5.0)


def test_threshold_rises_monotonically_as_the_horizon_runs_out():
    p = EconomicStop(1000, 100, 0.05, switch_cost=5.0, rng=np.random.default_rng(0))
    vals = []
    for t in range(0, 1000, 50):
        p._t = t
        vals.append(p.threshold)
    assert all(b >= a for a, b in pairwise(vals))


def test_threshold_never_divides_by_zero_at_the_last_event():
    p = EconomicStop(100, 10, 0.05, switch_cost=5.0, rng=np.random.default_rng(0))
    p._t = 100  # past the end
    assert np.isfinite(p.threshold)


def test_zero_switch_cost_reduces_exactly_to_gated_deployment():
    """With c_s = 0 the threshold is 0, so the two policies must agree event for event."""
    preds, y = _stream(seed=4)
    a = run_episode(
        EconomicStop(2000, 200, 0.05, switch_cost=0.0, rng=np.random.default_rng(3)),
        model_predictions=preds,
        labels=y,
        delay=50,
        budget=200,
        label_price=0.05,
        switch_cost=0.0,
        trace=False,
    )
    b = run_episode(
        GatedDeploymentStop(2000, 200, 0.05, rng=np.random.default_rng(3)),
        model_predictions=preds,
        labels=y,
        delay=50,
        budget=200,
        label_price=0.05,
        switch_cost=0.0,
        trace=False,
    )
    assert a.net_cost == pytest.approx(b.net_cost)
    assert a.requested_labels == b.requested_labels
    assert a.deployment_switches == b.deployment_switches
    assert a.prediction_loss == pytest.approx(b.prediction_loss)


def test_a_positive_switch_cost_makes_promotion_strictly_harder():
    """Raising c_s can only raise the deploy bar, so it never promotes more often."""
    preds, y = _stream(seed=11, acc=(0.70, 0.76))
    switches = []
    for cs in (0.0, 5.0, 50.0):
        res = run_episode(
            EconomicStop(2000, 200, 0.05, switch_cost=cs, rng=np.random.default_rng(5)),
            model_predictions=preds,
            labels=y,
            delay=50,
            budget=200,
            label_price=0.05,
            switch_cost=cs,
            trace=False,
        )
        switches.append(res.deployment_switches)
    assert switches[0] >= switches[1] >= switches[2]


def test_rejects_negative_switch_cost():
    with pytest.raises(ValueError, match="switch_cost must be >= 0"):
        EconomicStop(100, 10, 0.05, switch_cost=-1.0, rng=np.random.default_rng(0))


def test_budget_holds_pathwise():
    preds, y = _stream(seed=7)
    res = run_episode(
        EconomicStop(2000, 40, 0.05, switch_cost=5.0, rng=np.random.default_rng(2)),
        model_predictions=preds,
        labels=y,
        delay=100,
        budget=40,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert check_budget_feasible(res, 40) == []


def test_determinism():
    preds, y = _stream(seed=8)
    out = [
        run_episode(
            EconomicStop(2000, 100, 0.05, switch_cost=5.0, rng=np.random.default_rng(13)),
            model_predictions=preds,
            labels=y,
            delay=50,
            budget=100,
            label_price=0.05,
            switch_cost=5.0,
            trace=False,
        ).net_cost
        for _ in range(2)
    ]
    assert out[0] == out[1]


def test_state_round_trip():
    p = EconomicStop(2000, 100, 0.05, switch_cost=5.0, rng=np.random.default_rng(1))
    p._t = 321
    q = EconomicStop(2000, 100, 0.05, switch_cost=5.0, rng=np.random.default_rng(1))
    q.load_state_dict(p.state_dict())
    assert q._t == 321
    assert q.threshold == pytest.approx(p.threshold)
