from fractions import Fraction as F

import pytest

from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame


@pytest.mark.parametrize(
    ("horizon", "budget", "delay", "model"),
    [
        (5, 2, 2, RegimeModel()),
        (
            5,
            2,
            1,
            RegimeModel(
                transition01=F(1, 4),
                transition10=F(1, 4),
                emission0=F(1, 20),
                emission1=F(19, 20),
                prior1=F(1, 2),
            ),
        ),
        (
            6,
            3,
            1,
            RegimeModel(
                transition01=F(1, 4),
                transition10=F(1, 4),
                emission0=F(1, 20),
                emission1=F(19, 20),
                prior1=F(1, 2),
            ),
        ),
    ],
)
def test_decomposition_matches_full_two_law_oracle(
    horizon: int, budget: int, delay: int, model: RegimeModel
) -> None:
    config = GameConfig(
        horizon=horizon,
        budget=budget,
        delay=delay,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    full = CausalSwitchingGame(config, model)
    full_report, full_policy, _ = full.solve()
    reduced = FirstPromotionDecomposedGame(config, model)
    reduced_report, reduced_policy, _ = reduced.solve()

    assert reduced_report["raw_recovered_cost"] == full_report["raw_recovered_cost"]
    assert reduced.expected_metrics(reduced_policy) == full.expected_metrics(full_policy)
    assert reduced.null_risk(reduced_policy) == full.null_risk(full_policy) == config.alpha
    assert len(reduced.learner.infos) < len(full.learner.infos)
    assert reduced_report["nodes"] < full_report["nodes"]
