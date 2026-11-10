"""Exact oracle validation: DP == brute force over all deterministic policies; forward checks."""

from __future__ import annotations

from fractions import Fraction as F
from itertools import product

import numpy as np
import pytest

from shiftlab.paper3.contracts import Costs, ProblemSpec
from shiftlab.paper3.oracle import (
    OUTCOMES,
    EconomicOracle,
    HMMModel,
    OraclePolicy,
    _tape_probabilities,
    brute_force_optimum,
    oracle_risk,
    solve_economic,
)
from shiftlab.paper3.simulation import Tape, run_policy

# regimes flip which model is better, so information has value
M = HMMModel(
    trans=((F(9, 10), F(1, 10)), (F(1, 10), F(9, 10))),
    prior1=F(1, 2),
    m0=(F(3, 10), F(3, 5)),
    m1=(F(3, 5), F(3, 10)),
)


def test_forward_probabilities_exact():
    probs = _tape_probabilities(M, 3)
    assert sum(probs.values()) == 1
    o = EconomicOracle(M, 3, 1, 1, F(1, 50), F(1, 10))
    # marginal of the first two outcomes from the filter equals enumeration
    for a, b in product(OUTCOMES, repeat=2):
        enum = sum(p for tp, p in probs.items() if tp[0] == a and tp[1] == b)
        assert o.joint(((1, a), (2, b))) == enum
    assert sum(o.joint(((1, a),)) for a in OUTCOMES) == 1


@pytest.mark.parametrize(
    "T,B,d,c,k",
    [
        (3, 1, 1, F(1, 50), F(1, 10)),
        (3, 2, 2, F(1, 50), F(1, 10)),
        (3, 1, 2, F(1, 100), F(1, 5)),
        (4, 1, 2, F(1, 50), F(1, 10)),
        (4, 0, 1, F(1, 50), F(1, 10)),
        (4, 1, 3, F(1, 100), F(1, 20)),
    ],
)
def test_dp_equals_brute_force(T, B, d, c, k):
    dp = solve_economic(M, T, B, d, c, k).value
    bf, n = brute_force_optimum(M, T, B, d, c, k)
    assert dp == bf and n > 1


def test_information_has_value_and_policy_is_better_than_baselines():
    r = solve_economic(M, 3, 1, 1, F(1, 50), F(1, 10))
    assert r.policy[(1, 0, 1, (), ())][1] == 1  # buys the label at t=1
    o = EconomicOracle(M, 3, 1, 1, F(1, 50), F(1, 10))
    never = o.policy_value(lambda s: (0, 0))
    always = o.policy_value(lambda s: (1, 0))
    assert r.value < min(never, always)
    # no-information optimum is attained when B = 0, and is worse
    assert solve_economic(M, 3, 0, 1, F(1, 50), F(1, 10)).value > r.value


def test_float_mode_matches_exact():
    ex = solve_economic(M, 8, 2, 2, F(1, 50), F(1, 5)).value
    fl = solve_economic(M, 8, 2, 2, F(1, 50), F(1, 5), num=float).value
    assert float(ex) == pytest.approx(fl, rel=1e-12)


def test_simulator_loop_reproduces_exact_value():
    """End-to-end: DP policy in run_policy on HMM tapes has mean J within 4 SE of the exact value."""
    T, B, d, c, k = 6, 2, 2, F(1, 50), F(1, 5)
    o = EconomicOracle(M, T, B, d, c, k, num=float)
    exact = float(solve_economic(M, T, B, d, c, k).value)
    spec = ProblemSpec(
        T=T, B=B, costs=Costs(c_q=float(c), k=float(k), c_compute=0.0), delay_known=d
    )
    rng = np.random.default_rng(0)
    js = []
    for _ in range(3000):
        ell = M.sample_tape(T, rng)
        tape = Tape(ell, np.ones(T, bool), np.zeros((T, 1)), np.full(T, d))
        js.append(run_policy(OraclePolicy(o), tape, spec, 0).J)
    se = np.std(js) / np.sqrt(len(js))
    assert abs(np.mean(js) - exact) < 4 * se


def test_oracle_risk_wired_and_constraint_binds():
    r = oracle_risk(2, 1, 1)
    assert F(r["calibrated_risk_bound"]) <= F(1, 10)
    free = oracle_risk(2, 1, 1, alpha=1)
    assert F(r["calibrated_total_cost"]) >= F(free["calibrated_total_cost"])
