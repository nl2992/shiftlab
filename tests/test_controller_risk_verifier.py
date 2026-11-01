from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

import pytest

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.risk_preserving_approx.controller_risk_verifier import (
    verify_causal_null_risk,
)


@dataclass(frozen=True)
class ScriptedController:
    initial_state: object = None
    mode: str = "never"

    def step(self, memory, time, released, previous_action, remaining_queries):
        if self.mode == "never":
            return 0, 0, memory
        if self.mode == "immediate":
            return (1 if time == 1 else 0), 0, memory
        if self.mode == "one_query":
            if time == 1:
                return 0, 1, memory
            return (1 if released == (1,) else 0), 0, memory
        if self.mode == "pending_adaptive":
            if time in (1, 2):
                return 0, 1, memory
            if time == 3:
                assert len(released) == 1
                return 0, 0, released[0]
            if time == 4:
                assert len(released) == 1
                return (1 if memory == 0 and released[0] == 1 else 0), 0, memory
        raise AssertionError(f"unexpected controller input at t={time}: {released=}")


def reference_risk(controller, *, horizon, budget, delay):
    game = CausalSwitchingGame(
        GameConfig(horizon=horizon, budget=budget, delay=delay, alpha=F(1, 10)),
        RegimeModel(),
    )

    def policy(history, outcomes):
        memory = controller.initial_state
        previous_action = 0
        for time in range(1, len(history) + 1):
            released = tuple(y for request, y in outcomes if request + delay == time)
            remaining = budget - sum(query for _, query in history[: time - 1])
            action, query, memory = controller.step(
                memory, time, released, previous_action, remaining
            )
            previous_action = action
        time = len(history) + 1
        released = tuple(y for request, y in outcomes if request + delay == time)
        remaining = budget - sum(query for _, query in history)
        action, query, _ = controller.step(memory, time, released, previous_action, remaining)
        selected = (action, query)
        return tuple(F(choice == selected) for choice in game.choices(history))

    return game.null_risk(policy)


@pytest.mark.parametrize(
    ("controller", "horizon", "budget", "delay", "expected"),
    [
        (ScriptedController(mode="never"), 3, 0, 1, F(0)),
        (ScriptedController(mode="immediate"), 3, 0, 1, F(1)),
        (ScriptedController(mode="one_query"), 2, 1, 1, F(1, 2)),
        (ScriptedController(mode="pending_adaptive"), 4, 2, 2, F(1, 2)),
    ],
)
def test_product_state_verifier_matches_full_history_reference(
    controller, horizon, budget, delay, expected
):
    result = verify_causal_null_risk(controller, horizon=horizon, budget=budget, delay=delay)
    assert result.risk == expected
    assert result.risk == reference_risk(controller, horizon=horizon, budget=budget, delay=delay)
    assert result.visited_states > 0


def test_verifier_rejects_controller_that_exceeds_pathwise_budget():
    with pytest.raises(ValueError, match="pathwise query budget"):
        verify_causal_null_risk(ScriptedController(mode="one_query"), horizon=2, budget=0, delay=1)
