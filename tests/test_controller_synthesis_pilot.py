from fractions import Fraction as F

import numpy as np
from scipy.optimize import linprog

from scripts.exhaustive_evaluation.pilot_controller_synthesis import (
    StreakController,
    alternative_cost,
    exact_root_mixture,
)
from shiftlab.dive.risk_preserving_approx.controller_risk_lp import verify_controller_lp
from shiftlab.dive.risk_preserving_approx.controller_risk_verifier import verify_causal_null_risk


def test_root_mixture_matches_independent_linear_program():
    rng = np.random.default_rng(17)
    for _ in range(20):
        rows = [{"risk": F(0), "cost": F(20)}] + [
            {"risk": F(int(rng.integers(1, 20)), 20), "cost": F(int(rng.integers(1, 20)))}
            for _ in range(10)
        ]
        cost, mix = exact_root_mixture(rows, F(1, 4))
        lp = linprog(
            [float(r["cost"]) for r in rows],
            A_ub=[[float(r["risk"]) for r in rows]],
            b_ub=[0.25],
            A_eq=[np.ones(len(rows))],
            b_eq=[1],
            bounds=(0, None),
            method="highs",
        )
        assert lp.success
        np.testing.assert_allclose(float(cost), lp.fun, atol=1e-12)
        assert sum(rows[i]["risk"] * w for i, w in mix) <= F(1, 4)


def test_alternative_known_policies_have_exact_costs():
    never = StreakController(1, 1, 1, "never")
    always = StreakController(1, 1, 1, "always")
    assert alternative_cost(never, horizon=12, budget=6, delay=2)[0] == F(48, 5)
    assert alternative_cost(always, horizon=12, budget=6, delay=2)[0] == F(5, 2)


def test_selected_streak_risk_matches_standard_product_lp():
    for streak in [4, 5, 6, 7]:
        controller = StreakController(1, 1, streak)
        exact = verify_causal_null_risk(controller, horizon=24, budget=12, delay=2)
        lp = verify_controller_lp(controller, horizon=24, budget=12, delay=2)
        np.testing.assert_allclose(float(exact.risk), lp.risk, atol=1e-12)
