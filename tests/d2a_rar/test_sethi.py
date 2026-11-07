"""Tests for the Sethi et al. (ICML 2026) PAPER_RECONSTRUCTION. CPU-small Monte Carlo."""

import math

import numpy as np
import pytest
from scipy.optimize import minimize

from shiftlab.sota.sethi import (
    ConvexHullNull,
    FiniteUnionNull,
    SequentialMarkovTest,
    StationaryNull,
    beta_t,
    boundary,
)

PI5 = np.array([0.1, 0.1, 0.2, 0.2, 0.4])
# Appendix G.1 matrices (Q_good has pi as stationary law; Q_bad does not)
QGOOD = np.array(
    [
        [0.5, 0.2, 0, 0, 0.3],
        [0.2, 0.5, 0.3, 0, 0],
        [0, 0.15, 0.5, 0.35, 0],
        [0, 0, 0.35, 0.5, 0.15],
        [0.075, 0, 0, 0.075, 0.85],
    ]
)
QBAD = np.array(
    [
        [0.1, 0.5, 0.1, 0.1, 0.2],
        [0.2, 0.1, 0.4, 0.2, 0.1],
        [0.1, 0.1, 0.1, 0.6, 0.1],
        [0.3, 0.2, 0.1, 0.1, 0.3],
        [0.1, 0.1, 0.1, 0.1, 0.6],
    ]
)


def _stream(Q, T, rng, x0=None):
    m = len(Q)
    x = int(rng.integers(m)) if x0 is None else x0
    yield x
    for _ in range(T):
        x = int(rng.choice(m, p=Q[x]))
        yield x


def _run(test, Q, T, rng, x0=None):
    for x in _stream(Q, T, rng, x0):
        if test.update(x):
            return test.rejected_at
    return None


def test_boundary_formula():
    N = np.array([3.0, 0.0, 7.0])
    m = 3
    b = sum(math.log(math.e * (1 + n / (m - 1))) for n in N)
    assert beta_t(N, m) == pytest.approx(b)
    assert boundary(N, m, 0.05) == pytest.approx(math.log(20) + (m - 1) * b)


def test_stationary_fixtures():
    assert np.allclose(PI5 @ QGOOD, PI5)
    assert not np.allclose(PI5 @ QBAD, PI5)


def test_dual_lower_bound_matches_primal():
    rng = np.random.default_rng(1)
    for _ in range(3):
        N = np.zeros((5, 5))
        for a, b in zip(*[iter(list(_stream(QBAD, 400, rng)))] * 2, strict=False):
            N[a, b] += 1
        null = StationaryNull(PI5)
        up = null.bounds(N)[1]
        lo = min(null._dual(N), up)  # the dual lower bound itself
        q = N / N.sum(1, keepdims=True)
        c = np.sum(N[N > 0] * np.log(q[N > 0]))

        def f(v):
            return -np.sum(N * np.log(np.maximum(v.reshape(5, 5), 1e-12)))  # noqa: B023 (closure used immediately)

        cons = [
            {"type": "eq", "fun": lambda v: v.reshape(5, 5).sum(1) - 1},
            {"type": "eq", "fun": lambda v: (PI5 @ v.reshape(5, 5) - PI5)[:-1]},
        ]
        r = minimize(
            f,
            np.tile(PI5, (5, 1)).ravel(),
            constraints=cons,
            bounds=[(1e-9, 1)] * 25,
            method="SLSQP",
            options={"maxiter": 500},
        )
        assert lo <= up + 1e-9
        assert lo <= c + r.fun + 1e-4  # weak duality: never above the primal optimum
        assert lo >= c + r.fun - 1e-2  # and tight on this convex problem


def test_alpha_correct_null_tight_boundary_chain():
    """Null kernel QGOOD (zeros on the boundary of the class), several initial laws.
    Paper bound: P(reject ever) <= alpha. We use alpha=0.2 to give the bound a chance to bind."""
    alpha, reps, T = 0.2, 60, 600
    rng = np.random.default_rng(0)
    rej = 0
    for r in range(reps):
        test = SequentialMarkovTest(5, alpha, StationaryNull(PI5), check_every=40)
        rej += _run(test, QGOOD, T, rng, x0=r % 5) is not None
    rate = rej / reps
    se = math.sqrt(alpha * (1 - alpha) / reps)
    assert rate <= alpha + 3 * se, rate


def test_alpha_correct_null_two_state_iid_and_sticky():
    """Small-m null with a loose class: all kernels with stationary law (.5,.5); members include iid and sticky chains."""
    alpha, reps, T = 0.5, 80, 200
    null = StationaryNull(np.array([0.5, 0.5]))
    rng = np.random.default_rng(3)
    for Q in (
        np.full((2, 2), 0.5),
        np.array([[0.9, 0.1], [0.1, 0.9]]),
        np.array([[0.0, 1.0], [1.0, 0.0]]),
    ):
        rej = 0
        for _ in range(reps):
            test = SequentialMarkovTest(2, alpha, null, check_every=20)
            rej += _run(test, Q, T, rng) is not None
        se = math.sqrt(alpha * (1 - alpha) / reps)
        assert rej / reps <= alpha + 3 * se, (Q, rej / reps)


def test_convex_hull_null_alpha_and_power():
    K = [np.array([[0.8, 0.2], [0.2, 0.8]]), np.array([[0.3, 0.7], [0.6, 0.4]])]
    null = ConvexHullNull(K)
    rng = np.random.default_rng(5)
    alpha, reps = 0.3, 100
    rej = 0
    for _ in range(reps):
        test = SequentialMarkovTest(2, alpha, null, check_every=5)
        rej += _run(test, 0.5 * K[0] + 0.5 * K[1], 400, rng) is not None
    assert rej / reps <= alpha + 3 * math.sqrt(alpha * (1 - alpha) / reps)
    # power: a kernel outside the hull is eventually rejected
    Qout = np.array([[0.05, 0.95], [0.95, 0.05]])
    stops = [
        _run(SequentialMarkovTest(2, 0.05, null, check_every=5), Qout, 3000, rng) for _ in range(10)
    ]
    assert all(s is not None for s in stops)


def test_finite_union_min():
    a, b = (
        StationaryNull(np.array([0.5, 0.5])),
        ConvexHullNull([np.array([[0.8, 0.2], [0.2, 0.8]])]),
    )
    N = np.array([[10.0, 30.0], [30.0, 10.0]])
    lo, up = FiniteUnionNull([a, b]).bounds(N)
    assert lo <= min(a.bounds(N)[1], b.bounds(N)[1]) + 1e-9 and up == pytest.approx(
        min(a.bounds(N)[1], b.bounds(N)[1])
    )


def test_power_bad_chain_and_evidence():
    rng = np.random.default_rng(2)
    test = SequentialMarkovTest(5, 0.05, StationaryNull(PI5), check_every=50)
    tau = _run(test, QBAD, 8000, rng)
    assert tau is not None
    assert test.log_evidence() >= math.log(1 / 0.05) - 1e-9
    # stopping time scales with log(1/alpha): larger alpha stops no later on the same path
    rng = np.random.default_rng(2)
    t2 = SequentialMarkovTest(5, 0.4, StationaryNull(PI5), check_every=50)
    tau2 = _run(t2, QBAD, 8000, rng)
    assert tau2 is not None and tau2 <= tau


def test_no_lookahead_and_empty_rows():
    t = SequentialMarkovTest(3, 0.05, StationaryNull(np.ones(3) / 3))
    assert t.update(0) is False and t.t == 0 and t.N.sum() == 0  # X_0 creates no count
    t.update(1)
    assert t.N.sum() == 1 and t.N[0, 1] == 1
    assert np.isfinite(beta_t(t.N.sum(1), 3))  # rows with N_x = 0 are harmless


def test_common_contract_adapter_runs_and_passes_audit():
    """COMMON_CONTRACT_PORT smoke: audited paired run on a dev family (integrity only, no performance claim)."""
    from shiftlab.bench.contract import (
        BudgetSpec,
        ClockSpec,
        EnvSpec,
        load_cost_vectors,
        load_family,
        run_paired,
    )
    from shiftlab.bench.contract.adapters_sethi import SethiAdapter

    spec = load_family("iid_shift_d10")
    env = EnvSpec(
        T=spec.T,
        costs=load_cost_vectors()["balanced"],
        budget=BudgetSpec(label_cap=50),
        clocks=ClockSpec(retrain_duration=20),
    )
    assert SethiAdapter.port_status == "COMMON_CONTRACT_PORT"
    assert set(SethiAdapter.vocabulary) <= set(env.allowed_actions)
    pr = run_paired(
        {"m": lambda: SethiAdapter.build(env)}, spec, env, seeds=range(110_900_000, 110_900_002)
    )  # verify_run inside
    assert len(pr.runs["m"]) == 2
