from pathlib import Path

import pandas as pd

from shiftlab.dive.budgeted_promotion_context_drift_development import (
    FAMILY_CELLS,
    METHODS,
    run_development,
)


def test_positive_drift_development_smoke_records_all_methods_and_cells(tmp_path: Path):
    protocol = (
        Path(__file__).parents[1]
        / "docs/scout_context_policy_positive_drift_development_protocol.md"
    )
    report_path = run_development(
        output=tmp_path / "positive_drift_smoke",
        seeds=2,
        seed_offset=20_268_900,
        n=1000,
        d=4,
        device="cpu",
        protocol=protocol,
        bootstrap_draws=100,
    )

    root = report_path.parent.parent
    detail = pd.read_parquet(root / "metrics/scout_context_drift_development_streams.parquet")
    summary = pd.read_parquet(root / "metrics/scout_context_drift_development_cells.parquet")
    contrasts = pd.read_parquet(root / "metrics/scout_context_drift_development_contrasts.parquet")
    assert len(detail) == 2 * FAMILY_CELLS * len(METHODS)
    assert len(summary) == FAMILY_CELLS * len(METHODS)
    assert set(detail.alpha_allocation.unique()) == set(METHODS)
    assert len(contrasts) == 2
    assert detail.propensity_min.gt(0).all()
    assert (detail.labels_queried <= detail.label_budget).all()
    assert not detail.duplicated(["scenario", "budget_rate", "seed", "alpha_allocation"]).any()
    assert "exploratory development" in report_path.read_text(encoding="utf-8")
