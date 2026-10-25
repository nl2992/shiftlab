from pathlib import Path

import pandas as pd

from shiftlab.dive.budgeted_promotion_context_temporal_calibration import run_calibration


def test_temporal_null_calibration_smoke_has_all_cells_and_no_false_nulls(tmp_path: Path):
    protocol = (
        Path(__file__).parents[1] / "docs/scout_context_policy_eventwise_temporal_null_protocol.md"
    )
    report_path = run_calibration(
        output=tmp_path / "temporal_null_smoke",
        protocol=protocol,
        seeds=2,
        seed_offset=20_272_150,
        n=1000,
        d=4,
        device="cpu",
        workers=2,
    )
    detail = pd.read_parquet(
        report_path.parent.parent / "metrics/eventwise_temporal_null_streams.parquet"
    )
    summary = pd.read_parquet(
        report_path.parent.parent / "metrics/eventwise_temporal_null_summary.parquet"
    )
    assert len(detail) == 2 * 16
    assert len(summary) == 16
    assert detail.candidate_is_monitor_null.astype(bool).all()
    assert detail.propensity_min.gt(0).all()
    assert int(detail.cap_violation.sum()) == 0
    assert summary.streams.eq(2).all()
    assert not summary.cell_pass.any()
    assert "smoke_only_not_calibration" in report_path.read_text(encoding="utf-8")
