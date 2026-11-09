"""Tests for the Online LLM Picker port, including the degeneracy claim we must disclose."""

import sys
from pathlib import Path

import numpy as np
import pytest

SOTA = Path(__file__).resolve().parents[2] / "scripts/promising_directions/sota"
sys.path.insert(0, str(SOTA))
sys.path.insert(0, str(SOTA / "competitors"))

from online_llm_picker import OnlineLLMPicker, pseudo_loss_matrix
from simulator import check_budget_feasible, run_episode


def mk(n_models=2, seed=0, **kw):
    return OnlineLLMPicker(n_models, 2, rng=np.random.default_rng(seed), **kw)


def test_pseudo_loss_matrix_is_exact_agreement():
    preds = np.array([0, 1, 1])
    L = pseudo_loss_matrix(preds, 2)
    assert np.array_equal(L[0], [0.0, 1.0, 1.0])  # if truth were class 0
    assert np.array_equal(L[1], [1.0, 0.0, 0.0])  # if truth were class 1


def test_agreement_region_gives_zero_query_probability():
    p = mk()
    q, mv = p.query_probability(np.array([1, 1]), t=5)
    assert q == 0.0 and mv == 0.0


def test_query_probability_matches_hand_computation_on_disagreement():
    """Uniform posterior over 2 models: Var = 0.25, Hbar = 1, so q = clip(max(0.25, eta), 0, 1)."""
    p = mk()
    t = 50
    q, max_var = p.query_probability(np.array([0, 1]), t=t)
    assert max_var == pytest.approx(0.25)
    assert q == pytest.approx(min(max(0.25, p.eta(t)), 1.0))


def test_eta_floor_saturates_before_any_annotation_so_early_rounds_query_everything():
    """Behavioural consequence of the published eta_t, and a hazard under a hard cap.

    eta_t = sqrt(log m / (t * (Vhat + eps))) and Vhat = 0 until the first annotation, so eta is
    enormous and q clips to 1: every disagreement is queried during burn-in. Under the paper's
    expected-proportion budget that is tolerable; under our hard cap it spends the budget at the
    very start. This is measured, not assumed, and is disclosed with the comparator.
    """
    p = mk()
    assert p.n_annotated == 0
    for t in (1, 10, 100, 1000):
        q, _ = p.query_probability(np.array([0, 1]), t=t)
        assert q == 1.0
    # once annotations arrive and Vhat > 0, the floor falls back below 1
    from simulator import ReleasedFeedback

    for i in range(40):
        p.observe(
            [
                ReleasedFeedback(
                    event_id=i,
                    t_requested=i,
                    t_released=i + 1,
                    label=0,
                    model_losses=np.array([0, 1], dtype=np.int8),
                    query_probability=0.5,
                )
            ]
        )
    assert p.eta(1000) < 1.0


def test_budget_is_front_loaded_under_the_cap():
    """The burn-in above, measured end to end rather than assumed.

    It is not a pure burn-in: delayed annotations begin lowering eta part-way through, so q falls
    below 1 and acquisition becomes probabilistic again. What is robust is the front-loading --
    half the budget goes in the opening sixth of the episode -- which is the consequence of the
    eta floor that matters under a hard cap.
    """
    preds, labels = _stream(T=600, seed=8)
    p = mk(seed=8)
    res = run_episode(
        p,
        model_predictions=preds,
        labels=labels,
        delay=5,
        budget=25,
        label_price=0.05,
        switch_cost=5.0,
    )
    bought = [r["event_id"] for r in res.records if r["requested"]]
    assert len(bought) == 25
    assert float(np.median(bought)) < 600 / 5  # measured: median 90 of 600
    assert sum(t < 600 / 2 for t in bought) >= int(np.ceil(0.9 * len(bought)))


def test_degeneracy_query_rule_is_instance_blind_in_the_binary_two_model_case():
    """The disclosure: q_t depends only on posterior balance, not on which way they disagree.

    This reproduces, by a different route, the collapse already measured for Model Picker.
    """
    rng = np.random.default_rng(3)
    for _ in range(200):
        p = mk()
        p.Lhat = rng.random(2) * 10  # arbitrary posterior
        t = int(rng.integers(1, 500))
        q01, v01 = p.query_probability(np.array([0, 1]), t)
        q10, v10 = p.query_probability(np.array([1, 0]), t)
        # both disagreement patterns give identical acquisition: no instance information
        assert q01 == pytest.approx(q10)
        assert v01 == pytest.approx(v10)


def test_degeneracy_matches_the_closed_form_p_times_one_minus_p():
    """max_k Var_k = p(1-p) exactly, for two models on disagreement."""
    rng = np.random.default_rng(11)
    for _ in range(100):
        p = mk()
        p.Lhat = rng.random(2) * 5
        t = int(rng.integers(1, 200))
        post = p.posterior(t)
        _, max_var = p.query_probability(np.array([0, 1]), t)
        assert max_var == pytest.approx(post[0] * post[1])


def test_importance_weight_uses_issue_time_propensity():
    from simulator import ReleasedFeedback

    p = mk()
    fb = ReleasedFeedback(
        event_id=0,
        t_requested=0,
        t_released=1,
        label=0,
        model_losses=np.array([0, 1], dtype=np.int8),
        query_probability=0.25,
    )
    p.observe([fb])
    assert p.Lhat == pytest.approx(np.array([0.0, 4.0]))  # 1 / 0.25


def test_observe_rejects_non_positive_propensity():
    from simulator import ReleasedFeedback

    p = mk()
    bad = ReleasedFeedback(
        event_id=0,
        t_requested=0,
        t_released=1,
        label=0,
        model_losses=np.array([0, 1], dtype=np.int8),
        query_probability=0.0,
    )
    with pytest.raises(ValueError, match="non-positive issue-time propensity"):
        p.observe([bad])


def _stream(T=400, seed=0):
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, 2, T)
    p0 = np.where(rng.random(T) < 0.70, labels, 1 - labels)
    p1 = np.where(rng.random(T) < 0.80, labels, 1 - labels)
    return np.stack([p0, p1], axis=1), labels


def test_hard_budget_holds_pathwise_through_the_simulator():
    preds, labels = _stream()
    p = mk(seed=5)
    res = run_episode(
        p,
        model_predictions=preds,
        labels=labels,
        delay=5,
        budget=30,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert check_budget_feasible(res, 30) == []
    assert res.requested_labels <= 30


def test_uncapped_variant_exceeds_the_cap_showing_the_cap_is_an_adapter():
    """The published budget is an expected proportion; our cap is an imposed adapter."""
    preds, labels = _stream(seed=2)
    capped = run_episode(
        mk(seed=7),
        model_predictions=preds,
        labels=labels,
        delay=5,
        budget=20,
        label_price=0.05,
        switch_cost=5.0,
    )
    uncapped = run_episode(
        mk(seed=7, enforce_cap=False),
        model_predictions=preds,
        labels=labels,
        delay=5,
        budget=10**6,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert capped.requested_labels <= 20
    assert uncapped.requested_labels > 20  # the cap genuinely binds


def test_determinism_same_seed_same_trajectory():
    preds, labels = _stream(seed=4)
    a = run_episode(
        mk(seed=9),
        model_predictions=preds,
        labels=labels,
        delay=3,
        budget=40,
        label_price=0.05,
        switch_cost=5.0,
    )
    b = run_episode(
        mk(seed=9),
        model_predictions=preds,
        labels=labels,
        delay=3,
        budget=40,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert a.net_cost == b.net_cost
    assert a.requested_labels == b.requested_labels
    assert a.deployment_switches == b.deployment_switches


def test_state_dict_round_trip():
    p = mk(seed=1)
    p.Lhat = np.array([1.5, 2.5])
    p.V, p.n_annotated, p._deployed = 0.3, 4, 1
    q = mk(seed=1)
    q.load_state_dict(p.state_dict())
    assert np.array_equal(q.Lhat, p.Lhat)
    assert (q.V, q.n_annotated, q._deployed) == (p.V, p.n_annotated, p._deployed)
