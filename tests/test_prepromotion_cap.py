from fractions import Fraction as F

import pytest

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.dive.prepromotion_cap import PrePromotionCapGame


def test_query_cap_changes_after_first_promotion():
    game = PrePromotionCapGame(GameConfig(horizon=5, budget=3, delay=2), RegimeModel(), pre_cap=1)
    assert game.choices(((0, 1),)) == ((0, 0), (1, 0))
    assert (0, 1) in game.choices(((0, 1), (1, 0)))
    assert (1, 1) in game.choices(((0, 1), (1, 0), (0, 0)))
    assert all(query == 0 for _, query in game.choices(((0, 1), (1, 1), (0, 1))))


def test_pending_labels_cannot_change_cap():
    game = PrePromotionCapGame(GameConfig(horizon=5, budget=3, delay=2), RegimeModel(), pre_cap=1)
    history = ((0, 1),)
    assert game.information(history, ((1, 0),)) == game.information(history, ((1, 1),))
    assert game.choices(history) == ((0, 0), (1, 0))


@pytest.mark.parametrize("horizon,budget,delay", [(3, 0, 1), (4, 2, 7), (5, 2, 2)])
def test_full_precap_matches_reference(horizon, budget, delay):
    config = GameConfig(horizon=horizon, budget=budget, delay=delay)
    model = RegimeModel()
    baseline = FirstPromotionDecomposedGame(config, model)
    restricted = PrePromotionCapGame(config, model, pre_cap=budget)
    report0, _, _ = baseline.solve()
    report1, policy1, _ = restricted.solve()
    assert abs(float(F(report0["raw_recovered_cost"]) - F(report1["raw_recovered_cost"]))) < 1e-7
    assert restricted.null_risk(policy1) <= config.alpha
    assert restricted.learner.infos.keys() == baseline.learner.infos.keys()


def test_invalid_cap_rejected():
    config = GameConfig(horizon=3, budget=2)
    for cap in (-1, 3, True, 1.0):
        with pytest.raises(ValueError):
            PrePromotionCapGame(config, RegimeModel(), pre_cap=cap)
