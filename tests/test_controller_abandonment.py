from fractions import Fraction as F

from scripts.exhaustive_evaluation.pilot_controller_synthesis import alternative_cost
from scripts.exhaustive_evaluation.test_controller_abandonment import EvaluationController
from shiftlab.dive.risk_preserving_approx.controller_risk_verifier import verify_causal_null_risk


def test_zero_abandons_and_pending_positive_does_not_revive():
    c = EvaluationController(1, 1, 3, "abort")
    assert c.step(2, 4, (0, 1), 0, 2) == (0, 0, -1)
    assert c.step(-1, 5, (1,), 0, 2) == (0, 0, -1)


def test_success_stops_queries_and_promotion_is_absorbing():
    c = EvaluationController(1, 1, 3, "abort")
    assert c.step(2, 4, (1,), 0, 2) == (1, 0, 3)
    assert c.step(3, 5, (0,), 1, 2) == (1, 0, -1)


def test_analytical_three_positive_abandonment_policy():
    c = EvaluationController(1, 1, 3, "abort")
    assert verify_causal_null_risk(c, horizon=5, budget=4, delay=1).risk == F(1, 8)
    cost, _ = alternative_cost(c, horizon=5, budget=4, delay=1)
    # Expected paid queries 1+p+p^2; promote for last2 rounds after3 positives.
    p = F(4, 5)
    expected = 5 * p + F(1, 100) * (1 + p + p * p) + p**3 * (F(1, 10) - 2 * (2 * p - 1))
    assert cost == expected
