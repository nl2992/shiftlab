"""Capability-style messages. This is API separation, not a hostile-code sandbox."""

import heapq
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Request:
    sample_id: str
    prediction_time: int | float
    features: tuple[float, ...]
    entity_id: str | None
    domain_id: str | None
    decision_context: str | None
    feature_reference: str | None = None


@dataclass(frozen=True)
class Label:
    sample_id: str
    available_time: int | float
    target: float


def replay(frame: pd.DataFrame):
    """Yield request then labels available by this time; unknown availability is withheld.

    All requests at the same timestamp precede all feedback at that timestamp.
    Oracle regime, split, provenance and targets are absent from requests.
    """
    if frame.prediction_time.isna().any():
        raise ValueError("Unknown prediction times; define an explicit availability protocol first")
    pending = []
    ordered = frame.sort_values(["prediction_time", "sample_id"])
    for now, group in ordered.groupby("prediction_time", sort=True):
        while pending and pending[0][0] < now:
            available, identifier, target = heapq.heappop(pending)
            yield Label(identifier, available, target)
        for row in group.itertuples():
            if pd.isna(row.feature_available_time) or row.feature_available_time > now:
                raise ValueError("Features unavailable at prediction time")
            yield Request(
                row.sample_id,
                now,
                tuple(row.features),
                row.entity_id,
                row.domain_id,
                row.decision_context,
                getattr(row, "feature_reference", None),
            )
            if pd.notna(row.target) and pd.notna(row.label_available_time):
                if row.label_available_time < now:
                    raise ValueError(
                        "Target already observable before prediction; audit task construction"
                    )
                heapq.heappush(
                    pending, (row.label_available_time, row.sample_id, float(row.target))
                )
        while pending and pending[0][0] == now:
            available, identifier, target = heapq.heappop(pending)
            yield Label(identifier, available, target)
