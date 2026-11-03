"""Tests for the CAMS port: hand-computed steps, invariants, and agreement with the author code."""

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota/competitors"))

import cams
from cams import (
    CAMSDeploymentAdapter,
    CAMSNative,
    constant_policy_advice,
    normalise_advice,
    policy_posterior,
    query_probability,
    smooth_advice,
    stack_advice,
    weighted_entropy_query,
)
from simulator import (
    Event,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)

VENDOR = ROOT / "vendor_sota/cams"


def synth(T=120, M=3, K=3, seed=0):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, K, T)
    acc = np.array([0.8, 0.6, 0.4][:M] + [0.5] * max(0, M - 3))
    preds = np.where(rng.random((T, M)) < acc, y[:, None], rng.integers(0, K, (T, M)))
    ctx = rng.normal(size=(T, 2))
    return preds, y, ctx


def toy_advice(M):
    """Two fixed contextual policies (context-free here) plus the constant policies."""
    pols = [lambda c: np.array([1.0] + [0.0] * (M - 1)) + 0.0 * c[0], lambda c: np.ones(M)]
    return stack_advice(M, pols)


# ---------------------------------------------------------------------------------------------
# 1. hand-computed weight update
# ---------------------------------------------------------------------------------------------
def test_policy_weight_update_matches_hand_computation():
    # 2 models, 3 policies with raw advice [1,0], [0,1], [1,1]; models predict 0 and 1; K=2.
    raw = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    e = smooth_advice(normalise_advice(raw))
    # row [1,0]: mean .5, e0 = .25+.25 = .5, (row+.5)/2 = [.75,.25]; row [1,1]/2 = [.5,.5] has e0=0
    np.testing.assert_allclose(e, [[0.75, 0.25], [0.25, 0.75], [0.5, 0.5]])

    # t = 1: Loss = 0 so Q is uniform and w = [.5,.5]; v = (2 * (-.5 log2 .5)) / 2 = .5;
    # u = max(.5, 1/sqrt(1)) = 1, so the label is certain to be requested.
    preds = np.array([0, 1])
    q1 = policy_posterior(np.zeros(3), math.sqrt(3 / 1))
    w1 = q1 @ e
    np.testing.assert_allclose(w1, [0.5, 0.5])
    assert weighted_entropy_query(2, w1, preds) == pytest.approx(0.5)
    assert query_probability(2, w1, preds, 1) == 1.0

    # label y = 0 => model losses [0,1]; Loss += E @ (loss/1) = E[:,1] = [.25, .75, .5]
    loss = cams.loss_increment(e, np.array([0, 1]), 1.0)
    np.testing.assert_allclose(loss, [0.25, 0.75, 0.5])

    # t = 2: eta = sqrt(3/2); Q ∝ exp(-eta * [.25,.75,.5]), computed here by explicit arithmetic.
    eta = math.sqrt(3 / 2)
    num = [math.exp(-eta * 0.25), math.exp(-eta * 0.75), math.exp(-eta * 0.5)]
    expected_q = [x / sum(num) for x in num]
    q2 = policy_posterior(loss, cams.learning_rate(3, 2))
    np.testing.assert_allclose(q2, expected_q)

    # ... and through the Native policy object: observe() then the next predict
    adv = lambda ev: raw
    pol = CAMSNative(n_models=2, n_classes=2, advice_fn=adv, rng=np.random.default_rng(0))
    ev0 = Event(0, 0, 10, preds, None)
    pol.predict(ev0)
    req = pol.request_labels(ev0, 5)
    assert req.requested and req.probability == 1.0
    from simulator import ReleasedFeedback

    pol.observe(
        [ReleasedFeedback(0, 0, 1, 0, np.array([0, 1]), req.probability, dict(req.extra))]
    )
    np.testing.assert_allclose(pol.core.loss_tilde, [0.25, 0.75, 0.5])
    ev1 = Event(1, 1, 10, preds, None)
    w2 = pol.core.recommendation(ev1)
    np.testing.assert_allclose(w2, np.array(expected_q) @ e)


def test_cams_max_uses_best_policy_row_only():
    raw = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    pol = CAMSNative(
        n_models=2, n_classes=2, advice_fn=lambda ev: raw, rng=np.random.default_rng(0),
        variant="CAMS-MAX",
    )
    pol.core.loss_tilde = np.array([5.0, 0.0, 5.0])  # policy 1 is best
    ev = Event(3, 3, 10, np.array([0, 1]), None)
    w = pol.core.recommendation(ev)
    np.testing.assert_allclose(w, [0.25, 0.75])  # smoothed row of policy 1


# ---------------------------------------------------------------------------------------------
# 2. query probability
# ---------------------------------------------------------------------------------------------
def test_query_probability_in_unit_interval_and_zero_in_agreement_region():
    rng = np.random.default_rng(1)
    for _ in range(500):
        M, K = int(rng.integers(2, 6)), int(rng.integers(2, 5))
        w = rng.dirichlet(np.ones(M))
        t = int(rng.integers(1, 500))
        preds = rng.integers(0, K, M)
        u = query_probability(K, w, preds, t)
        assert 0.0 <= u <= 1.0
        if len(np.unique(preds)) == 1:
            assert u == 0.0  # author: CAMS_identity.py:126-130, utils.py:41-43


def test_query_probability_floor_is_inverse_sqrt_t_inside_disagreement():
    w = np.array([0.5, 0.5])
    preds = np.array([0, 1])
    # v = 0.5 for binary; the floor 1/sqrt(t) takes over once t > 4
    assert query_probability(2, w, preds, 100) == pytest.approx(0.5)
    assert query_probability(2, np.array([0.99, 0.01]), preds, 400) == pytest.approx(
        max(weighted_entropy_query(2, np.array([0.99, 0.01]), preds), 1 / 20)
    )


# ---------------------------------------------------------------------------------------------
# 3. budget feasibility, 4. no update before release, 5. determinism
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("variant", ["CAMS", "CAMS-MAX"])
def test_budget_feasible_pathwise_through_simulator(variant):
    preds, y, ctx = synth()
    M = preds.shape[1]
    pol = CAMSDeploymentAdapter(
        n_models=M, n_classes=3, advice_fn=toy_advice(M), rng=policy_rng(0, 0, "cams"),
        variant=variant,
    )
    res = run_episode(
        pol, model_predictions=preds, labels=y, contexts=ctx, delay=4, budget=7,
        label_price=0.05, switch_cost=1.0,
    )
    assert check_budget_feasible(res, 7) == []
    assert check_no_future_access(res, 4) == []
    assert res.requested_labels <= 7
    assert res.refused_requests == 0  # the adapter never asks beyond the cap


def test_no_update_before_release():
    preds, y, ctx = synth(T=60)
    M = preds.shape[1]
    delay = 9
    pol = CAMSDeploymentAdapter(
        n_models=M, n_classes=3, advice_fn=toy_advice(M), rng=policy_rng(2, 0, "cams")
    )
    res = run_episode(
        pol, model_predictions=preds, labels=y, contexts=ctx, delay=delay, budget=60,
        label_price=0.0, switch_cost=0.0, trace=True,
    )
    first_req = min(r["event_id"] for r in res.records if r["requested"])
    # replay with a recording observe to see when the first update lands
    seen_at = []
    pol2 = CAMSDeploymentAdapter(
        n_models=M, n_classes=3, advice_fn=toy_advice(M), rng=policy_rng(2, 0, "cams")
    )
    orig = pol2.observe

    def spy(fb):
        seen_at.append((len(res.records), fb[0].t_released, fb[0].t_requested))
        orig(fb)

    pol2.observe = spy  # type: ignore[method-assign]
    run_episode(
        pol2, model_predictions=preds, labels=y, contexts=ctx, delay=delay, budget=60,
        label_price=0.0, switch_cost=0.0,
    )
    assert seen_at, "expected at least one label to be released"
    assert all(rel - req == delay for _, rel, req in seen_at)
    assert min(rel for _, rel, _ in seen_at) == first_req + delay
    # before that release the policy state is untouched
    pol3 = CAMSDeploymentAdapter(
        n_models=M, n_classes=3, advice_fn=toy_advice(M), rng=policy_rng(2, 0, "cams")
    )
    for t in range(first_req + delay):
        ev = Event(t, t, 60, preds[t], ctx[t])
        pol3.predict(ev)
        pol3.request_labels(ev, 60)
        assert pol3.core.n_updates == 0
        assert pol3.core.loss_tilde is None or not np.any(pol3.core.loss_tilde)


def test_determinism_and_state_roundtrip():
    preds, y, ctx = synth(T=150, seed=3)
    M = preds.shape[1]

    def make():
        return CAMSDeploymentAdapter(
            n_models=M, n_classes=3, advice_fn=toy_advice(M), rng=policy_rng(7, 1, "cams")
        )

    kw = {"model_predictions": preds, "labels": y, "contexts": ctx, "delay": 3, "budget": 20,
              "label_price": 0.05, "switch_cost": 0.5}
    a = run_episode(make(), **kw)
    b = run_episode(make(), **kw)
    assert a.records == b.records and a.net_cost == b.net_cost

    # state_dict/load_state_dict: save mid-run, restore into a fresh object, continue identically
    p1 = make()
    for t in range(60):
        ev = Event(t, t, 150, preds[t], ctx[t])
        p1.predict(ev)
        p1.request_labels(ev, 20)
    snap = p1.state_dict()
    p2 = make()
    p2.load_state_dict(snap)
    for t in range(60, 100):
        ev = Event(t, t, 150, preds[t], ctx[t])
        assert p1.predict(ev) == p2.predict(ev)
        r1, r2 = p1.request_labels(ev, 20), p2.request_labels(ev, 20)
        assert (r1.requested, r1.probability) == (r2.requested, r2.probability)


def test_constant_policies_are_present_and_one_hot():
    adv = toy_advice(4)(Event(0, 0, 1, np.zeros(4, int), np.zeros(2)))
    assert adv.shape == (2 + 4, 4)
    np.testing.assert_array_equal(adv[2:], constant_policy_advice(4))


def test_adapter_with_sampling_matches_native_at_delay_one_with_ample_budget():
    preds, y, ctx = synth(T=100, seed=5)
    M = preds.shape[1]
    kw = {"model_predictions": preds, "labels": y, "contexts": ctx, "delay": 1, "budget": 10_000,
              "label_price": 0.0, "switch_cost": 0.0}
    nat = CAMSNative(n_models=M, n_classes=3, advice_fn=toy_advice(M), rng=np.random.default_rng(9))
    ada = CAMSDeploymentAdapter(
        n_models=M, n_classes=3, advice_fn=toy_advice(M), rng=np.random.default_rng(9),
        deploy="sample",
    )
    a, b = run_episode(nat, **kw), run_episode(ada, **kw)
    assert [r["deployed_model"] for r in a.records] == [r["deployed_model"] for r in b.records]
    assert [r["requested"] for r in a.records] == [r["requested"] for r in b.records]


# ---------------------------------------------------------------------------------------------
# 6. numerical agreement with the author code (skipped if vendor_sota/ is absent: it is gitignored)
# ---------------------------------------------------------------------------------------------
def _load_author_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _AuthorData:
    pass


@pytest.mark.skipif(not (VENDOR / "src/methods/CAMS_identity.py").exists(), reason="no vendor_sota")
@pytest.mark.parametrize("variant,fname,fn", [
    ("CAMS", "CAMS_identity.py", "CAMS_identity"),
    ("CAMS-MAX", "CAMS_test.py", "CAMS_test"),
])
@pytest.mark.parametrize("seed,budget", [(0, 12), (1, 30), (2, 1000)])
def test_port_matches_author_code_numerically(variant, fname, fn, seed, budget, monkeypatch):
    # The author code stores ``binomial(size=1, ...)`` (a 1-element array) into a scalar slot,
    # which the installed NumPy rejects. Shim: the same draw returned as a scalar. The stream is
    # identical (a size-1 draw and a scalar draw consume the same bits).
    orig_binomial = np.random.binomial
    monkeypatch.setattr(
        np.random, "binomial", lambda size=None, n=1, p=0.5: orig_binomial(n, p)
    )
    d = VENDOR / "resources/contextual_data/VERTEBRAL"
    advice = np.load(d / "advice_matrix_identity.npz")["advice_matrix"][:, :12, :]
    preds = np.loadtxt(d / "predictions.out")
    oracle = np.loadtxt(d / "oracle.out")
    T = advice.shape[0]

    data = _AuthorData()
    data._num_classes = len(np.unique(oracle))
    data._num_models = preds.shape[1]
    data._num_policies_identity = advice.shape[1]
    data._num_instances = T
    data._budgets = [budget]
    data._predictions = preds
    data._oracle = oracle
    data._advice_matrix_identity = advice

    saved = {k: sys.modules.get(k) for k in ("config", "utils")}
    try:
        sys.modules["config"] = _load_author_module(VENDOR / "config.py", "config")
        sys.modules["utils"] = _load_author_module(VENDOR / "utils.py", "utils")
        mod = _load_author_module(VENDOR / "src/methods" / fname, f"author_{fn}")
        np.random.seed(seed)
        stream = np.arange(T)
        out = getattr(mod, fn)(data, 0, stream, 0, "Variance")
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    author_budgeted, author_hidden, author_w = out[2], out[3], out[4]

    pol = CAMSNative(
        n_models=data._num_models, n_classes=data._num_classes,
        advice_fn=lambda ev: advice[ev.t], rng=np.random.RandomState(seed), variant=variant,
    )
    res = run_episode(
        pol, model_predictions=preds.astype(int), labels=oracle.astype(int), delay=1,
        budget=budget, label_price=0.0, switch_cost=0.0,
    )
    mine_w = np.vstack([tr["w"] for tr in pol.core.trace])
    np.testing.assert_allclose(mine_w, author_w, atol=1e-12, rtol=0)
    assert [r["requested"] for r in res.records] == list(author_budgeted)
    mine_hidden = [
        int(preds[r["event_id"], r["deployed_model"]] != oracle[r["event_id"]]) for r in res.records
    ]
    assert mine_hidden == list(author_hidden)
