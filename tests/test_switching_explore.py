"""CPU-fast checks for the exploratory C1/C2 harness (R4: development only)."""

from itertools import product

import numpy as np
import pytest

from shiftlab.dive.switching_explore import (
    BASELINES,
    BankSpec,
    BudgetExceeded,
    Config,
    HMMBank,
    Method,
    Stream,
    Truth,
    bernoulli_grid_spec,
    build_method,
    make_bernoulli_stream,
    make_scenario_stream,
    run,
    score_actions,
    uniform_calendar,
)

SPEC = bernoulli_grid_spec(rates=(0.03, 0.25), pairs=((0.1, 0.9), (0.5, 0.5), (0.3, 0.3)))
ALL = (*BASELINES, "c1_hmm_cs", "c2_rho0.25", "c2_rho0.5", "c2_rho0.75")


def _flip(stream: Stream, mask: np.ndarray) -> Stream:
    l0, l1 = stream.loss0.copy(), stream.loss1.copy()
    l0[mask], l1[mask] = 1.0 - l0[mask], 1.0 - l1[mask]
    return Stream(l0, l1, None)


@pytest.mark.parametrize("name", ALL)
@pytest.mark.parametrize("d,B", [(1, 12), (10, 25)])
def test_budget_never_exceeded_including_pending(name, d, B):
    T = 100
    for seed in range(3):
        stream = make_scenario_stream("persistent_std", 200, seed)
        stream = Stream(stream.loss0[:T], stream.loss1[:T], None)
        cfg = Config(T=T, B=B, d=d, seed=seed)
        r = run(stream, build_method(name, SPEC), cfg)
        assert r.queries <= B  # counted at request time, so unreleased requests are included
        assert int(r.query_mask.sum()) == r.queries
        assert r.wasted_queries <= r.queries


def test_harness_rejects_over_budget_request():
    class Greedy(Method):
        def decide(self, t, released):
            return 0, True

        def can_query(self, t):  # rogue: ignore the guard so the harness must catch it
            return True

    stream = make_scenario_stream("null_boundary", 30, 0)
    with pytest.raises(BudgetExceeded):
        run(stream, Greedy(), Config(T=30, B=5, d=3))


@pytest.mark.parametrize("name", ALL)
def test_decisions_use_only_released_labels(name):
    """Altering any outcome not yet released at round t* (including round t* itself) or never queried
    cannot change actions/queries through t*; hence the action at t is predictable."""
    T, d = 120, 7
    base = make_scenario_stream("reversal", T, 3)
    cfg = Config(T=T, B=30, d=d, seed=3)
    ref = run(base, build_method(name, SPEC), cfg)
    for t_star in (20, 55, 90):
        mask = np.zeros(T, dtype=bool)
        mask[t_star - d :] = (
            True  # rounds s with s + d > t* - ... i.e. unreleased by the start of t*
        )
        mask[: t_star - d] = False
        alt = run(_flip(base, mask), build_method(name, SPEC), cfg)
        assert np.array_equal(alt.actions[:t_star], ref.actions[:t_star])
        assert np.array_equal(alt.query_mask[:t_star], ref.query_mask[:t_star])
    # unqueried rounds never reach the method at all
    unq = ref.query_mask == 0
    alt = run(_flip(base, unq), build_method(name, SPEC), cfg)
    assert np.array_equal(alt.actions, ref.actions)
    assert np.array_equal(alt.query_mask, ref.query_mask)


@pytest.mark.parametrize("name", ALL)
def test_oracle_truth_not_visible_to_methods(name):
    T = 80
    s0 = make_scenario_stream("persistent_std", T, 5)
    cfg = Config(T=T, B=20, d=3, seed=5)
    a = run(s0, build_method(name, SPEC), cfg)
    junk = Stream(s0.loss0, s0.loss1, Truth(np.full(T, 123.0), np.ones(T, dtype=int), None))
    b = run(junk, build_method(name, SPEC), cfg)
    c = run(Stream(s0.loss0, s0.loss1, None), build_method(name, SPEC), cfg)
    assert np.array_equal(a.actions, b.actions) and np.array_equal(a.actions, c.actions)
    assert np.array_equal(a.query_mask, b.query_mask)


def test_methods_receive_only_released_pairs():
    seen = []

    class Spy(Method):
        def decide(self, t, released):
            seen.append((t, released))
            return 0, t % 4 == 1

    T, d = 40, 5
    stream = make_scenario_stream("persistent_std", T, 1)
    run(stream, Spy(), Config(T=T, B=10, d=d))
    for t, rel in seen:
        for ev, val in rel:
            assert ev + d == t and ev % 4 == 1
            assert type(ev) is int and type(val) is float
            assert val == stream.D[ev - 1]


def test_hmm_filter_matches_bruteforce_likelihood_with_gaps_and_pending():
    spec = BankSpec(
        "bernoulli",
        np.array([0.2]),
        np.array([0.3]),
        1 - 2 * np.array([[0.1, 0.8]]),
        p=np.array([[0.1, 0.8]]),
    )
    bank = HMMBank(spec, prior1=0.4)
    obs = {2: 1, 3: 0, 7: 1}  # queried events -> Y (D = 1 - 2Y)
    for ev, y in obs.items():
        bank.update(ev, 1.0 - 2.0 * y)
    a, b, p = 0.2, 0.3, (0.1, 0.8)
    total = 0.0
    for path in product((0, 1), repeat=7):  # S_1..S_7; S_0 ~ prior
        for s0 in (0, 1):
            pr = 0.4 if s0 else 0.6
            prev = s0
            for s in path:
                flip = a if prev == 0 else b
                pr *= flip if s != prev else 1 - flip
                prev = s
            for ev, y in obs.items():
                q = p[path[ev - 1]]
                pr *= q if y else 1 - q
            total += pr
    assert bank.log_l[0] == pytest.approx(np.log(total), rel=1e-12)


def test_false_promotion_sanity_on_small_null_cell():
    """Boundary null (mean D = 0 >= -h): every promotion is false. Gate-based methods should be rare."""
    n, T, alpha = 150, 60, 0.1
    hits = {k: 0 for k in ("c1_hmm_cs", "c2_rho0.5", "episode_geo", "allonset_edetector")}
    pred_flag = 0
    for seed in range(n):
        rng = np.random.default_rng([seed, 9])
        stream = make_bernoulli_stream(rng, T, (0.5, 0.5), a=0.03, b=0.03)
        cfg = Config(T=T, B=20, d=1, seed=seed, alpha=alpha)
        for k in hits:
            r = run(stream, build_method(k, SPEC), cfg)
            hits[k] += int(r.promotions > 0)
            if k == "c1_hmm_cs":
                pred_flag += int((r.fp_pred or 0) > 0)
                assert r.fp_regime == r.promotions  # all regimes are no-benefit here
    for k, v in hits.items():
        assert v / n <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n), (k, v)
    assert pred_flag / n <= alpha + 3 * np.sqrt(alpha * (1 - alpha) / n)


def test_score_and_false_promotion_accounting():
    T = 6
    y = np.array([0, 1, 1, 0, 1, 1], dtype=float)
    truth = Truth(np.array([0.5, -0.5, -0.5, 0.5, -0.5, -0.5]), None, None)
    stream = Stream(y, 1 - y, truth)
    cfg = Config(T=T, B=2, d=1, c=0.01, s=0.1, h=0.1)
    actions = np.array([0, 1, 1, 0, 1, 1])
    r = score_actions(stream, cfg, actions, np.array([1, 0, 0, 0, 1, 0], dtype=float))
    assert r.switches == 3 and r.promotions == 2 and r.queries == 2 and r.fp_regime == 0
    loss = (1 - y)[[1, 2, 4, 5]].sum() + y[[0, 3]].sum()
    assert r.cost == pytest.approx(loss + 0.02 + 0.3)
    bad = score_actions(stream, cfg, np.array([1, 0, 0, 0, 0, 0]), np.zeros(T))
    assert bad.fp_regime == 1  # promoted at round 1 where regime mean +0.5 >= -h


def test_uniform_calendar_is_releasable_and_within_budget():
    for T, B, d in [(50, 10, 3), (30, 40, 5), (10, 0, 1), (200, 50, 10)]:
        cal = uniform_calendar(T, B, d)
        assert len(cal) <= B and all(1 <= t <= T - d for t in cal)
