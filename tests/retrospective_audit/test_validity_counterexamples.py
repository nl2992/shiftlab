"""Analytical counterexamples to stronger claims; these do not refute scoped nulls."""

from fractions import Fraction as F


def test_selected_event_hurdle_does_not_pay_one_time_fee():
    horizon = 10
    selected_events = 1
    gain = F(2, 100)
    fee = F(1, 10)
    hurdle = fee / horizon
    tested_increment = F(selected_events, horizon) * (gain - hurdle)
    full_net_benefit = selected_events * gain - fee
    assert tested_increment > 0
    assert full_net_benefit < 0
    assert selected_events * hurdle < fee


def test_shared_randomness_invalidates_unguarded_product():
    # Two identical one-step e-values: 2 on heads, 0 on tails.
    outcomes = [F(0), F(2)]
    assert sum(outcomes) / 2 == 1
    assert sum(x * x for x in outcomes) / 2 == 2


def test_fixed_mixture_preserves_expectation_under_same_example():
    outcomes = [F(0), F(2)]
    assert sum(F(1, 3) * x + F(2, 3) * x for x in outcomes) / 2 == 1
