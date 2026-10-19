"""Chronology is enforced at entity-independent time boundaries, not arbitrary row order."""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


def assign_splits(times, fractions=(0.5, 0.15, 0.15)) -> np.ndarray:
    values = pd.Series(times)
    if values.isna().any() or not values.is_monotonic_increasing:
        raise ValueError("Sorted known times required")
    unique = values.unique()
    if len(unique) < 4 or sum(fractions) >= 1 or min(fractions) <= 0:
        raise ValueError("Need at least four time groups and positive fractions summing below one")
    cuts = [
        unique[min(len(unique) - 1, max(1, int(len(unique) * f)))] for f in np.cumsum(fractions)
    ]
    return np.select(
        [values < cuts[0], values < cuts[1], values < cuts[2]],
        ["train", "validation", "calibration"],
        default="test",
    )


def fit_training_scaler(X: np.ndarray, splits: np.ndarray) -> StandardScaler:
    mask = np.asarray(splits) == "train"
    if not mask.any():
        raise ValueError("No training rows")
    return StandardScaler().fit(X[mask])


def purge_unavailable_labels(frame: pd.DataFrame) -> pd.DataFrame:
    """Withhold boundary-crossing labels from fitting/calibration partitions.

    Unknown real availability cannot establish a valid online protocol and is left unknown.
    Test rows are evaluator-owned; absent test labels remain eligible for offline scoring.
    """
    frame = frame.copy()
    order = ["train", "validation", "calibration", "test"]
    for index, split in enumerate(order[:-1]):
        next_times = frame.loc[frame.split.isin(order[index + 1 :]), "prediction_time"].dropna()
        if len(next_times):
            cutoff = next_times.min()
            mask = (
                (frame.split == split)
                & frame.label_available_time.notna()
                & (frame.label_available_time >= cutoff)
            )
            frame.loc[mask, "split"] = "unassigned"
    return frame
