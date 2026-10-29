"""Exact marginal/transport and channel-polytope checks, not efficacy tests."""

from fractions import Fraction as F
from itertools import product

import pytest

from shiftlab.dive.conditional_query_coupling import (
    choose_two_slot_channel,
    expected_switches,
    query_strata,
)

GRID = tuple(F(i, 4) for i in range(5))


def test_all_binary_query_channels_preserve_stratum_marginals_and_optimal_switches():
    for r, p, x, y in product(GRID, repeat=4):
        a, b = (x, 1 - x), (y, 1 - y)
        rows = query_strata(r, p, a, b)
        for j, row in enumerate(rows):
            if row.probability == 0:
                continue
            j00, j01, j10, j11 = row.joint
            assert sum(row.joint) == 1 and min(row.joint) >= 0
            assert row.probability * (j00 + j01) == (1 - r) * a[j]
            assert row.probability * (j10 + j11) == r * b[j]
            assert j01 + j11 == p
            # Independent feasible joint: t=P(old=1,new=1) is in this interval.
            lower = max(F(0), row.old_probability1 + p - 1)
            upper = min(row.old_probability1, p)
            assert lower <= j11 <= upper
            assert j01 + j10 == row.old_probability1 + p - 2 * upper
            for old, mass in ((0, 1 - row.old_probability1), (1, row.old_probability1)):
                if mass:
                    assert 0 <= row.transition_probability1(old) <= 1
        switching = expected_switches(rows)
        signed = [p * (1 - r) * aj - (1 - p) * r * bj for aj, bj in zip(a, b)]
        assert switching == sum(map(abs, signed))
        assert switching >= abs(p - r)
        free = all(z >= 0 for z in signed) if p >= r else all(z <= 0 for z in signed)
        assert (switching == abs(p - r)) == free


def test_strict_action_dependent_local_score_gain_at_equal_switching_cost():
    result = choose_two_slot_channel(
        prior1=F(1, 2), target1=F(3, 4), gamma=F(1, 2), value0=(1, 0), value1=(0, 1)
    )
    assert result.query0 == (F(3, 4), F(1, 4))
    assert result.query1 == (F(1, 4), F(3, 4))
    assert result.score == F(3, 4) > F(1, 2)
    assert result.expected_switches == F(1, 4)


def test_independent_marginal_query_dominates_repaired_channel_for_continuation_state():
    for r, p, x, y in product(GRID, repeat=4):
        original = query_strata(r, p, (x, 1 - x), (y, 1 - y))
        marginal = tuple(row.probability for row in original)
        replacement = query_strata(r, p, marginal, marginal)
        assert expected_switches(replacement) == abs(p - r)
        assert expected_switches(replacement) <= expected_switches(original)
        for before, after in zip(original, replacement, strict=True):
            # The future state (query slot, new action) is identical in law.
            assert before.probability == after.probability
            for new_action in (0, 1):
                old_sum_before = before.joint[new_action] + before.joint[2 + new_action]
                old_sum_after = after.joint[new_action] + after.joint[2 + new_action]
                assert before.probability * old_sum_before == after.probability * old_sum_after


def test_solver_dominates_every_feasible_grid_channel():
    for r, p, gamma, v0, v1 in product(
        GRID, GRID, (F(1, 2), F(1)), ((1, 0), (0, 1)), ((1, 0), (0, 1))
    ):
        result = choose_two_slot_channel(prior1=r, target1=p, gamma=gamma, value0=v0, value1=v1)
        for x, y in product(GRID, repeat=2):
            if not gamma / 2 <= min(x, y) or not max(x, y) <= 1 - gamma / 2:
                continue
            if expected_switches(query_strata(r, p, (x, 1 - x), (y, 1 - y))) != abs(p - r):
                continue
            score = (1 - r) * (x * v0[0] + (1 - x) * v0[1]) + r * (y * v1[0] + (1 - y) * v1[1])
            assert result.score >= score
        if gamma == 1:
            assert result.query0 == result.query1 == (F(1, 2), F(1, 2))
        if p == r and 0 < r < 1:
            assert result.query0 == result.query1


def test_three_slot_strata_and_query_importance_weighting():
    r, p = F(2, 5), F(3, 5)
    a, b = (F(1, 2), F(1, 3), F(1, 6)), (F(1, 4), F(1, 4), F(1, 2))
    rows = query_strata(r, p, a, b)
    loss0, loss1 = (F(1), F(0), F(1, 2)), (F(0), F(1), F(1, 4))
    actual = sum(
        row.probability * ((row.joint[0] + row.joint[2]) * l0 + (row.joint[1] + row.joint[3]) * l1)
        for row, l0, l1 in zip(rows, loss0, loss1)
    )
    mixture = sum(
        row.probability * ((1 - p) * l0 + p * l1) for row, l0, l1 in zip(rows, loss0, loss1)
    )
    assert actual == mixture
    estimated = sum(
        row.probability * ((1 - p) * l0 + p * l1) / (3 * row.probability)
        for row, l0, l1 in zip(rows, loss0, loss1)
    )
    assert estimated == ((1 - p) * sum(loss0) + p * sum(loss1)) / 3


@pytest.mark.parametrize("bad", [-1, 2, True, 0.5])
def test_invalid_probability_inputs(bad):
    with pytest.raises(ValueError):
        query_strata(bad, F(1, 2), (F(1, 2), F(1, 2)), (F(1, 2), F(1, 2)))


def test_invalid_query_distributions_and_solver_inputs():
    for a, b in (((), ()), ((1, 1), (1, 0)), ((1,), (1, 0))):
        with pytest.raises(ValueError):
            query_strata(F(1, 2), F(1, 2), a, b)
    with pytest.raises(ValueError):
        choose_two_slot_channel(prior1=0, target1=1, gamma=0, value0=(1, 0), value1=(0, 1))
    with pytest.raises(ValueError):
        choose_two_slot_channel(prior1=0, target1=1, gamma=1, value0=(1,), value1=(0, 1))
    certain = query_strata(0, 1, (1,), (1,))[0]
    with pytest.raises(ValueError):
        certain.transition_probability1(1)
