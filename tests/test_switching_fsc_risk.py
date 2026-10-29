from fractions import Fraction as F

import pytest

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.switching_fsc_risk import DeterministicFSC, worst_case_promotion_risk


def append_released(memory, _request_time, outcome):
    return (*memory, outcome)


def game_policy(game, controller):
    """Adapt a public-memory FSC to the full-history reference policy interface."""

    def policy(history, outcomes):
        memory = controller.initial_memory
        remaining = game.config.budget

        for time, selected in enumerate(history, start=1):
            for request_time, outcome in outcomes:
                if request_time + game.config.delay == time:
                    memory = controller.on_release(memory, request_time, outcome)
            action, query, memory = controller.decide(time, memory, remaining)
            assert (action, query) == selected
            remaining -= query

        time = len(history) + 1
        for request_time, outcome in outcomes:
            if request_time + game.config.delay == time:
                memory = controller.on_release(memory, request_time, outcome)
        action, query, _next_memory = controller.decide(time, memory, remaining)
        selected = (action, query)
        choices = game.choices(history)
        return tuple(F(choice == selected) for choice in choices)

    return policy


def test_compact_delayed_threshold_risk_matches_full_history_reference():
    controller = DeterministicFSC(
        initial_memory=(),
        on_release=append_released,
        decide=lambda time, memory, _remaining: (
            (
                0,
                int(time in (1, 2)),
                memory,
            )
            if time < 3
            else (int(memory == (1, 1)), 0, memory)
        ),
    )
    config = GameConfig(horizon=3, budget=2, delay=1)
    game = CausalSwitchingGame(config, RegimeModel())

    compact = worst_case_promotion_risk(controller, horizon=3, budget=2, delay=1)
    reference = game.null_risk(game_policy(game, controller))

    assert compact.risk == reference == F(1, 4)
    assert compact.visited_states < 32


def test_pending_label_asymmetry_and_nonmonotone_event_match_reference():
    controller = DeterministicFSC(
        initial_memory=(),
        on_release=append_released,
        decide=lambda time, memory, _remaining: (
            (0, int(time in (1, 2)), memory)
            if time < 4
            else (int(len(memory) == 2 and memory[0] != memory[1]), 0, memory)
        ),
    )
    config = GameConfig(horizon=4, budget=2, delay=2)
    game = CausalSwitchingGame(config, RegimeModel())

    compact = worst_case_promotion_risk(controller, horizon=4, budget=2, delay=2)
    reference = game.null_risk(game_policy(game, controller))

    assert compact.risk == reference == F(3, 4)
    assert compact.visited_states < 64


def test_compact_controller_cannot_exceed_hard_budget():
    controller = DeterministicFSC(
        initial_memory=(),
        on_release=append_released,
        decide=lambda _time, memory, _remaining: (0, 1, memory),
    )

    with pytest.raises(ValueError, match="pathwise hard query budget"):
        worst_case_promotion_risk(controller, horizon=2, budget=1, delay=1)
