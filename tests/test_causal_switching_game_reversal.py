"""Additional reversal-charge check without changing the frozen reference test source."""

from fractions import Fraction as F

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel


def test_initial_promotion_and_rollback_both_pay_switch_charge():
    game = CausalSwitchingGame(
        GameConfig(horizon=2, budget=0, delay=1), RegimeModel(transition01=0, transition10=0)
    )

    def policy(history, outcomes):
        chosen = int(not history), 0
        return tuple(F(choice == chosen) for choice in game.choices(history))

    decision, query, switching, queries, switches = game.expected_metrics(policy)
    assert (decision, query, switching, queries, switches) == (F(1), F(0), F(1, 5), F(0), F(2))
    assert game.null_risk(policy) == 1
