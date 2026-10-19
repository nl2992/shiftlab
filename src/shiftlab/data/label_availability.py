"""Shared, conservative rules for whether an outcome may enter a learner at a cutoff."""

import pandas as pd


def labels_available_before(frame: pd.DataFrame, cutoff: float) -> pd.Series:
    """Return labels known strictly before ``cutoff``; unknown times and targets stay masked.

    Strict comparison matches replay semantics: requests at a timestamp are issued before
    feedback arriving at that same timestamp.
    """
    return (
        frame.label_available_time.notna()
        & (frame.label_available_time < cutoff)
        & frame.target.notna()
    )


def labels_available_by(frame: pd.DataFrame, cutoff: float) -> pd.Series:
    """Return labels known by ``cutoff`` after same-time requests have been issued."""
    return (
        frame.label_available_time.notna()
        & (frame.label_available_time <= cutoff)
        & frame.target.notna()
    )


def purge_unavailable_labels(frame: pd.DataFrame) -> pd.DataFrame:
    """Mark boundary-crossing calibration/training labels unassigned.

    Unknown real availability remains unknown; downstream learner fitting must additionally use
    ``labels_available_before`` and cannot infer an arrival time from event time alone.
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
