"""Tests for the practical control policies.

The CUSUM and Shiryaev-Roberts controls are only exact likelihood-ratio procedures for the
simple-vs-simple Bernoulli pair they are given, so the tests check the LLR arithmetic against
hand computation rather than taking the name on trust.
"""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

SOTA = Path(__file__).resolve().parents[2] / "scripts/promising_directions/sota"
sys.path.insert(0, str(SOTA))
sys.path.insert(0, str(SOTA / "competitors"))

from controls import (
    BernoulliPairedModel,
    EconomicReplacement,
    FixedModel,
    PacedDisagreementAcquisition,
    PairedCUSUM,
    RetrospectiveOracle,
    ShiryaevRoberts,
)
from simulator import ReleasedFeedback, check_budget_feasible, run_episode


def _fb(d: int, q: float = 0.5, t: int = 0) -> ReleasedFeedback:
    """Feedback where the paired difference l0 - l1 equals `d`."""
    losses = np.array([1, 0] if d > 0 else [0, 1], dtype=np.int8)
    return ReleasedFeedback(
        event_id=t, t_requested=t, t_released=t + 1, label=0,
        model_losses=losses, query_probability=q,
    )


def _stream(T=400, seed=0, acc=(0.70, 0.80)):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, 2, T)
    p0 = np.where(rng.random(T) < acc[0], y, 1 - y)
    p1 = np.where(rng.random(T) < acc[1], y, 1 - y)
    return np.stack([p0, p1], axis=1), y


# ------------------------------------------------------------------ observation model
def test_bernoulli_model_rejects_invalid_hypotheses():
    with pytest.raises(ValueError, match="strictly inside"):
        BernoulliPairedModel(p0=0.0, p1=0.5)
    with pytest.raises(ValueError, match="p1 must exceed p0"):
        BernoulliPairedModel(p0=0.6, p1=0.6)


def test_llr_matches_hand_computation():
    m = BernoulliPairedModel(p0=0.5, p1=0.75)
    assert m.llr(+1) == pytest.approx(math.log(0.75 / 0.5))
    assert m.llr(-1) == pytest.approx(math.log(0.25 / 0.5))
    # a challenger-favouring observation must raise evidence, the reverse must lower it
    assert m.llr(+1) > 0 > m.llr(-1)


# ------------------------------------------------------------------ CUSUM
def test_cusum_is_page_recursion_and_floors_at_zero():
    m = BernoulliPairedModel(p0=0.5, p1=0.75)
    c = PairedCUSUM(100, 50, m, threshold=10.0, rng=np.random.default_rng(0))
    c.observe([_fb(-1)])
    assert c.stat == 0.0  # floored, not negative
    c.observe([_fb(+1), _fb(+1)])
    assert c.stat == pytest.approx(2 * m.llr(+1))


def test_cusum_switches_when_threshold_crossed_and_resets():
    m = BernoulliPairedModel(p0=0.5, p1=0.75)
    thr = 2.5 * m.llr(+1)
    c = PairedCUSUM(100, 50, m, threshold=thr, rng=np.random.default_rng(0))
    c.observe([_fb(+1), _fb(+1)])
    assert c.deployed == 0
    c.observe([_fb(+1)])
    assert c.deployed == 1
    assert c.stat == 0.0  # reset on switch


def test_cusum_ignores_agreement_events():
    m = BernoulliPairedModel()
    c = PairedCUSUM(100, 50, m, threshold=5.0, rng=np.random.default_rng(0))
    tie = ReleasedFeedback(
        event_id=0, t_requested=0, t_released=1, label=0,
        model_losses=np.array([1, 1], dtype=np.int8), query_probability=0.5,
    )
    c.observe([tie])
    assert c.stat == 0.0


# ------------------------------------------------------------------ Shiryaev-Roberts
def test_shiryaev_roberts_recursion_matches_hand_computation():
    m = BernoulliPairedModel(p0=0.5, p1=0.75)
    sr = ShiryaevRoberts(100, 50, m, threshold=100.0, rng=np.random.default_rng(0))
    sr.observe([_fb(+1)])
    # log R_1 = log(1 + 0) + llr = llr
    assert sr.stat == pytest.approx(m.llr(+1))
    sr.observe([_fb(+1)])
    expected = np.logaddexp(0.0, m.llr(+1)) + m.llr(+1)
    assert sr.stat == pytest.approx(expected)


def test_shiryaev_roberts_grows_faster_than_cusum_on_the_same_evidence():
    """SR accumulates 1 + R each step, so on a run of favourable evidence it leads CUSUM."""
    m = BernoulliPairedModel(p0=0.5, p1=0.75)
    hi = 10**6
    c = PairedCUSUM(100, 50, m, threshold=hi, rng=np.random.default_rng(0))
    sr = ShiryaevRoberts(100, 50, m, threshold=hi, rng=np.random.default_rng(0))
    ev = [_fb(+1) for _ in range(6)]
    c.observe(ev)
    sr.observe(ev)
    assert sr.stat > c.stat


# ------------------------------------------------------------------ economic rule
def test_economic_rule_waits_for_min_obs():
    e = EconomicReplacement(2000, 200, switch_cost=5.0, rng=np.random.default_rng(0), min_obs=10)
    e.t = 100
    e.acq.n_disagree = 50
    e.observe([_fb(+1) for _ in range(9)])
    assert e.deployed == 0  # below min_obs, no switch however favourable


def test_economic_rule_switches_only_when_payback_exceeds_switch_cost():
    # 20 observations all favouring the challenger, disagreement rate 0.5, 1900 events left
    e = EconomicReplacement(2000, 200, switch_cost=5.0, rng=np.random.default_rng(0), min_obs=10)
    e.t = 100
    e.acq.n_disagree = 50
    e.observe([_fb(+1) for _ in range(20)])
    assert e.deployed == 1
    # same evidence but almost no horizon left: payback cannot cover the switch
    e2 = EconomicReplacement(2000, 200, switch_cost=5.0, rng=np.random.default_rng(0), min_obs=10)
    e2.t = 1999
    e2.acq.n_disagree = 1000
    e2.observe([_fb(+1) for _ in range(20)])
    assert e2.deployed == 0


# ------------------------------------------------------------------ acquisition + plumbing
def test_paced_acquisition_respects_floor_and_gate():
    a = PacedDisagreementAcquisition(horizon=1000, budget=100, p_min=0.05)
    assert a.propensity(10, 100, disagree=False) == 0.0  # agreement never queried
    assert a.propensity(10, 0, disagree=True) == 0.0  # no budget, no query
    q = a.propensity(10, 100, disagree=True)
    assert 0.05 <= q <= 1.0


def test_fixed_and_oracle_never_query_and_switch_at_most_once():
    """A fixed policy buys nothing. It pays one switch iff it differs from the initial model.

    The simulator starts deployed on model 0, so deploying model 1 from t=0 is a genuine switch
    and is charged. This matches the original B3 records, where the always-challenger hindsight
    reference P1 shows exactly 1.00 switches.
    """
    preds, y = _stream()
    for pol in (FixedModel(0), FixedModel(1), RetrospectiveOracle(preds, y)):
        res = run_episode(
            pol, model_predictions=preds, labels=y, delay=5, budget=50,
            label_price=0.05, switch_cost=5.0,
        )
        assert res.requested_labels == 0
        assert res.deployment_switches == (0 if pol.index == 0 else 1)


def test_oracle_is_marked_as_an_oracle_and_picks_the_better_model():
    preds, y = _stream(acc=(0.60, 0.85))
    o = RetrospectiveOracle(preds, y)
    assert o.is_oracle is True
    assert "ORACLE" in o.name
    assert o.index == 1  # model 1 is genuinely better on this stream


@pytest.mark.parametrize("cls", [PairedCUSUM, ShiryaevRoberts])
def test_sequential_controls_respect_the_hard_budget(cls):
    preds, y = _stream(T=600, seed=3)
    pol = cls(600, 25, BernoulliPairedModel(), threshold=5.0, rng=np.random.default_rng(1))
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=5, budget=25,
        label_price=0.05, switch_cost=5.0,
    )
    assert check_budget_feasible(res, 25) == []


@pytest.mark.parametrize("cls", [PairedCUSUM, ShiryaevRoberts])
def test_sequential_controls_are_deterministic(cls):
    preds, y = _stream(T=400, seed=6)
    out = []
    for _ in range(2):
        pol = cls(400, 30, BernoulliPairedModel(), threshold=4.0, rng=np.random.default_rng(11))
        out.append(run_episode(
            pol, model_predictions=preds, labels=y, delay=3, budget=30,
            label_price=0.05, switch_cost=5.0,
        ))
    assert out[0].net_cost == out[1].net_cost
    assert out[0].requested_labels == out[1].requested_labels


def test_economic_rule_runs_end_to_end_within_budget():
    preds, y = _stream(T=500, seed=9)
    pol = EconomicReplacement(500, 40, switch_cost=5.0, rng=np.random.default_rng(2))
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=4, budget=40,
        label_price=0.05, switch_cost=5.0,
    )
    assert check_budget_feasible(res, 40) == []
    assert res.deployment_switches <= 1  # the rule only ever promotes once
