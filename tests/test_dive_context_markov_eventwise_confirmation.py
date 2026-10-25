from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from shiftlab.dive.budgeted_promotion_context_markov_eventwise_confirmation import (
    FAMILY_CELLS,
    METHODS,
    run_confirmation,
)


def test_eventwise_markov_confirmation_smoke_has_complete_matched_grid(tmp_path: Path):
    protocol = (
        Path(__file__).parents[1]
        / "docs/scout_context_policy_eventwise_markov_confirmation_protocol.md"
    )
    report_path = run_confirmation(
        output=tmp_path / "eventwise_markov_confirmation_smoke",
        protocol=protocol,
        seeds=2,
        seed_offset=20_272_010,
        n=1000,
        d=4,
        device="cpu",
        workers=2,
        bootstrap_draws=200,
    )
    root = report_path.parent.parent
    detail = pd.read_parquet(root / "metrics/eventwise_markov_confirmation_streams.parquet")
    summary = pd.read_parquet(root / "metrics/eventwise_markov_confirmation_cells.parquet")
    contrasts = pd.read_parquet(root / "metrics/eventwise_markov_confirmation_contrasts.parquet")
    manifest = json.loads((report_path.parent / "manifest.json").read_text(encoding="utf-8"))
    key = ["scenario", "budget_rate", "seed", "alpha_allocation"]

    assert len(detail) == 2 * FAMILY_CELLS * len(METHODS)
    assert detail[key].drop_duplicates().shape[0] == len(detail)
    assert set(detail["alpha_allocation"]) == set(METHODS)
    assert detail["propensity_min"].gt(0).all()
    assert not (detail["labels_queried"] > detail["label_budget"]).any()
    assert len(summary) == FAMILY_CELLS * len(METHODS)
    assert set(contrasts["contrast"]) == {
        "eventwise_minus_rank",
        "eventwise_minus_nested_volume",
        "eventwise_minus_minimum_bound",
    }
    assert manifest["status"] == "smoke_only_not_confirmation"
    assert manifest["inference"]["primary_gate_pass"] is False


def test_eventwise_query_confirmation_smoke_uses_matching_calibration(tmp_path: Path):
    root = Path(__file__).parents[1]
    protocol = root / "docs/scout_context_eventwise_query_confirmation_protocol.md"
    calibration = (
        root / "outputs/scout_context_eventwise_query_null_calibration_1000/reports/manifest.json"
    )
    report_path = run_confirmation(
        output=tmp_path / "eventwise_query_confirmation_smoke",
        protocol=protocol,
        seeds=2,
        seed_offset=21_209_010,
        n=1000,
        d=4,
        device="cpu",
        workers=2,
        bootstrap_draws=200,
        bootstrap_seed=21_300_600,
        query_policies=("uniform", "variance"),
        persistence_values=(0.0, 0.8),
        null_calibration_manifest=calibration,
    )
    output = report_path.parent.parent
    detail = pd.read_parquet(output / "metrics/eventwise_markov_confirmation_streams.parquet")
    summary = pd.read_parquet(output / "metrics/eventwise_markov_confirmation_cells.parquet")
    contrasts = pd.read_parquet(output / "metrics/eventwise_markov_confirmation_contrasts.parquet")
    manifest = json.loads((report_path.parent / "manifest.json").read_text(encoding="utf-8"))

    expected_cells = 3 * 2 * 2 * 2 * 2
    assert len(detail) == 2 * expected_cells * len(METHODS) * 2
    assert not detail.duplicated(
        ["scenario", "query_policy", "budget_rate", "seed", "alpha_allocation"]
    ).any()
    assert set(detail.query_policy) == {"uniform", "variance"}
    assert set(detail.context_persistence) == {0.0, 0.8}
    assert len(summary) == expected_cells * len(METHODS) * 2
    assert set(contrasts.contrast) == {
        "variance_eventwise_minus_rank",
        "variance_eventwise_minus_nested_volume",
        "variance_eventwise_minus_minimum_bound",
        "variance_eventwise_minus_uniform_eventwise",
    }
    assert manifest["prerequisite_null_calibration"]["status"] == "passed"
    assert manifest["status"] == "smoke_only_not_confirmation"
