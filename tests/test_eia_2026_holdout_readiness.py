from __future__ import annotations

from datetime import datetime

import numpy as np
import torch

from scripts.audit_eia_2026_holdout_readiness import _eligible_rows, _summarize_rows
from scripts.evaluate_eia_retraining_frontier import _simulate_policy
from scripts.run_eia_2026_out_of_time_confirmation import (
    _block_bootstrap_intervals,
    _split_arrays,
)


def _epoch(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp())


def test_eligible_forecasts_align_features_at_t_with_demand_at_t_plus_one():
    start = _epoch("2026-01-01T00:00:00Z")
    series = {
        f"EBA.CISO-ALL.{kind}.H": {
            start: 10.0,
            start + 3600: 11.0,
            start + 7200: 12.0,
        }
        for kind in ("D", "DF", "NG", "TI")
    }

    rows = _eligible_rows(series, "CISO")

    assert [row["event_time"] for row in rows] == [start, start + 3600]
    assert [row["target_time"] for row in rows] == [start + 3600, start + 7200]
    assert all(row["split"] == "test" and row["complete_features"] for row in rows)


def test_missing_predictor_is_counted_but_not_marked_complete():
    start = _epoch("2026-01-01T00:00:00Z")
    series = {
        f"EBA.CISO-ALL.{kind}.H": {start: 10.0, start + 3600: 11.0}
        for kind in ("D", "DF", "NG", "TI")
    }
    series["EBA.CISO-ALL.NG.H"][start] = None

    rows = _eligible_rows(series, "CISO")
    summary = _summarize_rows(rows)

    assert summary["test"]["rows_with_observed_next_hour_target"] == 1
    assert summary["test"]["rows_with_complete_four_feature_vector"] == 0


def test_gap_summary_reports_nonhourly_event_intervals():
    first = _epoch("2026-01-01T00:00:00Z")
    rows = [
        {"event_time": first, "split": "test", "complete_features": True},
        {"event_time": first + 7200, "split": "test", "complete_features": True},
    ]

    summary = _summarize_rows(rows)

    assert summary["test"]["non_hourly_gaps_in_complete_event_sequence"] == 1
    assert summary["test"]["largest_event_gap_seconds"] == 7200


def test_split_arrays_preserve_gaps_without_interpolating():
    train_start = _epoch("2019-01-01T00:00:00Z")
    calibration_start = _epoch("2025-01-01T00:00:00Z")
    test_start = _epoch("2026-01-01T00:00:00Z")
    times = [
        train_start,
        train_start + 3600,
        train_start + 7200,
        calibration_start,
        calibration_start + 3600,
        calibration_start + 7200,
        test_start,
        test_start + 3600,
        test_start + 7200,
        test_start + 10800,
    ]
    series = {
        f"EBA.CISO-ALL.{kind}.H": {time: float(index + 1) for index, time in enumerate(times)}
        for kind in ("D", "DF", "NG", "TI")
    }
    for kind in ("D", "DF", "NG", "TI"):
        series[f"EBA.CISO-ALL.{kind}.H"][test_start + 3600] = 50.0
    series["EBA.CISO-ALL.NG.H"][test_start + 3600] = None

    splits = _split_arrays(series, "CISO")

    assert len(splits["train"][1]) == 2
    assert len(splits["calibration"][1]) == 2
    assert len(splits["test"][1]) == 2
    assert list(splits["test"][2]) == [test_start, test_start + 7200]


def test_paired_block_bootstrap_returns_zero_for_identical_predictions(monkeypatch):
    monkeypatch.setattr("scripts.run_eia_2026_out_of_time_confirmation.BOOTSTRAP_DRAWS", 50)
    start = _epoch("2026-01-01T00:00:00Z")
    times = start + np.arange(20, dtype=np.int64) * 168 * 3600
    y = [1.0] * 20
    predictions = {
        policy: [1.0] * 20 for policy in ("frozen", "weekly", "monthly", "error_trigger")
    }

    intervals = _block_bootstrap_intervals(
        times=np.asarray(times, dtype=float),
        y=np.asarray(y, dtype=float),
        predictions={key: np.asarray(value) for key, value in predictions.items()},
        domain="CISO",
        delay=0,
    )

    assert len(intervals) == 9
    assert all(row["point_difference"] == 0 for row in intervals)
    assert all(row["ci_2_5"] == 0 and row["ci_97_5"] == 0 for row in intervals)


def test_frozen_policy_simulation_accepts_sparse_monotone_test_events():
    rng = np.random.default_rng(7)
    train_x = rng.normal(size=(64, 4))
    train_y = train_x @ np.asarray([0.5, -0.2, 0.1, 0.3]) + rng.normal(scale=0.1, size=64)
    train_time = np.arange(64, dtype=float) * 3600
    calibration_x = rng.normal(size=(200, 4))
    calibration_y = calibration_x @ np.asarray([0.5, -0.2, 0.1, 0.3]) + rng.normal(
        scale=0.1, size=200
    )
    calibration_time = 100_000 + np.arange(200, dtype=float) * 3600
    test_x = rng.normal(size=(40, 4))
    test_y = test_x @ np.asarray([0.5, -0.2, 0.1, 0.3]) + rng.normal(scale=0.1, size=40)
    test_time = 1_000_000 + np.arange(40, dtype=float) * 3600
    test_time[10:] += 3600

    prediction, details = _simulate_policy(
        policy="frozen",
        delay_hours=0,
        x=test_x,
        y=test_y,
        event_time=test_time,
        label_event_time=test_time + 3600,
        train_x=train_x,
        train_y=train_y,
        train_label_event_time=train_time + 3600,
        calibration_x=calibration_x,
        calibration_y=calibration_y,
        calibration_time=calibration_time,
        device=torch.device("cpu"),
    )

    assert np.isfinite(prediction).all()
    assert details["test_n"] == 40
    assert details["updates_after_test_start"] == 0
