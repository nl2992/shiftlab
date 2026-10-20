from types import SimpleNamespace

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor

from scripts.evaluate_sequential_adaptation import (
    AuditedLearner,
    cost_frontier_summary,
    initial_rows,
)
from shiftlab.streaming import Feedback


def test_initial_adaptation_labels_require_strictly_earlier_known_availability():
    frame = pd.DataFrame(
        {
            "split": ["train", "train", "train", "calibration"],
            "prediction_time": [0, 1, 2, 3],
            "feature_available_time": [0, 1, 5, np.nan],
            "label_available_time": [4, 5, np.nan, 5],
            "target": [1.0, 2.0, 3.0, 4.0],
        }
    )
    eligible = initial_rows(frame, "train", cutoff=5)
    assert eligible.prediction_time.tolist() == [0]

    eligible_calibration = initial_rows(frame, "calibration", cutoff=5)
    assert eligible_calibration.empty


def test_random_forest_can_refit_only_after_periodic_feedback_arrives():
    rng = np.random.default_rng(12)
    X = rng.normal(size=(60, 3))
    y = X[:, 0] - X[:, 1]
    learner = AuditedLearner(
        X[:40],
        y[:40],
        X[40:60],
        y[40:60],
        SimpleNamespace(window=20, alpha=0.1, threshold=5.0, period=1, budget=1),
        "periodic",
        model_family="random_forest",
        model_seed=7,
    )
    assert isinstance(learner.model, RandomForestRegressor)
    learner.observe(
        Feedback(time=60, available_at=68, features=tuple(X[0]), target=float(y[0]), prediction=0.0)
    )
    assert learner.interventions == [68]
    assert learner.fit_audit == [
        {
            "fit_feedback_available_time": 68,
            "arrived_feedback_count": 1,
            "method": "periodic",
            "model_family": "random_forest",
        }
    ]


def test_histogram_gradient_boosting_can_refit_after_arrived_feedback():
    rng = np.random.default_rng(18)
    X = rng.normal(size=(60, 3))
    y = X[:, 0] ** 2 - X[:, 1]
    learner = AuditedLearner(
        X[:40],
        y[:40],
        X[40:60],
        y[40:60],
        SimpleNamespace(window=20, alpha=0.1, threshold=5.0, period=1, budget=1),
        "periodic",
        model_family="hist_gradient_boosting",
        model_seed=9,
    )
    assert isinstance(learner.model, HistGradientBoostingRegressor)
    learner.observe(
        Feedback(time=60, available_at=68, features=tuple(X[0]), target=float(y[0]), prediction=0.0)
    )
    assert learner.interventions == [68]
    assert learner.fit_audit[0]["model_family"] == "hist_gradient_boosting"


def test_cost_frontier_uses_cumulative_loss_and_resource_charge():
    records = [
        {
            "schedule": "abrupt",
            "policy": "hold",
            "seed": 1,
            "mse": 3.0,
            "test_n": 10,
            "resource_spent": 0.0,
            "training_seconds": 1.0,
            "inference_seconds": 2.0,
            "adaptation_seconds": 0.0,
            "update_count": 0,
        },
        {
            "schedule": "abrupt",
            "policy": "refit",
            "seed": 1,
            "mse": 2.0,
            "test_n": 10,
            "resource_spent": 4.0,
            "training_seconds": 2.0,
            "inference_seconds": 2.0,
            "adaptation_seconds": 1.0,
            "update_count": 1,
        },
        {
            "schedule": "abrupt",
            "policy": "wasteful",
            "seed": 1,
            "mse": 4.0,
            "test_n": 10,
            "resource_spent": 8.0,
            "training_seconds": 3.0,
            "inference_seconds": 2.0,
            "adaptation_seconds": 1.0,
            "update_count": 1,
        },
    ]
    summary = cost_frontier_summary(records).set_index("policy")
    assert summary.pareto_efficient.to_dict() == {
        "hold": True,
        "refit": True,
        "wasteful": False,
    }
    assert summary.mean_objective_at_resource_price_1.to_dict() == {
        "hold": 30.0,
        "refit": 24.0,
        "wasteful": 48.0,
    }
