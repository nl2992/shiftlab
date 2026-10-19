"""Explicit supervised tasks constructed from evaluator-owned arrays."""

import numpy as np


def forecast_task(values, horizon=1, lookback=4, task="regression", threshold=0.0):
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
        y = (y > threshold).astype(int)
    elif task == "volatility":
        y = np.array([np.sqrt(np.mean(np.diff(values[i : i + horizon + 1]) ** 2)) for i in index])
    elif task not in ["regression", "quantile", "rare_magnitude"]:
        raise ValueError("Unsupported task")
    return X, y, index, index + horizon
