from __future__ import annotations

import pandas as pd
import pytest

from scripts.confirm_matched_path_bound_ablation import (
    CALIBRATION_SEED,
    CONFIRMATION_SEED,
    run_stage,
)
from scripts.run_matched_path_bound_ablation import (
    DEFAULT_SEED,
    SCHEDULES,
    build_schedule,
    run,
)


@pytest.mark.parametrize("name,low,high,slots", SCHEDULES)
def test_propensity_schedules_have_registered_mean_and_support(name, low, high, slots):
    schedule = build_schedule(
        name=name, low=low, high=high, high_slots=slots, horizon=100, streams=10
    )
    assert schedule.shape == (100, 10)
    assert schedule.min() == pytest.approx(low)
    assert schedule.max() == pytest.approx(high)
    assert schedule.mean() == pytest.approx(0.20)


def test_matched_path_grid_shares_labels_and_constant_q_is_identity(tmp_path):
    output = tmp_path / "matched_path"
    run(
        streams=30,
        seed=DEFAULT_SEED,
        horizon=100,
        device_name="cpu",
        output=output,
    )
    metrics = pd.read_parquet(output / "metrics/stream_metrics.parquet")
    assert len(metrics) == 30 * 6 * len(SCHEDULES) * 2
    assert metrics["budget_respected"].all()
    paths = metrics.pivot(
        index=["scenario", "schedule", "stream_id"],
        columns="bound_mode",
        values=["labels_queried", "events_processed", "registered_events"],
    )
    for field in ("labels_queried", "events_processed", "registered_events"):
        assert paths[(field, "fixed")].equals(paths[(field, "eventwise")])
    constant = metrics[metrics["schedule"] == "constant_q20"].pivot(
        index=["scenario", "stream_id"],
        columns="bound_mode",
        values="post_onset_detection",
    )
    assert constant["fixed"].equals(constant["eventwise"])


def test_matched_path_calibration_smoke_and_confirmation_gate(tmp_path):
    output = tmp_path / "calibration_smoke"
    run_stage(
        stage="calibration",
        streams=30,
        seed=CALIBRATION_SEED,
        horizon=100,
        device_name="cpu",
        output=output,
    )
    calibration = pd.read_csv(output / "metrics/calibration.csv")
    assert len(calibration) == 4
    assert calibration["streams"].eq(30).all()
    assert calibration["simultaneous_one_sided_95_upper"].gt(0.05).all()
    with pytest.raises(ValueError, match="requires the independent calibration"):
        run_stage(
            stage="confirmation",
            streams=30,
            seed=CONFIRMATION_SEED,
            horizon=100,
            device_name="cpu",
            output=tmp_path / "confirmation",
        )
