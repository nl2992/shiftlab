"""Explicit supervised tasks constructed from evaluator-owned arrays."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TaskSpec:
    name: str
    kind: str
    definition: str
    label_availability_rule: str


TASKS = {
    "regression": TaskSpec(
        "regression",
        "regression",
        "future value at fixed horizon",
        "target event plus measured release lag",
    ),
    "quantile": TaskSpec(
        "quantile",
        "regression",
        "same response, evaluated by pinball loss at a prespecified quantile",
        "target event plus measured release lag",
    ),
    "volatility": TaskSpec(
        "volatility",
        "regression",
        "RMS first differences over the entire future horizon",
        "last future outcome and all constituent observations available",
    ),
    "rare_magnitude": TaskSpec(
        "rare_magnitude",
        "regression",
        "positive excess above a fixed threshold at the target horizon; zero otherwise",
        "target event plus measured release lag",
    ),
    "binary": TaskSpec(
        "binary",
        "classification",
        "future value exceeds a fixed threshold",
        "target event plus measured release lag",
    ),
    "exceedance": TaskSpec(
        "exceedance",
        "classification",
        "future threshold exceedance",
        "target event plus measured release lag",
    ),
    "rare_event": TaskSpec(
        "rare_event",
        "classification",
        "exceedance of a threshold selected without test labels",
        "target event plus measured release lag",
    ),
    "multiclass": TaskSpec(
        "multiclass",
        "classification",
        "future value falls in prespecified ordered bins",
        "target event plus measured release lag",
    ),
}


def forecast_task(
    values, horizon=1, lookback=4, task="regression", threshold=0.0, class_boundaries=None
):
    """No future-valued features. Label index is returned for availability mapping.

    Volatility is future RMS first differences, not a claim about latent economic risk.
    Quantile forecasting uses the same response with a quantile loss at evaluation.
    """
    values = np.asarray(values, dtype=float)
    if horizon < 1 or lookback < 1 or len(values) <= horizon + lookback:
        raise ValueError("Insufficient series or invalid horizon/lookback")
    index = np.arange(lookback - 1, len(values) - horizon)
    X = np.stack([values[i - lookback + 1 : i + 1] for i in index])
    y = values[index + horizon]
    if task in ["binary", "exceedance", "rare_event"]:
        y = np.where(np.isnan(y), np.nan, (y > threshold).astype(float))
    elif task == "multiclass":
        bins = np.asarray(class_boundaries, dtype=float)
        if (
            bins.ndim != 1
            or not len(bins)
            or not np.isfinite(bins).all()
            or not np.all(np.diff(bins) > 0)
        ):
            raise ValueError(
                "Multiclass bins must be explicitly supplied, finite and strictly increasing; never fit them on test outcomes"
            )
        y = np.where(np.isnan(y), np.nan, np.digitize(y, bins).astype(float))
    elif task == "rare_magnitude":
        y = np.maximum(y - threshold, 0)
    elif task == "volatility":
        y = np.array([np.sqrt(np.mean(np.diff(values[i : i + horizon + 1]) ** 2)) for i in index])
    elif task not in ["regression", "quantile", "rare_magnitude"]:
        raise ValueError("Unsupported task")
    return X, y, index, index + horizon


def quantile_loss(target, prediction, quantile=0.9):
    if not 0 < quantile < 1:
        raise ValueError("quantile must lie in (0,1)")
    error = np.asarray(target) - np.asarray(prediction)
    return np.maximum(quantile * error, (quantile - 1) * error)
