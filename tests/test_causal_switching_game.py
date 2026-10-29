"""Analytic optima and information-order checks for the classical game reference."""

from fractions import Fraction as F
from functools import cache
from itertools import product

import pytest

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def _promotion_probability_on_tape(game, policy, tape):
    @cache
    def visit(history, outcomes):
        time = len(history) + 1
        if time > game.config.horizon:
            return F(0)
        value = F(0)
        for (action, query), mass in zip(
            game.choices(history), policy(history, outcomes), strict=True
        ):
            if action:
                continuation = F(1)
            else:
                continuation = visit(
                    history + ((action, query),),
                    outcomes + (((time, tape[time - 1]),) if query else ()),
                )
            value += mass * continuation
        return value

    return visit((), ())


def test_monotone_promotion_sequence_form_matches_unrestricted_small_cell():
    config = GameConfig(
        horizon=3,
        budget=2,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 10),
        emission1=F(9, 10),
    )
    unrestricted, restricted = (
        CausalSwitchingGame(config, model),
        CausalSwitchingGame(config, model),
    )
    unrestricted_report, _, _ = unrestricted.solve()
    restricted_report, restricted_policy, _ = restricted.solve(monotone_promotion=True)

    tape_values = {
        tape: _promotion_probability_on_tape(restricted, restricted_policy, tape)
        for tape in product((0, 1), repeat=config.horizon)
    }
    for tape, probability in tape_values.items():
        for bit, value in enumerate(tape):
            if not value:
                successor = tape[:bit] + (1,) + tape[bit + 1 :]
                assert probability <= tape_values[successor]
    assert (
        abs(restricted_report["solver_objective"] - unrestricted_report["solver_objective"]) <= 1e-8
    )
    assert restricted_report["raw_causal_null_risk"] == "1/10"


STATIC = RegimeModel(transition01=0, transition10=0)


def deterministic(game, rule):
    def policy(history, outcomes):
        visible = dict(game.information(history, outcomes)[1])
        chosen = rule(history, visible)
        return tuple(F(choice == chosen) for choice in game.choices(history))

    return policy


def test_pending_outcomes_are_not_learner_information():
    game = CausalSwitchingGame(GameConfig(horizon=3, budget=2, delay=2), STATIC)
    history = ((0, 1),)
    assert game.information(history, ((1, 0),)) == game.information(history, ((1, 1),))
    history += ((0, 0),)
    assert game.information(history, ((1, 0),)) != game.information(history, ((1, 1),))


@pytest.mark.parametrize("alpha,expected", [(F(1), F(187, 200)), (F(1, 10), F(987, 1000))])
def test_stationary_two_round_analytic_optimum(alpha, expected):
    game = CausalSwitchingGame(GameConfig(horizon=2, budget=1, delay=1, alpha=alpha), STATIC)
    report, _, _ = game.solve()
    assert abs(float(F(report["calibrated_total_cost"]) - expected)) < 1e-8
    assert F(report["calibrated_risk_bound"]) <= alpha
    assert report["equality_residual"] < 1e-8
    assert report["inequality_violation"] < 1e-8


@pytest.mark.parametrize("budget,delay", [(0, 1), (2, 3)])
def test_no_usable_information_keeps_incumbent_without_query_cost(budget, delay):
    game = CausalSwitchingGame(GameConfig(horizon=3, budget=budget, delay=delay), STATIC)
    report, _, _ = game.solve()
    assert F(report["calibrated_total_cost"]) == F(3, 2)
    assert F(report["calibrated_metrics"]["queries"]) == 0
    assert F(report["calibrated_risk_bound"]) == 0


def test_zero_risk_forbids_promotion_and_unhelpful_queries():
    game = CausalSwitchingGame(GameConfig(horizon=3, budget=2, delay=1, alpha=F(0)), STATIC)
    report, _, _ = game.solve()
    assert F(report["calibrated_total_cost"]) == F(3, 2)
    assert F(report["calibrated_risk_bound"]) == 0


def test_independent_verifier_detects_iid_only_calibration_failure():
    game = CausalSwitchingGame(GameConfig(horizon=3, budget=2, delay=1), STATIC)

    def rule(history, visible):
        time = len(history) + 1
        if time == 1:
            return 0, 1
        if time == 2:
            return 0, int(visible[1] == 0)
        return int(visible.get(2) == 1), 0

    policy = deterministic(game, rule)
    assert game.null_risk(policy, iid_boundary=True) == F(1, 4)
    assert game.null_risk(policy) == F(1, 2)


def test_null_cannot_choose_pending_label_after_future_query_coin():
    game = CausalSwitchingGame(GameConfig(horizon=3, budget=2, delay=2), STATIC)

    def policy(history, outcomes):
        time = len(history) + 1
        if time == 2:
            return tuple(F(1, 2) if a == 0 else F(0) for a, q in game.choices(history))
        visible = dict(game.information(history, outcomes)[1])
        chosen = (0, 1) if time == 1 else (int(visible[1] == history[1][1]), 0)
        return tuple(F(choice == chosen) for choice in game.choices(history))

    assert game.null_risk(policy) == F(1, 2)


def test_budget_is_reserved_at_request_even_without_arrival():
    game = CausalSwitchingGame(GameConfig(horizon=3, budget=1, delay=3), STATIC)
    assert all(q == 0 for _, q in game.choices(((0, 1),)))


def test_tree_limit_is_terminal_and_reported():
    game = CausalSwitchingGame(GameConfig(horizon=3, budget=2, max_nodes=2), STATIC)
    with pytest.raises(RuntimeError, match="node limit"):
        game.build()
