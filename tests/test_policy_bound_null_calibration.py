from __future__ import annotations

import subprocess

import pytest

from scripts import analyze_policy_bound_null_calibration as analyzer
from scripts.analyze_policy_bound_null_calibration import (
    EXPECTED_CONFIG,
    MAX_PRIMARY_FALSE_ESCALATIONS,
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


def test_primary_event_cutoff_matches_the_registered_strict_bound() -> None:
    assert MAX_PRIMARY_FALSE_ESCALATIONS == 12
    assert clopper_pearson_upper(12, 500, confidence=0.995) < 0.05
    assert clopper_pearson_upper(13, 500, confidence=0.995) >= 0.05


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


def test_analysis_rejects_non_cuda_or_mismatched_run_provenance(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(analyzer, "ROOT", tmp_path)
    protocol = tmp_path / analyzer.PROTOCOL
    protocol.parent.mkdir(parents=True)
    protocol.write_text("locked protocol", encoding="utf-8")
    run_script = tmp_path / "scripts/run_policy_bound_null_calibration.py"
    run_script.parent.mkdir(parents=True)
    run_script.write_text("locked runner", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "add", "scripts/run_policy_bound_null_calibration.py"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "commit", "-qm", "record runner"], cwd=tmp_path, check=True)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    manifest = {
        "resolved_device": "cuda",
        "run_provenance": {
            "protocol_sha256": sha256(protocol),
            "run_script_sha256": sha256(run_script),
            "source_git_commit_at_run": commit,
        },
    }
    analyzer.verify_run_provenance(manifest)

    run_script.write_text("later runner revision", encoding="utf-8")
    analyzer.verify_run_provenance(manifest)

    manifest["resolved_device"] = "cpu"
    with pytest.raises(ValueError, match="resolve to CUDA"):
        analyzer.verify_run_provenance(manifest)
