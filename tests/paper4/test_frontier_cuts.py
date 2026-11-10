"""Fast CPU checks for frontier-cut generation (FCG)."""

from __future__ import annotations

import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame
from shiftlab.paper4.frontier_cuts import (
    best_response_null,
    frontier_cut_generation,
    learner_only_game,
    risk_row_for_null,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/research_risk_approx"))

CELLS = {
    "C1": (5, 2, F(1, 4), (F(1, 20), F(19, 20))),
    "C2": (5, 2, F(9, 10), (F(1, 10), F(9, 10))),
}


def make(horizon, budget, transition, emissions):
    config = GameConfig(
        horizon=horizon,
        budget=budget,
        delay=1,
        alpha=F(1, 10),
        query_cost=F(1, 100),
        switch_cost=F(1, 10),
    )
    model = RegimeModel(
        transition01=transition,
        transition10=transition,
        emission0=emissions[0],
        emission1=emissions[1],
        prior1=F(1, 2),
    )
    return config, model


def test_iid_strategy_row_matches_iid_risk_coefficients():
    from iid_relaxation_certified_pipeline import iid_risk_coefficients

    config, model = make(4, 2, F(1, 4), (F(1, 20), F(19, 20)))
    game = learner_only_game(config, model)
    assert risk_row_for_null(game, {}) == iid_risk_coefficients(game)


def test_best_response_matches_null_risk_and_cut_is_tight():
    config, model = make(4, 2, F(9, 10), (F(1, 10), F(9, 10)))
    game = learner_only_game(config, model)
    from shiftlab.paper4.frontier_cuts import realization_flow

    def always_query_then_promote(history, outcomes):
        choices = game.choices(history)
        target = (
            (1, 0)
            if len(history) >= 2
            else (0, 1 if game.config.budget > sum(q for _, q in history) else 0)
        )
        return tuple(F(c == target) for c in choices)

    for policy in (always_query_then_promote,):
        risk, strategy = best_response_null(game, policy)
        assert risk == game.null_risk(policy)
        row = risk_row_for_null(game, strategy)
        flow = realization_flow(game, policy)
        assert sum((c * v for c, v in zip(row, flow, strict=True)), F(0)) == risk


@pytest.mark.parametrize("cell", ["C1", "C2"])
def test_fcg_matches_reference(cell):
    config, model = make(*CELLS[cell])
    out = frontier_cut_generation(config, model)
    report, _policy, _records = FirstPromotionDecomposedGame(config, model).solve()
    # calibrated_total_cost = feasible (root-mixed with continue-forever) cost of the
    # reference LP solution; it is the reference upper value V_ref.
    v_ref = F(report["calibrated_total_cost"])
    assert out["final_robust_risk"] <= config.alpha
    assert out["L"] <= out["U"]
    assert abs(float(out["U"] - v_ref)) <= 1e-6
    assert float(out["U"] - out["L"]) <= 1e-6 * max(1.0, abs(float(out["U"])))
