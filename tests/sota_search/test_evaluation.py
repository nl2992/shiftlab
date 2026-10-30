import numpy as np
import pytest

from shiftlab.sota_search.adapters import AdapterConfig
from shiftlab.sota_search.evaluation import evaluate
from shiftlab.sota_search.generators import WorldConfig, make_world


@pytest.mark.parametrize(
    "track,method", [("Q1", "ppe"), ("Q2", "direct"), ("Q3", "frozen"), ("Q3", "greedy")]
)
def test_evaluation_costs_reconcile_with_raw_trajectory(track, method):
    config = WorldConfig(horizon=128, delay=3)
    source = make_world(config, seed=7, partition="source")
    world = make_world(config, seed=8)
    result = evaluate(world, source, AdapterConfig(track=track, method=method), query_seed=9)
    m, t = result.metrics, result.trajectory
    assert m["labels_used"] <= m["hard_label_cap"]
    assert m["labels_used"] == t["queried"].sum()
    assert m["realized_net_cost"] == pytest.approx(
        t["realized_deployed_loss"].sum() + t["label_charge"].sum() + t["switch_charge"].sum()
    )
    expected = t["evaluator_expected_model_losses"][np.arange(128), t["deployed_model"]]
    np.testing.assert_array_equal(expected, t["expected_deployed_loss"])
    assert m["expected_available_model_regret"] >= -1e-12
    if method == "frozen":
        assert m["labels_used"] == m["switches"] == 0


def test_evaluator_refuses_shifted_source():
    world = make_world(WorldConfig(horizon=128), seed=2)
    with pytest.raises(ValueError, match="nominal"):
        evaluate(world, world, AdapterConfig(), query_seed=3)
