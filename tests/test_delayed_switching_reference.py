"""Information-boundary and exact-expectation checks for a reference, not efficacy tests."""

from itertools import product
from math import ceil, log

import pytest

from shiftlab.dive.delayed_switching_reference import DelayedBudgetHedge, PairedFeedback


def replay(losses, *, blocks=2, delay=2, eta=0.7, seed=0, uniform=0.6):
    learner = DelayedBudgetHedge(
        horizon=len(losses),
        blocks=blocks,
        budget=blocks,
        delay=delay,
        eta=eta,
        query_seed=seed,
        deployment_uniform=uniform,
    )
    pending = {}
    trace = []
    for t, pair in enumerate(losses, 1):
        decision = learner.step(t, pending.pop(t, ()))
        if decision.query:
            pending[t + delay] = (PairedFeedback(t, *pair),)
        trace.append(decision)
    return learner, trace


@pytest.mark.parametrize("delay", [1, 2, 5, 20])
def test_budget_counts_pending_queries_and_ignores_unarrived_labels(delay):
    learner, trace = replay([(1.0, 0.0)] * 8, blocks=4, delay=delay)
    assert learner.queries == sum(row.query for row in trace) == 4
    assert learner.pending_count == sum(
        row.query and t + delay > 8 for t, row in enumerate(trace, 1)
    )
    if delay > 8:
        assert {row.probability1 for row in trace} == {0.5}


def test_acquisition_and_probabilities_are_independent_of_deployment_coin():
    losses = [(float(t % 3 == 0), float(t % 2 == 0)) for t in range(12)]
    _, first = replay(losses, blocks=4, uniform=0.01)
    _, second = replay(losses, blocks=4, uniform=0.99)
    assert [(x.query, x.probability1) for x in first] == [(x.query, x.probability1) for x in second]
    assert [x.action for x in first] != [x.action for x in second]


def test_unreleased_future_outcomes_do_not_change_decisions():
    _, first = replay([(1.0, 0.0)] * 8, blocks=4, delay=3)
    _, second = replay([(1.0, 0.0)] * 4 + [(0.0, 1.0)] * 4, blocks=4, delay=3)
    assert first[:7] == second[:7]


def test_arrivals_inside_block_wait_for_next_boundary():
    learner = DelayedBudgetHedge(
        horizon=8,
        blocks=2,
        budget=2,
        delay=1,
        eta=1.0,
        query_seed=2,
        deployment_uniform=0.6,
    )
    # Seed 2 schedules its first query at event 1, arriving at event 2.
    assert learner.step(1).query
    assert learner.step(2, [PairedFeedback(1, 1.0, 0.0)]).probability1 == 0.5
    assert learner.step(3).probability1 == 0.5
    assert learner.step(4).probability1 == 0.5
    assert learner.step(5).probability1 > 0.5


def test_invalid_feedback_is_atomic_and_round_order_is_checked():
    learner = DelayedBudgetHedge(
        horizon=4,
        blocks=4,
        budget=4,
        delay=1,
        eta=1.0,
        query_seed=0,
        deployment_uniform=0.4,
    )
    with pytest.raises(ValueError, match="in order"):
        learner.step(2)
    learner.step(1)
    for rows in (
        [],
        [PairedFeedback(2, 0, 1)],
        [PairedFeedback(1, float("nan"), 0)],
        [PairedFeedback(1, 2, 0)],
        [PairedFeedback(1, 0, 1)] * 2,
    ):
        with pytest.raises(ValueError):
            learner.step(2, rows)
        assert learner.queries == learner.pending_count == 1
    learner.step(2, [PairedFeedback(1, 0, 1)])


def test_early_feedback_is_rejected_and_boundary_arrival_is_used():
    learner = DelayedBudgetHedge(
        horizon=4,
        blocks=4,
        budget=4,
        delay=2,
        eta=1.0,
        query_seed=0,
        deployment_uniform=0.6,
    )
    learner.step(1)
    with pytest.raises(ValueError, match="exact availability"):
        learner.step(2, [PairedFeedback(1, 1, 0)])
    assert learner.step(2).probability1 == 0.5
    assert learner.step(3, [PairedFeedback(1, 1, 0)]).probability1 > 0.5


@pytest.mark.parametrize(
    "override",
    [
        {"horizon": 4.0},
        {"blocks": 0},
        {"blocks": 3},
        {"budget": 1},
        {"delay": 0},
        {"eta": float("inf")},
        {"deployment_uniform": 1.0},
    ],
)
def test_invalid_contracts_are_rejected(override):
    parameters = {
        "horizon": 4,
        "blocks": 2,
        "budget": 2,
        "delay": 1,
        "eta": 1.0,
        "query_seed": 0,
        "deployment_uniform": 0.4,
    }
    parameters.update(override)
    with pytest.raises(ValueError):
        DelayedBudgetHedge(**parameters)


@pytest.mark.parametrize("delay", [1, 3, 8])
def test_exact_expectation_over_uniform_query_locations_and_deployment_coin(delay):
    # Enumerate both query locations in each of three length-2 blocks. This does not
    # use PRNG seeds as a stand-in for exact integration over the query randomization.
    for bits in product((0.0, 1.0), repeat=6):
        losses = [(bit, 1 - bit) for bit in bits]
        eta, switch_cost, query_cost = 0.8, 0.4, 0.1
        expected_cost = 0.0
        for offsets in product((0, 1), repeat=3):

            class QueryLocations:
                def __init__(self):
                    self.remaining = iter(offsets)  # noqa: B023 - Consumed synchronously within this loop iteration.

                def randrange(self, width):
                    assert width == 2
                    return next(self.remaining)

            learner = DelayedBudgetHedge(
                horizon=6,
                blocks=3,
                budget=3,
                delay=delay,
                eta=eta,
                query_seed=0,
                deployment_uniform=0.5,
            )
            learner._query_rng = QueryLocations()
            pending, probabilities = {}, []
            for t, pair in enumerate(losses, 1):
                row = learner.step(t, pending.pop(t, ()))
                probabilities.append(row.probability1)
                if row.query:
                    pending[t + delay] = [PairedFeedback(t, *pair)]
            decision_cost = sum(
                (1 - p) * pair[0] + p * pair[1]
                for p, pair in zip(probabilities, losses, strict=True)
            )
            # Exact common-uniform coupling expectation, including initial action 0.
            switches = probabilities[0] + sum(
                abs(p - q) for p, q in zip(probabilities[1:], probabilities[:-1], strict=True)
            )
            assert switches <= 0.5 + eta * 3 / 4 + 1e-12
            expected_cost += (decision_cost + switch_cost * switches + 3 * query_cost) / 8
        comparator = min(sum(pair[a] for pair in losses) for a in (0, 1))
        bound = (
            2 * log(2) / eta
            + eta * 6 / 8
            + eta * 6 * ceil(delay / 2) / 4
            + switch_cost * (0.5 + eta * 3 / 4)
            + 3 * query_cost
        )
        assert expected_cost - comparator <= bound + 1e-12
