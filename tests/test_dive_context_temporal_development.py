from pathlib import Path

import pandas as pd

from shiftlab.dive.budgeted_promotion_context_temporal_development import run_development


def test_temporal_development_smoke_has_complete_matched_grid(tmp_path: Path):
    protocol = (
        Path(__file__).parents[1]
        / "docs/scout_context_policy_eventwise_temporal_development_protocol.md"
    )
    report_path = run_development(
        output=tmp_path / "temporal_development_smoke",
        protocol=protocol,
        seeds=2,
        seed_offset=20_272_100,
        n=1000,
        d=4,
        device="cpu",
        workers=2,
        bootstrap_draws=200,
    )
    detail = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_temporal_development_streams.parquet"
    )
    cells = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_temporal_development_cells.parquet"
    )
    contrasts = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_temporal_development_contrasts.parquet"
    )
    assert len(detail) == 2 * 48 * 4
    assert len(cells) == 48 * 4
    assert detail.groupby(["scenario", "budget_rate", "alpha_allocation"]).size().eq(2).all()
    assert set(detail.context_prevalence_schedule.unique()) == {
        "gradual_up",
        "gradual_down",
        "recurring_low_first",
        "recurring_high_first",
    }
    assert set(detail.context_signal_strength.unique()) == {0.0, 0.05, 0.1}
    assert detail.propensity_min.gt(0).all()
    assert int(cells.cap_violations.sum()) == 0
    assert contrasts.contrast.nunique() == 3
    assert "smoke_only" in report_path.read_text(encoding="utf-8")
