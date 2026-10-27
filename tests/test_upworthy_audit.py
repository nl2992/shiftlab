"""Tests for source-level Upworthy experiment data validation."""

from __future__ import annotations

import pandas as pd
import pytest

from scripts.audit_upworthy_exploratory import summarize


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "created_at": ["2013-06-24 23:00:00", "2014-01-12 00:00:00", "2013-06-25 00:00:00"],
            "updated_at": ["2013-06-24 23:00:00"] * 3,
            "clickability_test_id": ["a", "a", "b"],
            "impressions": [100, 100, 50],
            "clicks": [10, 12, 4],
            "winner": [False, True, True],
            "test_week": [201326, 201326, 201326],
        }
    )


def test_summary_flags_experiment_if_any_package_is_in_buffered_window() -> None:
    result = summarize(valid_frame())
    assert result["experiments"] == 2
    assert result["experiments_with_one_arm"] == 1
    assert (
        result["conservative_assignment_risk_window"][
            "experiments_with_any_package_created_in_window"
        ]
        == 2
    )
    assert result["publisher_flagged_problem_column_present"] is False


def test_summary_rejects_impossible_aggregate_counts() -> None:
    frame = valid_frame()
    frame.loc[0, "clicks"] = 101
    with pytest.raises(ValueError, match="Invalid arm exposure or click count"):
        summarize(frame)


def test_summary_rejects_unparseable_creation_time() -> None:
    frame = valid_frame()
    frame.loc[0, "created_at"] = "unknown"
    with pytest.raises(ValueError, match="timestamps cannot be parsed"):
        summarize(frame)
