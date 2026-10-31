import numpy as np
import pytest

from shiftlab.dive.atlas_r6_baselines import R6_METHODS, build_r6
from shiftlab.dive.switching_explore import (
    Config,
    Stream,
    build_method,
    make_bernoulli_stream,
    run,
)

NAMES = list(R6_METHODS)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("d", [1, 10])
@pytest.mark.parametrize("B", [15, 75])
def test_runs_within_budget(name, d, B):
    cfg = Config(T=300, B=B, d=d, seed=3)
    for seed in range(3):
        st = make_bernoulli_stream(np.random.default_rng(seed), 300, (0.1, 0.9))
        r = run(st, build_r6(name, cfg), cfg)
        assert r.queries <= B


@pytest.mark.parametrize("name", NAMES)
def test_non_peeking(name):
    T, d, t0 = 300, 10, 150
    cfg = Config(T=T, B=30, d=d, seed=5)
    for seed in range(3):
        st = make_bernoulli_stream(np.random.default_rng(seed), T, (0.1, 0.9))
        y = st.loss0.copy()
        y[t0:] = 1.0 - y[t0:]  # flip outcomes of rounds > t0
        st2 = Stream(y, 1.0 - y, st.truth)
        a = run(st, build_r6(name, cfg), cfg)
        b = run(st2, build_r6(name, cfg), cfg)
        # labels of rounds > t0 are released at >= t0 + 1 + d, so decisions through t0 + d are blind
        assert np.array_equal(a.actions[: t0 + d], b.actions[: t0 + d])
        assert np.array_equal(a.query_mask[: t0 + d], b.query_mask[: t0 + d])


@pytest.mark.parametrize("name", NAMES)
def test_strong_favourable(name):
    T = 300
    path = np.ones(T, dtype=int)
    diffs, promos = [], 0
    for seed in range(10):
        c = Config(T=T, B=30, d=10, seed=seed)
        st = make_bernoulli_stream(np.random.default_rng(seed), T, (0.1, 0.9), path=path)
        r = run(st, build_r6(name, c), c)
        base = run(st, build_method("no_switch"), c)
        diffs.append(r.cost - base.cost)
        promos += r.promotions
    print(name, "mean cost minus no_switch", float(np.mean(diffs)))
    assert promos > 0
    assert np.mean(diffs) < 0


def test_fwer_boundary_null():
    T, h, alpha, n = 300, 0.1, 0.1, 200
    p = (1 + h) / 2
    path = np.zeros(T, dtype=int)
    hits = 0
    for seed in range(n):
        c = Config(T=T, B=30, d=10, h=h, alpha=alpha, seed=seed)
        st = make_bernoulli_stream(np.random.default_rng(1000 + seed), T, (p, p), path=path)
        hits += run(st, build_r6("online_fwer_spending", c), c).promotions > 0
    rate = hits / n
    sd = (alpha * (1 - alpha) / n) ** 0.5
    print("fwer boundary-null any-promotion rate", rate, "limit", alpha + 2 * sd)
    assert rate <= alpha + 2 * sd


def test_hard_budget_pacing_is_ungated_and_tracks_linear_target():
    assert R6_METHODS["hard_budget_pacing"][1] is False
    T, B, d = 400, 40, 5
    spent = []
    for seed in range(5):
        c = Config(T=T, B=B, d=d, seed=seed)
        st = make_bernoulli_stream(np.random.default_rng(seed), T, (0.1, 0.9))
        r = run(st, build_r6("hard_budget_pacing", c), c)
        assert r.queries <= B and r.query_mask[T - d :].sum() == 0
        spent.append(r.queries)
        half = r.query_mask[: (T - d) // 2].sum()
        assert abs(half - B / 2) <= 0.25 * B  # spend stays near the linear target
    assert np.mean(spent) > 0.8 * B  # and it actually spends the budget
