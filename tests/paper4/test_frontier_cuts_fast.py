"""Fast CPU checks for FCG-fast: exact agreement with the v1 implementation."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from shiftlab.dive.causal_switching_game import GameConfig
from shiftlab.dive.delayed_regime_information import RegimeModel
from shiftlab.paper4.frontier_cuts import frontier_cut_generation
from shiftlab.paper4.frontier_cuts_fast import frontier_cut_generation_fast

CELLS = {
    "C1": (5, 2, F(1, 4), (F(1, 20), F(19, 20))),
    "C2": (5, 2, F(9, 10), (F(1, 10), F(9, 10))),
}


@pytest.mark.parametrize("cell", ["C1", "C2"])
def test_fast_matches_v1_exactly(cell):
    horizon, budget, transition, emissions = CELLS[cell]
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
    v1 = frontier_cut_generation(config, model)
    fast = frontier_cut_generation_fast(config, model)
    assert fast["U"] == v1["U"]
    assert fast["final_robust_risk"] <= config.alpha
    assert fast["L"] <= fast["U"]
    assert float(fast["gap"]) <= 1e-6 * max(1.0, abs(float(fast["U"])))
    assert fast["n_rows"] == v1["n_rows"]
    assert fast["end_to_end_seconds"] >= fast["build_seconds"]
