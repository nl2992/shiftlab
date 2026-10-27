import numpy as np
import pandas as pd
import pytest

from scripts.evaluate_gas_sensor_candidates import (
    _batch_ids,
    _cost_matrices,
    _equal_batch_average,
    _metrics,
    _select_by_validation,
)


def test_batch_ids_require_and_parse_source_batch_names():
    parsed = _batch_ids(pd.Series(["batch-1", "batch-10"], dtype="string"))
    np.testing.assert_array_equal(parsed, [1, 10])
    with pytest.raises(ValueError, match="batch-<integer>"):
        _batch_ids(pd.Series(["domain-a"], dtype="string"))


def test_class_six_cost_scenarios_only_scale_class_six_errors():
    costs = _cost_matrices(np.array([1, 2, 3, 4, 5, 6]))
    assert costs["symmetric"][0, 5] == 1.0
    assert costs["class6_x2"][0, 5] == 2.0
    assert costs["class6_x5"][0, 5] == 5.0
    assert costs["class6_x5"][5, 5] == 0.0


def test_validation_selector_can_keep_incumbent_and_uses_stable_tie_break():
    rows = [
        {"model": "retrained", "mean_decision_cost": 0.4},
        {"model": "incumbent", "mean_decision_cost": 0.2},
    ]
    assert _select_by_validation(rows) == "incumbent"
    assert (
        _select_by_validation(
            [
                {"model": "z_model", "mean_decision_cost": 0.1},
                {"model": "a_model", "mean_decision_cost": 0.1},
            ]
        )
        == "a_model"
    )


def test_equal_batch_summary_weights_domains_equally_not_by_row_count():
    rows = [
        {
            "accuracy": 1.0,
            "macro_f1": 1.0,
            "multiclass_log_loss": 0.0,
            "multiclass_brier": 0.0,
            "mean_decision_cost": 0.0,
        },
        {
            "accuracy": 0.0,
            "macro_f1": 0.0,
            "multiclass_log_loss": 2.0,
            "multiclass_brier": 2.0,
            "mean_decision_cost": 1.0,
        },
    ]
    result = _equal_batch_average(rows, n_total=101)
    assert result["n"] == 101
    assert result["accuracy"] == 0.5
    assert result["mean_decision_cost"] == 0.5
    assert result["aggregation"].startswith("arithmetic mean")


def test_metrics_score_posterior_expected_cost_action():
    classes = np.array([1, 2, 6])
    costs = np.ones((3, 3)) - np.eye(3)
    costs[:, 2] *= 5.0
    y = np.array([6])
    probability = np.array([[0.42, 0.42, 0.16]])
    result = _metrics(y, probability, classes, costs)
    # Predictive argmax ties at class 1, but expected-cost action prefers class 6.
    assert result["accuracy"] == 0.0
    assert result["mean_decision_cost"] == 0.0
