from __future__ import annotations

import json

import pandas as pd
import pytest

from scripts.confirm_predictable_stake_portfolio import (
    CALIBRATION_SEED,
    CONFIRMATION_SEED,
    METHODS,
    run_stage,
)


def _development_manifest(path):
    manifest = path / "reports" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"selection": {"selected_eta": 0.0}, "artifact_sha256": {}}))
    return manifest


def test_gpu_or_cpu_delayed_pair_smoke_and_calibration_outputs(tmp_path):
    development = _development_manifest(tmp_path / "development")
    output = tmp_path / "calibration"
    run_stage(
        stage="calibration",
        streams=30,
        seed=CALIBRATION_SEED,
        horizon=100,
        device_name="cpu",
        output=output,
        development_manifest=development,
    )
    metrics = pd.read_parquet(output / "metrics/stream_metrics.parquet")
    calibration = pd.read_csv(output / "metrics/calibration_summary.csv")
    assert len(metrics) == 30 * 2 * len(METHODS)
    assert len(calibration) == 4
    assert metrics["budget_respected"].all()
    assert not metrics["support_violation"].any()
    paths = metrics.pivot(
        index=["scenario", "stream_id"],
        columns="method",
        values=["labels_queried", "events_processed"],
    )
    for field in ("labels_queried", "events_processed"):
        assert paths[(field, METHODS[0])].equals(paths[(field, METHODS[1])])
    assert (output / "reports/manifest.json").exists()


def test_confirmation_refuses_failed_calibration(tmp_path):
    development = _development_manifest(tmp_path / "development")
    calibration = tmp_path / "calibration.csv"
    pd.DataFrame(
        {
            "scenario": ["a", "b", "c", "d"],
            "method": ["a", "b", "c", "d"],
            "streams": [30] * 4,
            "simultaneous_one_sided_95_upper": [0.051] * 4,
            "budget_violations": [0] * 4,
            "support_violations": [0] * 4,
        }
    ).to_csv(calibration, index=False)
    with pytest.raises(ValueError, match="gated on all four calibrated upper limits"):
        run_stage(
            stage="confirmation",
            streams=30,
            seed=CONFIRMATION_SEED,
            horizon=100,
            device_name="cpu",
            output=tmp_path / "confirmation",
            development_manifest=development,
            calibration_summary=calibration,
        )
