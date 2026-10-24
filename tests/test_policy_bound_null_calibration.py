from __future__ import annotations

import pytest

from scripts import analyze_policy_bound_null_calibration as analyzer
from scripts.analyze_policy_bound_null_calibration import (
    EXPECTED_CONFIG,
    clopper_pearson_upper,
    sha256,
    validate_seed_block,
    wilson_interval,
)
from scripts.run_policy_bound_harm_confirmation import (
    CALIBRATION_CONFIG,
    CALIBRATION_METHODS,
    CALIBRATION_SCENARIOS,
)


def test_zero_event_simultaneous_upper_bound_is_below_calibration_target() -> None:
    upper = clopper_pearson_upper(0, 500, confidence=1 - 0.05 / 10)
    assert 0 < upper < 0.05


def test_pointwise_zero_event_upper_matches_closed_form() -> None:
    upper = clopper_pearson_upper(0, 500)
    assert upper == pytest.approx(1 - 0.05 ** (1 / 500))


def test_wilson_interval_covers_observed_rate_and_rejects_invalid_counts() -> None:
    low, high = wilson_interval(3, 500)
    assert low < 3 / 500 < high
    with pytest.raises(ValueError):
        wilson_interval(501, 500)


def test_calibration_requires_the_exact_registered_seed_block() -> None:
    import pandas as pd

    expected = pd.Series(range(54_000_000, 54_000_500))
    validate_seed_block(expected, method="uniform_proxy", scenario="stationary")

    shifted = expected.copy()
    shifted.iloc[-1] += 1
    with pytest.raises(ValueError, match="exact registered seed block"):
        validate_seed_block(shifted, method="uniform_proxy", scenario="stationary")


def test_analyzer_config_matches_the_confirmation_gate_config() -> None:
    expected = {
        **CALIBRATION_CONFIG,
        "scenario_subset": list(CALIBRATION_SCENARIOS),
        "method_subset": list(CALIBRATION_METHODS),
    }
    assert EXPECTED_CONFIG == expected


def test_analysis_rejects_a_changed_artifact_before_rehashing_it(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(analyzer, "ROOT", tmp_path)
    output = tmp_path / "run"
    metrics = output / "metrics/hard_budget_comparison.parquet"
    metrics.parent.mkdir(parents=True)
    metrics.write_bytes(b"registered metric bytes")
    source = tmp_path / "source.py"
    source.write_text("registered source", encoding="utf-8")
    manifest = {
        "sha256": {
            "artifacts": {"metrics/hard_budget_comparison.parquet": sha256(metrics)},
            "source_files": {"source.py": sha256(source)},
        }
    }
    analyzer.verify_manifest_integrity(output, manifest)

    metrics.write_bytes(b"altered metric bytes")
    with pytest.raises(ValueError, match="artifact failed its manifest hash"):
        analyzer.verify_manifest_integrity(output, manifest)
