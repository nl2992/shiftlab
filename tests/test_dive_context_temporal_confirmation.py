import json
from pathlib import Path

import pandas as pd

from shiftlab.dive.budgeted_promotion_context_temporal_confirmation import run_confirmation


def test_temporal_confirmation_smoke_verifies_calibration_and_complete_grid(tmp_path: Path):
    root = Path(__file__).parents[1]
    protocol = root / "docs/scout_context_policy_eventwise_temporal_confirmation_protocol.md"
    calibration = (
        root / "outputs/scout_context_policy_eventwise_temporal_null_1000/reports/manifest.json"
    )
    report_path = run_confirmation(
        output=tmp_path / "temporal_confirmation_smoke",
        protocol=protocol,
        calibration_manifest=calibration,
        seeds=2,
        seed_offset=20_272_180,
        n=1000,
        d=4,
        device="cpu",
        workers=2,
        bootstrap_draws=200,
    )
    output = report_path.parent.parent
    detail = pd.read_parquet(output / "metrics/eventwise_temporal_confirmation_streams.parquet")
    cells = pd.read_parquet(output / "metrics/eventwise_temporal_confirmation_cells.parquet")
    contrasts = pd.read_parquet(
        output / "metrics/eventwise_temporal_confirmation_contrasts.parquet"
    )
    manifest = json.loads((report_path.parent / "manifest.json").read_text())
    assert len(detail) == 2 * 32 * 4
    assert len(cells) == 32 * 4
    assert detail.groupby(["scenario", "budget_rate", "alpha_allocation"]).size().eq(2).all()
    assert detail.propensity_min.gt(0).all()
    assert int(cells.cap_violations.sum()) == 0
    assert set(contrasts.contrast) == {
        "eventwise_minus_rank",
        "eventwise_minus_nested_volume",
        "eventwise_minus_minimum_bound",
    }
    assert manifest["prerequisite_null_calibration"]["status"] == "passed"
    assert manifest["inference"]["total_rows"] == 256
    assert "smoke_only" in report_path.read_text(encoding="utf-8")


def test_temporal_variance_confirmation_smoke_pairs_query_policies(tmp_path: Path):
    root = Path(__file__).parents[1]
    protocol = (
        root / "docs/scout_context_policy_eventwise_temporal_variance_confirmation_protocol.md"
    )
    calibration = (
        root
        / "outputs/scout_context_policy_eventwise_temporal_variance_null_1000/reports/manifest.json"
    )
    report_path = run_confirmation(
        output=tmp_path / "temporal_variance_confirmation_smoke",
        protocol=protocol,
        calibration_manifest=calibration,
        seeds=2,
        seed_offset=21_440_100,
        n=1000,
        d=4,
        device="cpu",
        workers=2,
        bootstrap_draws=200,
        query_policies=("uniform", "variance"),
    )
    output = report_path.parent.parent
    detail = pd.read_parquet(output / "metrics/eventwise_temporal_confirmation_streams.parquet")
    cells = pd.read_parquet(output / "metrics/eventwise_temporal_confirmation_cells.parquet")
    contrasts = pd.read_parquet(
        output / "metrics/eventwise_temporal_confirmation_contrasts.parquet"
    )
    manifest = json.loads((report_path.parent / "manifest.json").read_text())
    assert len(detail) == 2 * 32 * 4 * 2
    assert len(cells) == 32 * 4 * 2
    assert set(detail.query_policy.unique()) == {"uniform", "variance"}
    assert (
        detail.groupby(["scenario", "budget_rate", "query_policy", "alpha_allocation"])
        .size()
        .eq(2)
        .all()
    )
    assert manifest["configuration"]["shared_query_randomness"] is True
    assert manifest["prerequisite_null_calibration"]["normalized_manifest_sha256"] == (
        "e60dc80185335cd0328cc80a57fdec82ad23d611361db9773201cf64185b97a0"
    )
    assert int(cells.cap_violations.sum()) == 0
    assert set(contrasts.loc[contrasts.primary_comparison, "contrast"]) == {
        "variance_eventwise_minus_rank",
        "variance_eventwise_minus_nested_volume",
    }
    assert len(contrasts) == 7
    assert manifest["inference"]["total_rows"] == 512
    assert "smoke_only" in report_path.read_text(encoding="utf-8")
