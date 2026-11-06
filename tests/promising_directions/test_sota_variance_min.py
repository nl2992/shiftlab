"""Tests for the variance-minimisation port (native, causal adapter, streaming IPW)."""

import importlib.util
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))

from competitors.variance_min import (
    VarianceMinCausalAdapter,
    VarianceMinNative,
    VarianceMinStreamingIPW,
    binary_zero_one_score_is_disagreement,
    fit_class_prior,
    lure,
    pair_score,
    query_weights,
    zero_one_loss_table,
)
from simulator import (
    Event,
    ReleasedFeedback,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)

AUTHOR_SRC = ROOT / "vendor_sota/variance_min/src"


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


def test_score_hand_computed():
    # 3 classes, models predict (0,1), surrogate (.5,.3,.2): c0 |0-1|, c1 |1-0|, c2 |1-1|
    table = zero_one_loss_table(np.array([[0, 1], [2, 2]]), 3)
    p = np.tile([0.5, 0.3, 0.2], (2, 1))
    np.testing.assert_allclose(pair_score(table, p), [0.8, 0.0])
    q = query_weights(table, p, eps=0.01, normalize=True)
    np.testing.assert_allclose(q, np.array([0.81, 0.01]) / 0.82)


def test_binary_two_model_score_is_exactly_disagreement():
    """Analytic: |l1(c)-l2(c)| = 1[pred1 != pred2] for both c, so score = disagree * sum_c p_c."""
    rng = np.random.default_rng(1)
    preds = rng.integers(0, 2, size=(500, 2))
    for _ in range(5):  # any surrogate, including a hostile one
        a = rng.random(500)
        p_est = np.stack([a, 1 - a], axis=1)
        assert binary_zero_one_score_is_disagreement(preds, p_est)
    # three classes: the collapse is gone, the surrogate now matters
    p3 = np.array([[0.7, 0.2, 0.1]])
    t3 = zero_one_loss_table(np.array([[0, 1]]), 3)
    assert pair_score(t3, p3)[0] == pytest.approx(0.9)
    p3b = np.array([[0.1, 0.1, 0.8]])
    assert pair_score(t3, p3b)[0] == pytest.approx(0.2)


def test_lure_hand_computed():
    ll = np.array([[1.0, 0.0], [0.0, 1.0]])
    q = np.array([0.5, 0.25])
    # m=1: 1 + (1/(4*.5) - 1) * 2/3 = 2/3 ; m=2: 1 + (1/(3*.25) - 1) * 2/2 = 4/3
    np.testing.assert_allclose(lure(ll, q, 4), [(2 / 3) / 2, (4 / 3) / 2], atol=1e-7)


def test_lure_unbiased_by_exact_enumeration():
    """Enumerate every ordered draw of M=2 from N=4 with the ACTUAL sequential probabilities
    (renormalised over the remaining pool) and check E[LURE] equals the pool mean loss exactly."""
    N = 4
    rng = np.random.default_rng(3)
    loss = rng.integers(0, 2, size=(N, 2)).astype(float)
    w = np.array([5.0, 1.0, 2.0, 0.5])
    expect = np.zeros(2)
    for a, b in itertools.permutations(range(N), 2):
        qa = w[a] / w.sum()
        rest = w.copy()
        rest[a] = 0
        qb = w[b] / rest.sum()
        h = lure(loss[[a, b]], np.array([qa, qb]), N)
        expect += qa * qb * h
    np.testing.assert_allclose(expect, loss.mean(axis=0), atol=1e-6)


def test_native_reproducible_and_no_label_leak():
    preds, y = _stream(120)
    p = np.full((120, 2), 0.5)
    m = VarianceMinNative(2)
    a = m.run(preds, y, p, 30, rng=np.random.default_rng(0))
    b = m.run(preds, y, p, 30, rng=np.random.default_rng(0))
    np.testing.assert_array_equal(a["hat"], b["hat"])
    assert len(set(a["queried"].tolist())) == 30  # without replacement
    # labels are read only at the drawn points: scrambling the others changes nothing
    y2 = y.copy()
    keep = set(a["queried"].tolist())
    for i in range(len(y2)):
        if i not in keep:
            y2[i] = 1 - y2[i]
    c = m.run(preds, y2, p, 30, rng=np.random.default_rng(0))
    np.testing.assert_array_equal(a["hat"], c["hat"])


# ---------------------------------------------------------------- numerical agreement w/ author
def _load_author():
    pytest.importorskip("numba", reason="author code needs numba (run: uv run --with numba ...)")
    if not AUTHOR_SRC.exists():
        pytest.skip("vendor_sota/variance_min not cloned")
    mods = {}
    for name in ("query", "estimator"):
        spec = importlib.util.spec_from_file_location(
            f"_vm_author_{name}", AUTHOR_SRC / f"{name}.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mods[name] = mod
    return mods["query"], mods["estimator"]


@pytest.mark.parametrize("n_classes,K", [(2, 2), (3, 2), (4, 3)])
def test_score_and_lure_match_author_code(n_classes, K):
    query, estimator = _load_author()
    rng = np.random.default_rng(7)
    N = 60
    preds = rng.integers(0, n_classes, size=(N, K))
    p_est = rng.dirichlet(np.ones(n_classes), size=N)
    table = zero_one_loss_table(preds, n_classes)
    idx = np.arange(N, dtype=np.int64)
    theirs = query.q_by_loss_diff(table, p_est, list(idx), normalize=False)
    ours = query_weights(table, p_est, None, normalize=False)
    np.testing.assert_allclose(ours, theirs, rtol=1e-12)
    ll = rng.integers(0, 2, size=(20, K)).astype(float)
    q = rng.random(20) * 0.5 + 0.05
    np.testing.assert_allclose(lure(ll, q, N), estimator.LURE(ll, q, N), rtol=1e-12)


def test_full_loop_matches_author_run_model_selection():
    """Author loop (Sec5/test.py lines 42-75) copied verbatim, sampler = author's numba
    ``sample_from_p`` with the author's seeds; ours reuses that sampler so the draw sequence is
    identical. Compares queried order, recorded q and every LURE row."""
    query, estimator = _load_author()
    preds, y = _stream(150, seed=5, n_classes=3)
    p_est = np.random.default_rng(2).dirichlet(np.ones(3), size=150)
    N = 150
    table = zero_one_loss_table(preds, 3)
    l_true = (preds != y[:, None]).astype(float)
    Ltrue = [l_true[:, k] for k in range(2)]  # Sec5 layout: model -> per-point loss

    def author_loop(seed, n_steps=40):  # verbatim logic of Sec5/test.py lines 42-75
        idx_u = list(range(N))
        L, q, hat, order = [], [], [], []
        q_full = query.q_by_loss_diff(table, p_est, idx_u, normalize=False)
        for i in range(n_steps):
            q_now = q_full[idx_u]
            q_now = q_now / np.sum(q_now)
            k = query.sample_from_p(q_now, seed=N * seed + i + 1)
            j = idx_u[k]
            L.append([LL[j] for LL in Ltrue])
            q.append(q_now[k])
            hat.append(estimator.LURE(np.array(L), np.array(q), N))
            idx_u.pop(k)
            order.append(j)
        return np.array(hat), order, np.array(q)

    seed = 3
    h_a, o_a, q_a = author_loop(seed)
    ours = VarianceMinNative(3).run(
        preds,
        y,
        p_est,
        40,
        sampler=lambda q_now, i: int(query.sample_from_p(q_now, seed=N * seed + i + 1)),
    )
    assert list(ours["queried"]) == o_a
    np.testing.assert_allclose(ours["q"], q_a, rtol=1e-12)
    np.testing.assert_allclose(ours["hat"], h_a, rtol=1e-12)


# ---------------------------------------------------------------- adapter through the simulator
def _adapter(cls, preds, y, seed, rate, dev_n=200):
    prior = fit_class_prior(y[:dev_n], 2)  # development labels only
    return cls(2, 2, policy_rng(seed, 0, cls.name), rate=rate, class_prior=prior)


@pytest.mark.parametrize("cls", [VarianceMinCausalAdapter, VarianceMinStreamingIPW])
def test_budget_feasible_no_future_and_deterministic(cls):
    preds, y = _stream(500, seed=11)
    kw = {
        "model_predictions": preds,
        "labels": y,
        "delay": 7,
        "budget": 25,
        "label_price": 0.1,
        "switch_cost": 1.0,
    }
    r1 = run_episode(_adapter(cls, preds, y, 4, rate=0.2), **kw)
    r2 = run_episode(_adapter(cls, preds, y, 4, rate=0.2), **kw)
    assert check_budget_feasible(r1, 25) == []
    assert check_no_future_access(r1, 7) == []
    assert r1.requested_labels == 25 and r1.refused_requests >= 0
    assert r1.records == r2.records and r1.net_cost == r2.net_cost


def test_zero_budget_requests_nothing():
    preds, y = _stream(100)
    pol = _adapter(VarianceMinCausalAdapter, preds, y, 0, rate=0.5)
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=1, budget=0, label_price=0.1, switch_cost=1.0
    )
    assert res.requested_labels == 0 and res.refused_requests == 0


def test_only_arrived_events_and_frozen_propensity():
    """The score for event t uses only its own predictions; the normaliser is the running mean over
    events 0..t. Feeding future events later must not change earlier propensities."""
    preds, y = _stream(60, seed=2)
    a = _adapter(VarianceMinCausalAdapter, preds, y, 1, rate=0.3)
    ps = []
    for t in range(30):
        ev = Event(event_id=t, t=t, horizon=60, model_predictions=preds[t])
        a.predict(ev)
        ps.append(a.propensity(ev))
    b = _adapter(VarianceMinCausalAdapter, preds, y, 1, rate=0.3)
    qs = []
    for t in range(30):
        ev = Event(event_id=t, t=t, horizon=60, model_predictions=preds[t])
        qs.append(b.propensity(ev))
    # identical prefix whatever happens after; and agreeing events get the eps floor, not zero
    assert ps == qs
    agree = preds[:30, 0] == preds[:30, 1]
    assert all(p > 0 for p in ps)
    if agree.any() and (~agree).any():
        assert max(np.array(ps)[agree]) < min(np.array(ps)[~agree])


def test_adapter_uses_issue_time_propensity_not_recomputation():
    a = VarianceMinStreamingIPW(
        2, 2, np.random.default_rng(0), rate=0.5, class_prior=np.array([0.5, 0.5])
    )
    a.horizon = 10
    a.observe([ReleasedFeedback(0, 0, 3, 1, np.array([1, 0]), 0.25)])
    np.testing.assert_allclose(a.estimate(), np.array([1 / 0.25, 0.0]) / 10)
    with pytest.raises(ValueError):
        a.observe([ReleasedFeedback(1, 1, 4, 0, np.array([0, 1]), 0.0)])


def test_state_roundtrip():
    preds, y = _stream(80)
    pol = _adapter(VarianceMinCausalAdapter, preds, y, 0, rate=0.3)
    run_episode(
        pol, model_predictions=preds, labels=y, delay=2, budget=20, label_price=0.1, switch_cost=1.0
    )
    other = _adapter(VarianceMinCausalAdapter, preds, y, 0, rate=0.3)
    other.load_state_dict(pol.state_dict())
    np.testing.assert_allclose(other.estimate(), pol.estimate())


def test_streaming_ipw_unbiased_and_lure_adapter_bias_is_measured():
    """Monte Carlo over the sampler with the data fixed and the cap not binding. IPW (HT) must be
    unbiased for the stream mean loss. The LURE-on-stream estimator is only measured; its
    unbiasedness is not claimed (BLOCKED in the module), so the assertion is a loose sanity bound
    and the printed gap is what gets reported."""
    preds, y = _stream(300, seed=21, acc=(0.85, 0.6))
    truth = (preds != y[:, None]).mean(axis=0)
    est = {VarianceMinStreamingIPW: [], VarianceMinCausalAdapter: []}
    for cls, acc in est.items():
        for s in range(300):
            pol = _adapter(cls, preds, y, s, rate=0.15)
            run_episode(
                pol,
                model_predictions=preds,
                labels=y,
                delay=3,
                budget=300,
                label_price=0.0,
                switch_cost=0.0,
                trace=False,
            )
            acc.append(pol.estimate())
    ipw = np.mean(est[VarianceMinStreamingIPW], axis=0)
    lur = np.mean(est[VarianceMinCausalAdapter], axis=0)
    sd = np.std(est[VarianceMinStreamingIPW], axis=0) / np.sqrt(300)
    print("truth", truth, "ipw", ipw, "lure_adapter", lur)
    np.testing.assert_allclose(ipw, truth, atol=4 * sd.max() + 1e-3)
    assert np.all(np.abs(lur - truth) < 0.05)
