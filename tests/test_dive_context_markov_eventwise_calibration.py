from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from shiftlab.dive.budgeted_promotion_context_markov_eventwise_calibration import (
    FAMILY_CELLS,
    _cp_upper,
    run_calibration,
)


def test_eventwise_markov_null_smoke_checks_all_cells(tmp_path: Path):
    protocol = (
        Path(__file__).parents[1] / "docs/scout_context_policy_eventwise_markov_null_protocol.md"
    )
    report_path = run_calibration(
        output=tmp_path / "eventwise_markov_null_smoke",
        protocol=protocol,
        seeds=2,
        seed_offset=20_272_000,
        n=1000,
        d=4,
        device="cpu",
        workers=2,
    )
    metrics = report_path.parent.parent / "metrics/eventwise_markov_null_streams.parquet"
    summaries = report_path.parent.parent / "metrics/eventwise_markov_null_summary.parquet"
    detail = pd.read_parquet(metrics)
    summary = pd.read_parquet(summaries)
    manifest = json.loads((report_path.parent / "manifest.json").read_text(encoding="utf-8"))

    assert len(detail) == 2 * FAMILY_CELLS
    assert detail[["scenario", "budget_rate", "seed", "alpha_allocation"]].drop_duplicates().shape[
        0
    ] == len(detail)
    assert detail["alpha_allocation"].eq("scout_context_policy_eventwise_propensity_bound").all()
    assert detail["candidate_is_monitor_null"].all()
    assert detail["propensity_min"].gt(0).all()
    assert not (detail["labels_queried"] > detail["label_budget"]).any()
    assert len(summary) == FAMILY_CELLS
    assert manifest["status"] == "smoke_only_not_calibration"
    assert manifest["inference"]["calibration_pass"] is False
    assert "smoke_only_not_calibration" in report_path.read_text(encoding="utf-8")


def test_clopper_pearson_zero_event_upper_is_exact():
    alpha = 0.05 / FAMILY_CELLS
    expected = 1 - alpha ** (1 / 1000)
    assert _cp_upper(0, 1000, alpha) == pytest.approx(expected)
