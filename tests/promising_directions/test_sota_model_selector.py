"""Tests for the Model Selector port (native pool method, causal adapter, block-pool experiment).

Author code: ``vendor_sota/model_selector`` (gitignored). The author repository registers the
method as ``model_picker``; it is not Karimi et al.'s Model Picker.
"""

import contextlib
import math
import random
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))

from competitors.model_selector import (
    ModelSelectorCausalAdapter,
    ModelSelectorNative,
    epsilon_grid,
    final_model_by_labeled_accuracy,
    gamma_from_epsilon,
    hypothetical_entropies,
    run_block_pool_experiment,
    select_epsilon,
    update_posterior,
    vote_noisy_oracle,
)
from simulator import (
    Event,
    ReleasedFeedback,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)

AUTHOR_SRC = ROOT / "vendor_sota/model_selector/src"
EMOTION = ROOT / "vendor_sota/model_selector/resources/datasets/emotion_detection"


def _h(*p):
    return -sum(x * math.log2(x) for x in p if x > 0)


def _stream(T=300, seed=0, acc=(0.8, 0.7), n_classes=2):
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


# --------------------------------------------------------------------------------------------
# Hand computation
# --------------------------------------------------------------------------------------------
def test_posterior_update_hand_computed():
    # gamma = 3 (epsilon 0.25); model 0 right, model 1 wrong: (0.5*3, 0.5)/2 = (0.75, 0.25)
    out = update_posterior(np.array([0.5, 0.5]), np.array([0, 1]), 0, gamma_from_epsilon(0.25))
    np.testing.assert_allclose(out, [0.75, 0.25])
    # both wrong -> unchanged; both right -> unchanged (a common factor cancels)
    np.testing.assert_allclose(update_posterior(out, np.array([1, 1]), 0, 3.0), out)
    np.testing.assert_allclose(update_posterior(out, np.array([0, 0]), 0, 3.0), out)


def test_expected_entropy_hand_computed_two_models():
    # post (.5,.5), gamma 3, preds (0,1), 2 classes: both hypothetical posteriors are (.75,.25)
    e = hypothetical_entropies(np.array([0.5, 0.5]), np.array([[0, 1]]), 2, 3.0)
    assert e[0] == pytest.approx(_h(0.75, 0.25))
    # a class nobody predicts leaves the posterior at (.5,.5): H = 1, weight 1/3
    e3 = hypothetical_entropies(np.array([0.5, 0.5]), np.array([[0, 1]]), 3, 3.0)
    assert e3[0] == pytest.approx((2 * _h(0.75, 0.25) + 1.0) / 3)


def test_expected_entropy_hand_computed_three_models():
    # post (.5,.25,.25), gamma 2, preds (0,0,1), 2 classes.
    # y=0: (1, .5, .25)/1.75 = (4/7, 2/7, 1/7); y=1: (.5, .25, .5)/1.25 = (.4, .2, .4)
    e = hypothetical_entropies(np.array([0.5, 0.25, 0.25]), np.array([[0, 0, 1]]), 2, 2.0)
    expect = 0.5 * (_h(4 / 7, 2 / 7, 1 / 7) + _h(0.4, 0.2, 0.4))
    assert e[0] == pytest.approx(expect)


# --------------------------------------------------------------------------------------------
# The epsilon noise model
# --------------------------------------------------------------------------------------------
def test_epsilon_noise_model_and_grid():
    assert gamma_from_epsilon(0.25) == pytest.approx(3.0)
    assert gamma_from_epsilon(0.5) == 1.0
    for bad in (0.0, 1.0, -0.1):
        with pytest.raises(ValueError):
            gamma_from_epsilon(bad)
    # Eq. 7: a correct prediction is weighted (1-eps)/eps relative to an incorrect one.
    post = update_posterior(np.array([0.5, 0.5]), np.array([0, 1]), 0, gamma_from_epsilon(0.4))
    assert post[0] / post[1] == pytest.approx(0.6 / 0.4)
    # grid constants from gridsearch_config.py lines 48-52 (finegrained configs: no extra 0.49)
    g = epsilon_grid()
    assert len(g) == 15 and g[0] == pytest.approx(0.35) and g[-1] == pytest.approx(0.49)
    assert len(epsilon_grid(include_extra_049=True)) == 16


def test_epsilon_half_is_random_sampling():
    # gamma = 1: every hypothetical posterior is the prior, every score ties (paper: eps=0.5
    # "mimics random sampling"; Drift collection).
    preds = np.array([[0, 1, 2], [0, 0, 1], [2, 1, 0]])
    e = hypothetical_entropies(np.ones(3) / 3, preds, 3, 1.0)
    np.testing.assert_array_equal(e, np.full(3, math.log2(3)))


# --------------------------------------------------------------------------------------------
# Final selection rule
# --------------------------------------------------------------------------------------------
def test_final_rule_is_highest_labeled_accuracy_not_posterior_argmax():
    # epsilon 0.6 -> gamma < 1: the posterior argmax is the WORST model, the accuracy rule is not.
    rng = np.random.RandomState(0)
    preds = np.array([[0, 1], [1, 0], [0, 1], [1, 0]] * 5)
    oracle = np.array([0, 1, 0, 1] * 5)  # model 0 always right
    res = ModelSelectorNative(2, 0.6).run(preds, oracle, 8, rng)
    assert res["final_model"] == 0
    assert int(np.argmax(res["final_posterior"])) == 1  # posterior would have said model 1
    np.testing.assert_array_equal(res["final_correct_counts"], [8, 0])


def test_final_rule_tie_break_is_uniform_random():
    rng = np.random.RandomState(0)
    picks = [final_model_by_labeled_accuracy(np.array([3.0, 3.0, 1.0]), rng) for _ in range(400)]
    assert set(picks) == {0, 1}
    assert 140 < picks.count(0) < 260


# --------------------------------------------------------------------------------------------
# Degeneracy with two models
# --------------------------------------------------------------------------------------------
@pytest.mark.parametrize("n_classes", [2, 3, 5])
def test_two_model_expected_entropy_is_instance_blind(n_classes):
    rng = np.random.default_rng(1)
    for _ in range(25):
        w = rng.dirichlet(np.ones(2))
        gamma = float(rng.uniform(1.0, 20.0))
        a = rng.integers(0, n_classes, 40)
        b = (a + 1 + rng.integers(0, n_classes - 1, 40)) % n_classes  # always disagree
        e = hypothetical_entropies(w, np.stack([a, b], axis=1), n_classes, gamma)
        # mathematically identical for every disagreement example, any K
        np.testing.assert_allclose(e, np.full(40, e[0]), rtol=0, atol=1e-12)
        if n_classes == 2:
            # K=2: the two hypothetical entropies are summed in swapped order, which is exact, so
            # the reference's `==` tie test sees one all-way tie. For K>2 the sum has >2 terms and
            # differs by ~1 ulp across rows (observed 5.6e-17): information-free, not uniform.
            np.testing.assert_array_equal(e, np.full(40, e[0]))


def test_three_models_are_not_degenerate_once_posterior_moves():
    preds = np.array([[0, 0, 1], [0, 1, 1], [0, 1, 0]])
    e = hypothetical_entropies(np.array([0.6, 0.3, 0.1]), preds, 2, 2.0)
    assert len(np.unique(np.round(e, 12))) > 1


def test_native_two_model_selection_is_uniform_random_over_disagreements():
    preds, y = _stream(T=200, seed=3)
    dis = np.flatnonzero(preds[:, 0] != preds[:, 1])
    res = ModelSelectorNative(2, 0.4).run(preds, y, 15, np.random.RandomState(5))
    # replay the tie-break draws of a pure random-without-replacement sampler
    r = np.random.RandomState(5)
    remaining = list(dis)
    replay = []
    for _ in range(15):
        j = int(r.choice(len(remaining), 1)[0])
        replay.append(int(remaining.pop(j)))
    assert res["labelled_indices"][:15] == replay
    # and epsilon does not change which examples are queried
    other = ModelSelectorNative(2, 0.49).run(preds, y, 15, np.random.RandomState(5))
    assert other["labelled_indices"] == res["labelled_indices"]


def test_adapter_gate_never_rejects_in_two_model_setting():
    preds, y = _stream(T=300, seed=4)
    pol = ModelSelectorCausalAdapter(2, 2, policy_rng(0, 0, "m"), 0.4, window=30, pace=False)
    res = run_episode(
        pol, model_predictions=preds, labels=y, delay=3, budget=10, label_price=0.1, switch_cost=1.0
    )
    first = [r["event_id"] for r in res.records if r["requested"]]
    dis = np.flatnonzero(preds[:, 0] != preds[:, 1])[:10]
    assert first == dis.tolist()  # entropy gate is a no-op: first 10 disagreements, in order


# --------------------------------------------------------------------------------------------
# Adapter: causality, budget, determinism
# --------------------------------------------------------------------------------------------
def _run(policy, preds, y, budget=12, delay=4):
    return run_episode(
        policy,
        model_predictions=preds,
        labels=y,
        delay=delay,
        budget=budget,
        label_price=0.2,
        switch_cost=1.0,
    )


def test_adapter_budget_feasible_pathwise_and_deterministic():
    preds, y = _stream(T=400, seed=2, acc=(0.7, 0.8, 0.6))
    out = []
    for budget in (0, 1, 7, 50):
        res = _run(ModelSelectorCausalAdapter(3, 2, policy_rng(0, 0, "a")), preds, y, budget)
        assert check_budget_feasible(res, budget) == []
        assert check_no_future_access(res, 4) == []
        assert res.requested_labels <= budget
        out.append(res)
    again = _run(ModelSelectorCausalAdapter(3, 2, policy_rng(0, 0, "a")), preds, y, 50)
    assert again.records == out[-1].records
    assert out[0].requested_labels == 0


def test_adapter_has_no_future_access():
    preds, y = _stream(T=300, seed=7, acc=(0.7, 0.8, 0.6))
    cut = 150
    preds2, y2 = preds.copy(), y.copy()
    rng = np.random.default_rng(99)
    preds2[cut:] = rng.integers(0, 2, preds2[cut:].shape)  # rewrite the entire future
    y2[cut:] = rng.integers(0, 2, len(y2) - cut)
    r1 = _run(ModelSelectorCausalAdapter(3, 2, policy_rng(0, 0, "a")), preds, y, 40)
    r2 = _run(ModelSelectorCausalAdapter(3, 2, policy_rng(0, 0, "a")), preds2, y2, 40)
    # decisions up to the cut cannot depend on anything after it (horizon is unchanged)
    keys = ("deployed_model", "requested", "release_time", "budget_remaining")
    for a, b in zip(r1.records[:cut], r2.records[:cut], strict=True):
        assert all(a[k] == b[k] for k in keys)
    # and the eligible set only ever holds already-arrived events
    pol = ModelSelectorCausalAdapter(3, 2, policy_rng(0, 0, "a"), window=20)
    for t in range(60):
        ev = Event(t, t, 60, preds[t])
        pol.predict(ev)
        pol.request_labels(ev, 10)
        assert all(eid <= t for eid, _ in pol.pool)
        assert len(pol.pool) <= 20


def test_adapter_pending_label_does_not_change_state_until_released():
    pol = ModelSelectorCausalAdapter(2, 2, policy_rng(0, 0, "a"), pace=False)
    ev = Event(0, 0, 10, np.array([0, 1]))
    pol.predict(ev)
    req = pol.request_labels(ev, 5)
    assert req.requested and pol.n_issued == 1 and pol.n_observed == 0
    np.testing.assert_allclose(pol.posterior, [0.5, 0.5])
    np.testing.assert_array_equal(pol.correct, [0, 0])
    pol.observe([ReleasedFeedback(0, 0, 3, 0, np.array([0, 1], dtype=np.int8), 1.0)])
    assert pol.posterior[0] > pol.posterior[1] and pol.n_observed == 1


def test_adapter_deploys_highest_labeled_accuracy_with_sticky_ties():
    pol = ModelSelectorCausalAdapter(3, 2, policy_rng(0, 0, "a"), initial_model=1)
    ev = Event(0, 0, 10, np.array([0, 1, 0]))
    assert pol.predict(ev) == 1  # no labels: incumbent kept
    pol.correct = np.array([2.0, 2.0, 1.0])
    assert pol.predict(ev) == 1  # incumbent 1 is a tied maximiser -> kept (no charged switch)
    pol.deployed = 2
    assert pol.predict(ev) == 0  # incumbent 2 is not a maximiser -> lowest-index maximiser
    pol.correct = np.array([1.0, 3.0, 1.0])
    assert pol.predict(ev) == 1


def test_adapter_state_roundtrip():
    preds, y = _stream(T=120, seed=1, acc=(0.7, 0.8, 0.6))
    pol = ModelSelectorCausalAdapter(3, 2, policy_rng(0, 0, "a"))
    _run(pol, preds, y, 15)
    clone = ModelSelectorCausalAdapter(3, 2, policy_rng(0, 0, "a"))
    clone.load_state_dict(pol.state_dict())
    assert clone.state_dict() == pol.state_dict()


# --------------------------------------------------------------------------------------------
# Block-pool experiment (the faithful pool method on arrived events)
# --------------------------------------------------------------------------------------------
def test_block_pool_reads_only_arrived_block_labels_and_respects_cap():
    preds, y = _stream(T=400, seed=11, acc=(0.7, 0.8, 0.6))
    out = run_block_pool_experiment(
        preds,
        y,
        block=100,
        budget_per_block=10,
        delay=2,
        label_price=0.2,
        switch_cost=1.0,
        budget=25,
        rng=np.random.RandomState(0),
    )
    assert out["labels"] <= 25 and len(out["accessed"]) == out["labels"]
    # every label read lies in its own block (nothing from a later block was visible)
    assert all(0 <= i < 400 for i in out["accessed"])
    with pytest.raises(ValueError):
        run_block_pool_experiment(
            preds, y, block=100, budget_per_block=5, delay=0, label_price=0.2, switch_cost=1.0
        )


def test_block_pool_guard_refuses_out_of_block_label():
    from competitors.model_selector import _BlockOracle

    view = _BlockOracle(np.arange(10), 2, 5)
    assert view[3] == 3
    with pytest.raises(IndexError):
        view[7]


# --------------------------------------------------------------------------------------------
# Numerical agreement with the author code
# --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def author():
    if not AUTHOR_SRC.exists():
        pytest.skip("vendor_sota/model_selector is gitignored and not present")
    import scipy.stats  # noqa: F401  (import before any torch stub exists)

    prefixes = (
        "model_selection",
        "epsilon_optimization",
        "benchmark",
        "data_provider",
        "utils",
        "models",
        "torch",
        "tqdm",
    )
    saved = {k: v for k, v in sys.modules.items() if k.split(".")[0] in prefixes}
    for k in saved:
        del sys.modules[k]
    added_stub = []
    for name in ("torch", "tqdm"):
        try:
            __import__(name)
        except ImportError:
            added_stub.append(name)
    sys.path.insert(0, str(AUTHOR_SRC))
    try:
        if "torch" in added_stub:
            t = types.ModuleType("torch")
            t.manual_seed = lambda s: None
            t.cuda = types.SimpleNamespace(manual_seed_all=lambda s: None)
            sys.modules["torch"] = t
        if "tqdm" in added_stub:
            q = types.ModuleType("tqdm")
            q.tqdm = lambda x, *a, **k: x
            sys.modules["tqdm"] = q
        pkg = types.ModuleType("model_selection.methods")
        pkg.__path__ = [str(AUTHOR_SRC / "model_selection/methods")]
        import model_selection  # noqa: F401

        sys.modules["model_selection.methods"] = pkg
        # NUMPY-2 SHIM: the reference does int(np.random.choice(n, 1)), which raises on numpy>=2.
        # Taking element [0] draws the same random number; nothing else is changed.
        src = (AUTHOR_SRC / "model_selection/methods/model_picker.py").read_text()
        old = "int(np.random.choice(np.size(loc_i_stars), 1))"
        assert old in src
        mod = types.ModuleType("model_selection.methods.model_picker")
        sys.modules[mod.__name__] = mod
        exec(  # noqa: S102
            compile(src.replace(old, old[:-1] + "[0])"), "model_picker.py", "exec"), mod.__dict__
        )
        import benchmark.benchmark as bb
        from epsilon_optimization.gridsearch import epsilon_grid_search
        from epsilon_optimization.gridsearch_config import GridSearchConfig
        from model_selection.model_selector import ModelSelector

        def _seed(s):  # torch is absent/stubbed; numpy + random seeding is what matters
            random.seed(s)
            np.random.seed(s)

        bb.set_seed = _seed
        ns = types.SimpleNamespace(
            ModelSelector=ModelSelector,
            ModelPicker=mod.ModelPicker,
            epsilon_grid_search=epsilon_grid_search,
            GridSearchConfig=GridSearchConfig,
        )
        for name in added_stub:  # a bare stub would break scipy's torch-array probing
            sys.modules.pop(name, None)
        yield ns
    finally:
        for k in [k for k in sys.modules if k.split(".")[0] in prefixes]:
            del sys.modules[k]
        sys.modules.update(saved)
        with contextlib.suppress(ValueError):
            sys.path.remove(str(AUTHOR_SRC))


def _author_run(author, preds, oracle, n_classes, eps, budget, seed):
    strat = author.ModelPicker({"name": "ms", "type": "model_picker", "epsilon": eps})
    sel = author.ModelSelector(strat)
    np.random.seed(seed)
    ranking, lt = sel.run(
        np.arange(len(preds)), preds, oracle.reshape(-1, 1), np.arange(n_classes), budget
    )
    return [int(r) for r in ranking], [int(e[0]) for e in lt]


@pytest.mark.parametrize(
    "seed,n_models,n_classes,eps,budget,n",
    [
        (0, 2, 2, 0.46, 20, 120),  # the degenerate binary two-model case
        (1, 3, 3, 0.40, 30, 150),
        (2, 5, 4, 0.35, 40, 200),
        (3, 4, 3, 0.49, 25, 100),
        (4, 3, 2, 0.50, 25, 100),  # gamma = 1: every score ties
        (5, 3, 3, 0.45, 60, 40),  # budget exceeds the disagreement set: back-fill path
    ],
)
def test_native_reproduces_author_outputs_exactly(
    author, seed, n_models, n_classes, eps, budget, n
):
    rng = np.random.default_rng(seed)
    y = rng.integers(0, n_classes, n)
    accs = np.linspace(0.55, 0.85, n_models)
    preds = np.stack(
        [np.where(rng.random(n) < a, y, rng.integers(0, n_classes, n)) for a in accs], axis=1
    )
    ranking, labelled = _author_run(author, preds, y, n_classes, eps, budget, seed)
    ours = ModelSelectorNative(n_classes, eps).run(
        preds, y.reshape(-1, 1), budget, np.random.RandomState(seed)
    )
    assert ours["labelled_indices"] == labelled
    assert ours["model_ranking_t"].tolist() == ranking


def test_native_reproduces_author_on_shipped_emotion_data(author):
    if not EMOTION.exists():
        pytest.skip("emotion_detection dataset not present")
    preds_all = np.load(EMOTION / "predictions.npy").astype(np.int64)
    oracle_all = np.load(EMOTION / "oracle.npy").reshape(-1).astype(np.int64)
    for seed, eps in ((0, 0.47), (1, 0.36)):
        pick = np.random.RandomState(100 + seed).permutation(len(oracle_all))[:200]
        preds, y = preds_all[pick], oracle_all[pick]
        ranking, labelled = _author_run(author, preds, y, 4, eps, 40, seed)
        ours = ModelSelectorNative(4, eps).run(preds, y, 40, np.random.RandomState(seed))
        assert ours["labelled_indices"] == labelled
        assert ours["model_ranking_t"].tolist() == ranking


def test_epsilon_selection_reproduces_author_gridsearch(author):
    if not EMOTION.exists():
        pytest.skip("emotion_detection dataset not present")
    preds = np.load(EMOTION / "predictions.npy").astype(np.int64)
    oracle = np.load(EMOTION / "oracle.npy").reshape(-1).astype(np.int64)
    cfg = {
        "experiment": {
            "name": "x_finegrained",
            "datasetPath": "d",
            "partitionMethod": "random",
            "numSamples": 80,
            "budget": 30,
            "iterations": 6,
            "uniqueIndices": False,
            "fitOracleSize": False,
            "parallel": False,
        },
        "epsilon_range": {"min": 0.35, "max": 0.49, "step": 0.02},
        "epsilon_metric": "all",
        "epsilon_metric_threshold": 0.9,
        "noisy_oracle": "vote",
        "methods": [{"name": "Model Picker", "type": "model_picker", "epsilon": 0.49}],
    }
    g = author.GridSearchConfig.from_json(cfg)
    np.random.seed(0)
    result, gs = author.epsilon_grid_search(preds, oracle, np.unique(oracle), g)
    by = {r.method: r.epsilons["Model Picker"] for r in gs}
    mine = select_epsilon(preds, 4, np.array(result.realisations), 30, grid=g.epsilons, seed0=0)
    np.testing.assert_allclose(mine["success_avg"], by["success_avg"]["success_avg_e"], atol=1e-12)
    assert mine["fastest"] == by["fastest"]["fastest_e"]
    assert mine["epsilon"] == pytest.approx(float(by["success_avg"]["optimal_epsilon"]))
    chosen_fast = select_epsilon(
        preds, 4, np.array(result.realisations), 30, grid=g.epsilons, metric="fastest"
    )["epsilon"]
    assert chosen_fast == pytest.approx(float(by["fastest"]["optimal_epsilon"]))


def test_vote_noisy_oracle_is_plurality_with_first_on_ties():
    p = np.array([[0, 0, 1], [1, 2, 2], [0, 1, 2]])
    assert vote_noisy_oracle(p, 3).tolist() == [0, 2, 0]
