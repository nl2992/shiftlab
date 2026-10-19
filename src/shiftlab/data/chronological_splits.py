"""Chronology is enforced at entity-independent time boundaries, not arbitrary row order."""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .label_availability import purge_unavailable_labels as _purge_unavailable_labels


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


def retrospective_event_splits(frame: pd.DataFrame) -> pd.DataFrame:
    """Shared historical event boundaries with outcome purging; no availability inference."""
    frame = frame.copy()
    frame["split"] = assign_splits(frame.event_time)
    order = ["train", "validation", "calibration", "test"]
    for index, split in enumerate(order[:-1]):
        later = frame.loc[frame.split.isin(order[index + 1 :]), "event_time"]
        if len(later):
            frame.loc[(frame.split == split) & (frame.label_event_time >= later.min()), "split"] = (
                "unassigned"
            )
    return frame


def purge_unavailable_labels(frame: pd.DataFrame) -> pd.DataFrame:
    """Compatibility wrapper for the shared label-availability implementation."""
    return _purge_unavailable_labels(frame)
