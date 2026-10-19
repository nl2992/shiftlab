"""Bridge standardized regression datasets to all three existing baseline tracks."""

from pathlib import Path

import numpy as np
import pandas as pd

from ..learner import Learner, LearnerSettings, decision_losses
from ..streaming import Feedback, Observation
from .schemas import Manifest, validate_frame
from .streaming import Request, replay
from .synthetic.generators import CLASSIFICATION


def evaluate_regression(directory: Path, paper: int, window=80, retrain_cost=10.0, budget=5):
    """Evaluate only when feature and label availability are known.

    Stored targets are evaluator-only: training/calibration sets are filtered by availability
    at the first test request. Online updates receive only Label messages from replay().
    This bridge uses existing Ridge baselines and does not claim classification support.
    """
    manifest = Manifest.model_validate_json((directory / "dataset_manifest.json").read_text())
    if manifest.dataset in CLASSIFICATION or manifest.dataset in ["gas_sensor", "folktables"]:
        raise ValueError(
            "Existing shared Ridge baseline requires regression; no classifier substituted"
        )
    frame = pd.read_parquet(directory / "observations.parquet")
    validate_frame(frame)
    if frame.prediction_time.isna().any() or frame.feature_available_time.isna().any():
        raise ValueError(
            "Dataset lacks a verified availability protocol; cannot run online benchmark"
        )
    test = frame[frame.split == "test"].copy()
    if not len(test):
        raise ValueError("No test rows")
    start = test.prediction_time.min()
    known = (
        frame.label_available_time.notna()
        & (frame.label_available_time < start)
        & frame.target.notna()
    )
    train = frame[(frame.split == "train") & known]
    calibration = frame[(frame.split == "calibration") & known]
    if len(train) < 20 or len(calibration) < 10:
        raise ValueError("Insufficient arrived training/calibration labels")
    settings = LearnerSettings(min(window, len(calibration)), 0.1, 20.0, 150, budget)
    methods = {1: ["frozen"], 2: ["fixed", "rolling"], 3: ["frozen", "periodic", "triggered"]}
    if paper not in methods:
        raise ValueError("paper must be 1,2,3")
    results = []
    targets = dict(zip(test.sample_id, test.target))
    for method in methods[paper]:
        learner = Learner(
            np.stack(train.features),
            train.target.to_numpy(),
            np.stack(calibration.features),
            calibration.target.to_numpy(),
            settings,
            method,
        )
        predictions = {}
        for event in replay(test):
            if isinstance(event, Request):
                observation = Observation(event.prediction_time, event.features)
                pred, radius = learner.predict(observation)
                predictions[event.sample_id] = (observation, pred, radius)
            else:
                observation, pred, _ = predictions[event.sample_id]
                learner.observe(
                    Feedback(
                        observation.time,
                        event.available_time,
                        observation.features,
                        event.target,
                        pred,
                    )
                )
        identifiers = list(predictions)
        y = np.array([targets[i] for i in identifiers])
        pred = np.array([predictions[i][1] for i in identifiers])
        radius = np.array([predictions[i][2] for i in identifiers])
        results.append(
            {
                "paper": paper,
                "method": method,
                "dataset": manifest.dataset,
                "version": manifest.version,
                "n_test": len(y),
                "mse": float(np.mean((y - pred) ** 2)),
                "coverage": float(np.mean(abs(y - pred) <= radius)),
                "mean_width": float(np.mean(2 * radius)),
                "decision_loss": float(np.mean(decision_losses(y, pred))),
                "alarms": learner.alarms,
                "num_interventions": len(learner.interventions),
                "objective": float(
                    np.sum((y - pred) ** 2) + retrain_cost * len(learner.interventions)
                ),
            }
        )
    return results
