from fractions import Fraction as F

import pytest

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.early_promotion_pruning import EarlyPromotionPruning
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame


@pytest.mark.parametrize(
    "horizon,budget,delay,alpha",
    [
        (3, 0, 1, F(1, 10)),
        (4, 2, 8, F(1, 10)),
        (5, 2, 2, F(1, 10)),
        (6, 3, 1, F(1, 10)),
        (4, 2, 1, F(0)),
    ],
)
def test_early_pruning_matches_reference_and_preserves_risk(horizon, budget, delay, alpha):
    model = RegimeModel(
        transition01=F(1, 4),
        transition10=F(1, 4),
        emission0=F(1, 20),
        emission1=F(19, 20),
        prior1=F(1, 2),
    )
    config = GameConfig(horizon=horizon, budget=budget, delay=delay, alpha=alpha)
    baseline = FirstPromotionDecomposedGame(config, model)
    report0, policy0, _ = baseline.solve()
    candidate = EarlyPromotionPruning(config, model)
    report1, policy1, records = candidate.solve()
    assert abs(float(F(report0["raw_recovered_cost"]) - F(report1["raw_recovered_cost"]))) < 1e-7
    assert candidate.null_risk(policy1) <= alpha
    assert baseline.null_risk(policy0) <= alpha
    assert candidate.learner.infos.keys() == baseline.learner.infos.keys()
    assert candidate.opponent.infos.keys() == baseline.opponent.infos.keys()
    for record in records:
        if (record["history"], record["released"]) in candidate.marked_information:
            assert all(
                F(p) == 0
                for p, choice in zip(record["probabilities"], record["choices"], strict=True)
                if choice[0]
            )
    if horizon == 6:
        assert len(candidate.marked_information) == 93
        assert candidate.skipped_continuations > 0


def test_pending_outcomes_do_not_affect_marking():
    model = RegimeModel()
    game = EarlyPromotionPruning(GameConfig(horizon=5, budget=2, delay=2), model)
    history = ((0, 1),)
    info0 = game.information(history, ((1, 0),))
    info1 = game.information(history, ((1, 1),))
    assert info0 == info1
    b0 = game._belief_from_history(history, ((1, 0),))
    b1 = game._belief_from_history(history, ((1, 1),))
    assert b0 == b1
    assert game.dominated(2, b0) == game.dominated(2, b1)
