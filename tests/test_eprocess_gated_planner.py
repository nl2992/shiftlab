from fractions import Fraction as F

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.eprocess_gated_planner import EProcessGatedPlanner, mix_with_never_promote


def test_fixed_stake_gate_and_root_mixture_have_exact_null_risk():
    config = GameConfig(
        horizon=6,
        budget=3,
        delay=2,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=F(1, 10),
        transition10=F(1, 10),
        emission0=F(1, 10),
        emission1=F(9, 10),
        prior1=F(1, 2),
    )
    game = EProcessGatedPlanner(config, model, stake=F(1), threshold=F(4))
    dynamic_cost, raw_policy = game.solve_gated()
    raw_metrics = game.expected_metrics(raw_policy)
    raw_risk = game.null_risk(raw_policy)

    assert dynamic_cost == sum(raw_metrics[:3])
    assert raw_risk == F(1, 4)
    activation = config.alpha / raw_risk
    mixture = mix_with_never_promote(game, raw_policy, activation)
    safe = lambda history, outcomes: tuple(F(choice == (0, 0)) for choice in game.choices(history))
    expected = tuple(
        activation * raw + (1 - activation) * baseline
        for raw, baseline in zip(raw_metrics, game.expected_metrics(safe), strict=True)
    )
    assert game.expected_metrics(mixture) == expected
    assert game.null_risk(mixture) == config.alpha
    assert expected[3] <= config.budget
