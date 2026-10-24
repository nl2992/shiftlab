from __future__ import annotations

import json

import pandas as pd
import pytest
import torch

from scripts.confirm_delayed_markov_predictable_bounds import (
    CALIBRATION_SEED,
    CONFIRMATION_SEED,
    run_stage,
)
from scripts.validate_delayed_markov_predictable_bounds import (
    DEFAULT_SEED_ROOT,
    run_development,
)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CPU smoke is covered by the runner")
def test_delayed_markov_screen_cuda_smoke(tmp_path):
    output = tmp_path / "delayed_markov"
    run_development(
        streams=30,
        horizon=100,
        seed=DEFAULT_SEED_ROOT,
        device_name="cuda",
        output=output,
    )

    metrics = pd.read_parquet(output / "metrics/stream_metrics.parquet")
    assert len(metrics) == 30 * 6 * 2 * 2
    assert metrics["budget_respected"].all()
    assert set(metrics["feedback_delay"]) == {1, 12}
    assert set(metrics["bound_mode"]) == {"fixed", "predictable"}
    assert metrics["events_processed"].le(100).all()
    assert metrics["labels_queried"].le(20).all()
    assert metrics["mean_feedback_delay"].isin([0.0, 1.0, 12.0]).all()

    manifest = json.loads((output / "reports/manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "development_only_not_calibration_or_confirmation"
    assert manifest["device_resolved"] == "cuda"


def test_delayed_markov_screen_cpu_smoke(tmp_path):
    output = tmp_path / "delayed_markov_cpu"
    run_development(
        streams=30,
        horizon=100,
        seed=DEFAULT_SEED_ROOT,
        device_name="cpu",
        output=output,
    )

    metrics = pd.read_parquet(output / "metrics/stream_metrics.parquet")
    assert len(metrics) == 30 * 6 * 2 * 2
    assert metrics["budget_respected"].all()
    assert (metrics["evaluator_cumulative_expected_harm_cost"] >= 0).all()
    assert (output / "metrics/paired_bound_differences.csv").is_file()


def test_delayed_markov_screen_rejects_existing_output(tmp_path):
    output = tmp_path / "nonempty"
    output.mkdir()
    (output / "sentinel").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run_development(
            streams=30,
            horizon=100,
            seed=DEFAULT_SEED_ROOT,
            device_name="cpu",
            output=output,
        )


def test_delayed_markov_calibration_cpu_smoke_is_not_certification(tmp_path):
    output = tmp_path / "calibration_smoke"
    run_stage(
        stage="calibration",
        streams=30,
        seed=CALIBRATION_SEED,
        device_name="cpu",
        output=output,
        horizon=100,
    )
    calibration = pd.read_csv(output / "metrics/calibration.csv")
    assert len(calibration) == 4
    assert calibration["streams"].eq(30).all()
    assert calibration["simultaneous_one_sided_95_upper"].gt(0.05).all()
    manifest = json.loads((output / "reports/manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "frozen_calibration"


def test_delayed_markov_confirmation_requires_passed_calibration(tmp_path):
    with pytest.raises(ValueError, match="requires the Stage 1"):
        run_stage(
            stage="confirmation",
            streams=30,
            seed=CONFIRMATION_SEED,
            device_name="cpu",
            output=tmp_path / "confirmation",
            horizon=100,
        )
