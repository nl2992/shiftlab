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
