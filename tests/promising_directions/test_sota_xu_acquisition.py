"""Tests for the Xu et al. acquisition component adapter."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))

from competitors.xu_acquisition import (
    PairedDiffPredictor,
    XuAcquisitionPolicy,
    bet_cap,
    rate_from_score,
    residual_score,
    solve_normaliser,
)
from simulator import (
    Event,
    ReleasedFeedback,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)

DELAY = 3


def _stream(T=600, seed=0, d=3):
    """Binary labels, two models. On disagreement exactly one is right and the challenger is the
    right one with probability sigmoid(2.5 x0), so the sign of D is predictable from context."""
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(T, d))
    y = rng.integers(0, 2, T)
    disagree = rng.random(T) < 0.5
    chal_right = rng.random(T) < 1 / (1 + np.exp(-2.5 * x[:, 0]))
    chal = np.where(disagree, np.where(chal_right, y, 1 - y), y)
    inc = np.where(disagree, 1 - chal, chal)
    return np.stack([inc, chal], 1), y, x


def _d(preds, y):
    return (preds[:, 0] != y).astype(int) - (preds[:, 1] != y).astype(int)


def _nuisance(seed=1):
    preds, y, x = _stream(T=800, seed=seed)
    return PairedDiffPredictor().fit(x, _d(preds, y), data_end=800, locked_start=800)


def _policy(variant="acquisition_only", seed=0, **kw):
    nuis = _nuisance() if variant == "prediction_assisted" else None
    return XuAcquisitionPolicy(
        variant, policy_rng(seed, 0, f"xu_{variant}"), delay=DELAY, nuisance=nuis, **kw
    )


def _run(variant, budget=60, seed=0, **kw):
    preds, y, x = _stream(seed=seed)
    pol = _policy(variant, seed=seed, **kw)
    res = run_episode(
        pol, model_predictions=preds, labels=y, contexts=x, delay=DELAY, budget=budget,
        label_price=0.1, switch_cost=1.0,
    )  # fmt: skip
    return pol, res


# ---------------------------------------------------------------- hand-computed acquisition
def test_hand_computed_score_and_rate():
    # mu_hat = 0.6 -> sqrt(1 - 0.36) = 0.8 ; c = 1.6 -> Q = 0.5 ; floor and cap respected
    assert residual_score(0.6) == pytest.approx(0.8)
    assert rate_from_score(0.8, 1.6, 0.05) == pytest.approx(0.5)
    assert rate_from_score(0.8, 0.5, 0.05) == 1.0
    assert rate_from_score(0.0, 1.6, 0.05) == 0.05
    # window [0.8, 0.8, 0, 0], target 0.25: mean rate = 2*(0.8/c)/4 = 0.25 -> c = 1.6
    assert solve_normaliser(np.array([0.8, 0.8, 0.0, 0.0]), 0.25, 0.05) == pytest.approx(1.6)
    # window [0.8, 0.4], target 0.3: (0.8 + 0.4)/c/2 = 0.3 -> c = 2.0
    assert solve_normaliser(np.array([0.8, 0.4]), 0.3, 0.01) == pytest.approx(2.0)


def test_bet_cap_matches_plain_and_hand_case():
    assert bet_cap(0.2, 0.0, 1.0, False) == pytest.approx(0.1)  # q/2, as b3_plus_policy
    # cv, q=0.5, mu=0.6, sgn=+1: lo = 0.6 - 1.6/0.5 = -2.6 ; cap = 1/(2*2.6)
    assert bet_cap(0.5, 0.6, 1.0, True) == pytest.approx(1 / 5.2)
    # sgn=-1: y_min = -(0.6 + 0.4/0.5) = -1.4 ; cap = 1/2.8
    assert bet_cap(0.5, 0.6, -1.0, True) == pytest.approx(1 / 2.8)


def test_floor_infeasible_means_everything_at_floor():
    assert math.isinf(solve_normaliser(np.ones(10), 0.01, 0.05))


# ---------------------------------------------------------------- propensity bounds
@pytest.mark.parametrize("variant", ["acquisition_only", "prediction_assisted"])
def test_propensity_floor_and_importance_weights_bounded(variant):
    q_min = 0.07
    pol, res = _run(variant, q_min=q_min)
    qs = [r["query_probability"] for r in res.records if r["requested"]]
    assert qs and min(qs) >= q_min - 1e-12 and max(qs) <= 1.0
    assert pol.min_q >= q_min - 1e-12
    assert 1.0 / pol.min_q <= 1.0 / q_min + 1e-9  # importance-weight bound
    assert pol.n_asked > 0


# ---------------------------------------------------------------- wealth nonnegativity
@pytest.mark.parametrize("variant", ["acquisition_only", "prediction_assisted"])
def test_wealth_factors_positive_on_adversarial_streams(variant):
    rng = np.random.default_rng(3)
    n = 400
    streams = {
        "all_plus": np.ones(n), "all_minus": -np.ones(n), "alternating": (-1.0) ** np.arange(n),
        "random": rng.choice([-1.0, 1.0], n),
    }  # fmt: skip
    for name, ds in streams.items():
        pol = _policy(variant)
        for i, d in enumerate(ds):
            q = 0.05  # worst case: smallest allowed propensity
            mu = (-0.95 if d > 0 else 0.95) if pol.cv else 0.0  # predictor maximally wrong
            # greedy bet: the largest the cap allows, both outcomes of the Bernoulli draw
            lam = bet_cap(q, mu, 1.0 if pol.dep == 0 else -1.0, pol.cv)
            for asked in (1, 0):
                pol._apply(i, i + DELAY, q, lam, mu, d, asked)
        assert pol.min_factor >= 0.5 - 1e-9, (name, pol.min_factor)
        assert np.isfinite(pol.logw)


# ---------------------------------------------------------------- no update before release
def test_no_update_before_release():
    preds, y, x = _stream()
    pol = _policy("acquisition_only", target_rate=0.5)
    res = run_episode(
        pol, model_predictions=preds, labels=y, contexts=x, delay=DELAY, budget=200,
        label_price=0.1, switch_cost=1.0,
    )  # fmt: skip
    assert not check_no_future_access(res, DELAY)
    # requesting a label changes no evidence state until feedback is released
    pol2 = _policy("acquisition_only", target_rate=0.9)
    ev = Event(0, 0, 600, np.array([0, 1]), x[0])
    pol2.predict(ev)
    pol2.request_labels(ev, 10)
    assert pol2.cnt == 0 and pol2.logw == 0.0 and pol2.s1 == 0.0


# ---------------------------------------------------------------- issue-time propensity used
def test_issue_time_propensity_used_in_weighting():
    pol = _policy("acquisition_only")
    losses = np.array([1, 0], dtype=np.int8)
    extra = {"lam": 0.1, "mu_hat": 0.0, "dep": 0}
    pol.observe([ReleasedFeedback(0, 0, DELAY, 1, losses, 0.25, extra)])
    assert pol.logw == pytest.approx(math.log(1.4))  # D=1, x=D/0.25=4, factor 1+0.1*4
    pol.observe([ReleasedFeedback(1, 1, DELAY + 1, 1, losses, 0.5, extra)])
    assert pol.logw == pytest.approx(math.log(1.4) + math.log(1.2))  # x=2
    with pytest.raises(ValueError):
        pol.observe([ReleasedFeedback(2, 2, 5, 1, losses, 0.0, extra)])


def test_control_variate_increment_hand_case():
    pol = _policy("prediction_assisted")
    # mu=0.5, q=0.25, asked, D=-1: x = 0.5 + (-1.5)/0.25 = -5.5 ; unasked: x = mu = 0.5
    assert pol.evidence_increment(0.25, 0.5, -1.0, 1) == pytest.approx(-5.5)
    assert pol.evidence_increment(0.25, 0.5, 0.0, 0) == pytest.approx(0.5)


# ---------------------------------------------------------------- budget feasibility
@pytest.mark.parametrize("variant", ["acquisition_only", "prediction_assisted"])
@pytest.mark.parametrize("budget", [0, 5, 40])
def test_budget_feasible_pathwise(variant, budget):
    _, res = _run(variant, budget=budget)
    assert not check_budget_feasible(res, budget)
    assert res.requested_labels <= budget
    assert res.refused_requests == 0  # the policy never asks at zero budget


def test_cap_binding_is_measured():
    # Floor above B/T: expected demand exceeds B, so the hard cap visibly binds.
    pol, res = _run("acquisition_only", budget=10, q_min=0.2)
    assert res.requested_labels == 10
    assert pol.cap_suppressed > 0 and pol.expected_demand > 10
    assert pol.floor_infeasible_events > 0
    # Generous cap: spending stays under it and nothing is suppressed.
    pol2, res2 = _run("acquisition_only", budget=500)
    assert res2.requested_labels < 500 and pol2.cap_suppressed == 0


# ---------------------------------------------------------------- nuisance data discipline
def test_nuisance_refuses_locked_window_or_future():
    preds, y, x = _stream(T=100)
    d = _d(preds, y)
    with pytest.raises(ValueError):
        PairedDiffPredictor().fit(x, d, data_end=101, locked_start=100)
    assert PairedDiffPredictor().fit(x, d, data_end=100, locked_start=100).fit_end == 100


def test_prediction_assisted_rate_varies_with_predictor():
    pol, _ = _run("prediction_assisted", budget=80)
    assert pol.max_q > pol.min_q  # score varies with the fitted mu_hat(x)
    assert pol.nuisance.fit_end == 800


def test_variant_validation():
    with pytest.raises(ValueError):
        XuAcquisitionPolicy("prediction_assisted", np.random.default_rng(0), delay=2)
    with pytest.raises(ValueError):
        XuAcquisitionPolicy("acquisition_only", np.random.default_rng(0), delay=0)
    assert _policy("prediction_assisted").name != _policy("acquisition_only").name


# ---------------------------------------------------------------- determinism / state
@pytest.mark.parametrize("variant", ["acquisition_only", "prediction_assisted"])
def test_deterministic(variant):
    a, ra = _run(variant, seed=4)
    b, rb = _run(variant, seed=4)
    assert ra.records == rb.records and a.state_dict() == b.state_dict()


def test_state_roundtrip():
    pol, _ = _run("prediction_assisted", budget=60)
    st = pol.state_dict()
    fresh = _policy("prediction_assisted")
    fresh.load_state_dict(st)
    assert fresh.state_dict() == st


# ---------------------------------------------------------------- author-code status
def test_author_code_status_recorded():
    """BLOCKED record: why no numerical comparison with the author code exists."""
    f = ROOT / "vendor_sota/xu_rcps/Predictor.py"
    if not f.exists():
        pytest.skip("author clone not present")
    with pytest.raises(SyntaxError):
        compile(f.read_text(), str(f), "exec")
