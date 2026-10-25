from pathlib import Path

import pandas as pd

from shiftlab.dive.budgeted_promotion_context_drift_calibration import (
    FAMILY_CELLS,
    _cp_upper,
    run_calibration,
)


def test_exact_upper_bound_is_monotone_and_valid():
    assert 0 < _cp_upper(0, 1000, 0.05) < 0.01
    assert _cp_upper(1, 1000, 0.05) > _cp_upper(0, 1000, 0.05)


def test_drift_calibration_smoke_records_all_registered_cells(tmp_path: Path):
    protocol = Path(__file__).parents[1] / "docs/scout_context_policy_drift_null_protocol.md"
    report_path = run_calibration(
        output=tmp_path / "drift_smoke",
        seeds=2,
        seed_offset=20_267_000,
        n=1000,
        d=4,
        device="cpu",
        protocol=protocol,
    )

    detail = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_drift_null_streams.parquet"
    )
    summary = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_drift_null_summary.parquet"
    )
    assert len(detail) == 2 * FAMILY_CELLS
    assert len(summary) == FAMILY_CELLS
    assert detail["candidate_is_monitor_null"].all()
    assert (detail["propensity_min"] > 0).all()
    assert (detail["labels_queried"] <= detail["label_budget"]).all()
    assert "smoke_only_not_calibration" in report_path.read_text(encoding="utf-8")


def test_eventwise_drift_calibration_smoke_uses_exact_bound_mode(tmp_path: Path):
    protocol = (
        Path(__file__).parents[1] / "docs/scout_context_policy_eventwise_drift_null_protocol.md"
    )
    report_path = run_calibration(
        output=tmp_path / "eventwise_drift_smoke",
        seeds=2,
        seed_offset=20_269_000,
        n=1000,
        d=4,
        device="cpu",
        bound_mode="eventwise_propensity",
        protocol=protocol,
    )

    detail = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_drift_null_streams.parquet"
    )
    summary = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_drift_null_summary.parquet"
    )
    assert len(detail) == 2 * FAMILY_CELLS
    assert len(summary) == FAMILY_CELLS
    assert set(detail.alpha_allocation.unique()) == {
        "scout_context_policy_eventwise_propensity_bound"
    }
    assert set(detail.bound_mode.unique()) == {"eventwise_propensity"}
    assert detail.candidate_is_monitor_null.all()
    assert (detail.labels_queried <= detail.label_budget).all()
    assert "Bound mode: eventwise_propensity" in report_path.read_text(encoding="utf-8")


def test_parallel_eventwise_calibration_matches_serial_metrics(tmp_path: Path):
    protocol = (
        Path(__file__).parents[1] / "docs/scout_context_policy_eventwise_drift_null_protocol.md"
    )
    common = {
        "seeds": 2,
        "seed_offset": 20_269_100,
        "n": 1000,
        "d": 4,
        "device": "cpu",
        "bound_mode": "eventwise_propensity",
        "protocol": protocol,
    }
    serial_report = run_calibration(output=tmp_path / "serial", workers=1, **common)
    parallel_report = run_calibration(output=tmp_path / "parallel", workers=2, **common)
    serial = pd.read_parquet(
        serial_report.parent.parent / "metrics/scout_context_drift_null_streams.parquet"
    )
    parallel = pd.read_parquet(
        parallel_report.parent.parent / "metrics/scout_context_drift_null_streams.parquet"
    )
    pd.testing.assert_frame_equal(serial, parallel, check_exact=False, rtol=1e-12, atol=1e-12)
