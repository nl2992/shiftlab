"""Tests for the Model Picker port (native and deployment adapter)."""

import types
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))

from competitors.model_picker import (  # noqa: E402
    ModelPickerDeploymentAdapter,
    ModelPickerNative,
    compute_u_t,
    eta_t,
    posterior,
    query_probability,
)
from simulator import (  # noqa: E402
    Event,
    ReleasedFeedback,
    check_budget_feasible,
    policy_rng,
    run_episode,
)

AUTHOR_FILE = ROOT / "vendor_sota/model_picker/src/methods/model_picker.py"


def _stream(T=400, seed=0, acc=(0.8, 0.7), n_classes=2):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, n_classes, T)
    preds = np.stack(
        [
            np.where(rng.random(T) < a, y, (y + 1 + rng.integers(0, n_classes - 1, T)) % n_classes)
            for a in acc
        ],
        axis=1,
    )
    return preds, y


def test_posterior_matches_hand_computation():
    loss = np.array([3.0, 1.0, 2.0])
    eta = 0.5
    expected = np.exp(-0.5 * np.array([2.0, 0.0, 1.0]))
    expected /= expected.sum()
    np.testing.assert_allclose(posterior(loss, eta), expected)
    # shift invariance (the reference subtracts min loss only for numerical safety)
    np.testing.assert_allclose(posterior(loss + 100, eta), expected)


def test_u_t_hand_computed():
    # 3 models, 3 classes, predictions (0,1,2), posterior (0.5, 0.3, 0.2).
    # class 0: wrong mass = 0.3+0.2 = 0.5 -> 0.25 ; class 1: 0.7 -> 0.21 ; class 2: 0.8 -> 0.16
    p = np.array([0.5, 0.3, 0.2])
    assert compute_u_t(p, np.array([0, 1, 2]), 2.0, 3) == pytest.approx(2.0 * 0.25)


def test_agreement_region_never_queries():
    p = np.array([0.5, 0.5])
    assert query_probability(p, np.array([1, 1]), 1.0, 2, eta=0.9) == 0.0
    a = ModelPickerDeploymentAdapter(2, 2, np.random.default_rng(0))
    ev = Event(event_id=0, t=0, horizon=10, model_predictions=np.array([1, 1]))
    assert not a.request_labels(ev, 5).requested


def test_u_t_floored_at_eta_t():
    # nearly one-hot posterior: p(1-p) ~ 0 but positive, so the floor must lift it to eta_t
    p = np.array([0.999999, 1e-6])
    t = 9
    eta = eta_t(2, t)
    u = query_probability(p, np.array([0, 1]), 1.0, 2, eta)
    assert u == pytest.approx(eta)
    assert u > compute_u_t(p, np.array([0, 1]), 1.0, 2)


def test_importance_weight_uses_issue_time_propensity():
    a = ModelPickerDeploymentAdapter(2, 2, np.random.default_rng(0))
    fb = ReleasedFeedback(
        event_id=0,
        t_requested=0,
        t_released=3,
        label=1,
        model_losses=np.array([1, 0], dtype=np.int8),
        query_probability=0.125,
    )
    a.observe([fb])
    np.testing.assert_allclose(a.loss, [8.0, 0.0])  # 1 / 0.125, whatever the posterior now is
    a.observe([fb])
    np.testing.assert_allclose(a.loss, [16.0, 0.0])
    with pytest.raises(ValueError):
        a.observe([ReleasedFeedback(1, 1, 2, 0, np.array([1, 0]), 0.0)])


def test_adapter_budget_feasible_pathwise_and_deterministic():
    preds, y = _stream()
    out = []
    for _ in range(2):
        pol = ModelPickerDeploymentAdapter(2, 2, policy_rng(7, 0, "model_picker_adapter"))
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=y,
            delay=5,
            budget=20,
            label_price=0.1,
            switch_cost=1.0,
        )
        assert check_budget_feasible(res, 20) == []
        out.append(res.records)
    assert out[0] == out[1]


def test_adapter_never_requests_at_zero_budget():
    preds, y = _stream()
    pol = ModelPickerDeploymentAdapter(2, 2, policy_rng(1, 0, "x"))
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=1, budget=0, label_price=0.0, switch_cost=0.0
    )
    assert res.requested_labels == 0 and res.refused_requests == 0


def test_native_ignores_cap_when_querying_but_not_when_recording():
    preds, y = _stream(T=600)
    mp = ModelPickerNative(2, 2)
    out = mp.run(preds, y, budget=10, rng=np.random.default_rng(3))
    assert out["z_t_log"].sum() > 10  # keeps querying (and updating) past the cap
    # reference bookkeeping: cumulative count must be < budget when recorded -> budget-1 records
    assert out["z_t_budget"].sum() == 9


def test_deployment_is_recommendation_with_sticky_ties():
    a = ModelPickerDeploymentAdapter(3, 2, np.random.default_rng(0), initial_model=1)
    ev = Event(0, 0, 5, np.array([0, 1, 1]))
    assert a.predict(ev) == 1  # all tied -> keep deployed
    a.loss = np.array([0.0, 2.0, 0.0])
    assert a.predict(ev) == 0  # model 1 no longer a minimiser -> lowest-index minimiser


# ---- numerical reproduction of the author's function ------------------------------------------
def _author_fn():
    if not AUTHOR_FILE.exists():
        pytest.skip("vendor_sota/model_picker is gitignored and not present")
    src = AUTHOR_FILE.read_text()
    # BLOCKED (worked around, in memory only): on this numpy the reference's
    # ``z_t_log[t-1] = np.random.binomial(size=1, n=1, p=u_t)`` raises "setting an array element
    # with a sequence". The one call is rewritten to return a scalar from the same RNG stream; no
    # arithmetic is touched and the vendored file on disk is unchanged.
    patched = src.replace("np.random.binomial(size=1, n=1, p=u_t)", "np.random.binomial(1, u_t)")
    assert patched != src
    mod = types.ModuleType("author_model_picker")
    exec(compile(patched, str(AUTHOR_FILE), "exec"), mod.__dict__)
    return mod.model_picker


@pytest.mark.parametrize(
    "seed,n_models,n_classes,budget", [(0, 2, 2, 25), (1, 3, 4, 40), (2, 5, 3, 10)]
)
def test_native_reproduces_author_outputs_exactly(seed, n_models, n_classes, budget):
    author = _author_fn()
    T = 300
    rng = np.random.default_rng(100 + seed)
    y = rng.integers(0, n_classes, T)
    preds = np.stack(
        [
            np.where(rng.random(T) < 0.6 + 0.05 * k, y, rng.integers(0, n_classes, T))
            for k in range(n_models)
        ],
        axis=1,
    )
    data = SimpleNamespace(
        _num_models=n_models,
        _num_classes=n_classes,
        _num_instances=T,
        _budgets=[budget],
        _predictions=preds,
        _oracle=y,
    )
    np.random.seed(1234 + seed)
    ref = author(data, 0, np.arange(T), 1.0, "Variance")
    mine = ModelPickerNative(n_models, n_classes, 1.0).run(
        preds, y, budget, np.random.RandomState(1234 + seed)
    )
    z_log, _, z_budget, hidden, post = ref
    np.testing.assert_array_equal(mine["z_t_log"], z_log)
    np.testing.assert_array_equal(mine["z_t_budget"], z_budget)
    np.testing.assert_array_equal(mine["hidden_loss_log"], hidden)
    np.testing.assert_allclose(mine["posterior_log"], post, rtol=0, atol=1e-12)
    assert z_log.sum() > 0


# ---- measurement 1: does the query rule collapse in the binary two-model case? ----------------
def test_binary_two_model_u_depends_only_on_posterior_balance():
    rng = np.random.default_rng(0)
    for _ in range(200):
        q = rng.random()
        p = np.array([q, 1 - q])
        us = {compute_u_t(p, pr, 1.0, 2) for pr in (np.array([0, 1]), np.array([1, 0]))}
        for u in us:
            assert u == pytest.approx(q * (1 - q))
        assert len({round(u, 12) for u in us}) == 1  # identical for every disagreement pattern
        assert compute_u_t(p, np.array([0, 0]), 1.0, 2) == 0.0


def test_report_floor_dominance_in_binary_two_model_stream(capsys):
    """Measures how often the eta_t floor, a data-independent schedule, sets the final u_t."""
    fracs = []
    for seed in range(5):
        preds, y = _stream(T=2000, seed=seed)
        out = ModelPickerNative(2, 2).run(preds, y, 10**9, np.random.default_rng(seed))
        dis = preds[:, 0] != preds[:, 1]
        t = np.arange(1, len(y) + 1)
        raw = out["posterior_log"][:, 0] * out["posterior_log"][:, 1]
        floor = np.array([eta_t(2, k) for k in t])
        fracs.append(float(np.mean((raw < floor)[dis])))
    print(f"floor binds on {np.mean(fracs):.3f} of disagreement rounds (per-seed {fracs})")
    # structural claim only: u is a function of (posterior balance, t); the value is reported.
    assert all(0.0 <= f <= 1.0 for f in fracs)


# ---- measurement 2: native vs adapter -----------------------------------------------------------
def test_report_native_vs_adapter_difference(capsys):
    """Native keeps learning past the cap; the adapter cannot. Reports the gap."""
    diffs = []
    for seed in range(5):
        preds, y = _stream(T=1500, seed=seed, acc=(0.75, 0.7))
        budget = 25
        nat = ModelPickerNative(2, 2).run(preds, y, budget, np.random.default_rng(seed))
        pol = ModelPickerDeploymentAdapter(2, 2, policy_rng(seed, 0, "model_picker_adapter"))
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=y,
            delay=1,
            budget=budget,
            label_price=0.0,
            switch_cost=0.0,
        )
        diffs.append((int(nat["z_t_log"].sum()), res.requested_labels, res.refused_requests))
    print("native queries, adapter queries, adapter refused:", diffs)
    assert all(a >= 25 for _, a, _ in diffs) or all(a <= 25 for _, a, _ in diffs)
    assert all(n > a for n, a, _ in diffs)  # the native ignores the cap
