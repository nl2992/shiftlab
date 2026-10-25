from pathlib import Path

import pandas as pd

from shiftlab.dive.budgeted_promotion_context_drift_confirmation import run_confirmation


def test_confirmation_smoke_writes_complete_matched_rows(tmp_path: Path):
    protocol = (
        Path(__file__).parents[1]
        / "docs/scout_context_policy_eventwise_bound_confirmation_protocol.md"
    )
    report_path = run_confirmation(
        output=tmp_path / "confirmation_smoke",
        protocol=protocol,
        seeds=2,
        seed_offset=20_270_000,
        n=1000,
        d=4,
        device="cpu",
        workers=2,
        bootstrap_draws=200,
    )
    detail = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_drift_confirmation_streams.parquet"
    )
    cells = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_drift_confirmation_cells.parquet"
    )
    contrasts = pd.read_parquet(
        report_path.parent.parent / "metrics/scout_context_drift_confirmation_contrasts.parquet"
    )
    assert len(detail) == 2 * 24 * 4
    assert len(cells) == 24 * 4
    assert len(contrasts) == 3
    assert detail.groupby(["scenario", "budget_rate", "alpha_allocation"]).size().eq(2).all()
    assert detail["propensity_min"].gt(0).all()
    assert (detail["labels_queried"] <= detail["label_budget"]).all()
    assert int(cells["cap_violations"].sum()) == 0
    assert "smoke_only_not_confirmation" in report_path.read_text(encoding="utf-8")
