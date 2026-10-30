from __future__ import annotations

from dataclasses import asdict

import numpy as np
import pytest

from scripts.sota_search.verify_generators import verify_losses
from shiftlab.sota_search.generators import WorldConfig, make_world


@pytest.mark.parametrize("family", ["G1", "G4"])
def test_independent_verifier_rejects_corrupted_losses(family):
    config = WorldConfig(family=family, horizon=128)
    world = make_world(config, seed=12)
    raw = {
        "features": np.array([e.features for e in world.events]),
        **{
            name: getattr(world.truth, name).copy()
            for name in (
                "outcomes",
                "regime_weight",
                "hidden_state",
                "predictive_losses",
                "decision_losses",
                "expected_predictive_losses",
                "expected_decision_losses",
                "nominal_predictive_losses",
                "nominal_decision_losses",
            )
        },
    }
    verify_losses(raw, asdict(config))
    raw["expected_predictive_losses"][0, 0] += 0.01
    with pytest.raises(AssertionError):
        verify_losses(raw, asdict(config))
