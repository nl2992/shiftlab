from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts import analyze_policy_bound_harm_confirmation as harm_analyzer
from scripts.analyze_policy_bound_harm_confirmation import (
    gpu_name_from_manifest,
    holm_adjust,
    paired_detection_pvalue,
    wilson_interval,
)
from scripts.run_policy_bound_harm_confirmation import (
    CALIBRATION_CONFIG,
    CALIBRATION_METHODS,
    CALIBRATION_PROTOCOL,
    CALIBRATION_SCENARIOS,
    HARM_CONFIRMATION_CONFIG,
    REQUIRED_CALIBRATION_ARTIFACTS,
    ROOT,
    calibration_passes,
    expected_calibration_source_hashes,
    sha256,
)


def write_calibration_summary(path, familywise_uppers):
    rows = [
        {
            "scenario": scenario,
            "method": method,
            "monitor": "fixed_mixture",
            "primary_familywise_95_upper": upper,
        }
        for (scenario, method), upper in zip(
            [
                (scenario, method)
                for scenario in CALIBRATION_SCENARIOS
                for method in CALIBRATION_METHODS
            ],
            familywise_uppers,
            strict=True,
        )
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    report_dir = path.parents[1] / "reports"
    report_dir.mkdir(parents=True)
    (report_dir / "policy_bound_null_calibration.md").write_text(
        "The calibration criterion is **PASS**.", encoding="utf-8"
    )
    metrics_path = path.parents[1] / "metrics/hard_budget_comparison.parquet"
    metrics_path.parent.mkdir(parents=True)
    metrics_path.write_bytes(b"test-only metric artifact")
    artifact_paths = {
        relative: path.parents[1] / relative for relative in REQUIRED_CALIBRATION_ARTIFACTS
    }
    run_path = ROOT / "scripts/run_policy_bound_null_calibration.py"
    analyzer_path = ROOT / "scripts/analyze_policy_bound_null_calibration.py"
    protocol_path = ROOT / CALIBRATION_PROTOCOL
    manifest = {
        "configuration": {
            **CALIBRATION_CONFIG,
            "scenario_subset": list(CALIBRATION_SCENARIOS),
            "method_subset": list(CALIBRATION_METHODS),
        },
        "resolved_device": "cuda",
        "sha256": {
            "artifacts": {
                relative: sha256(artifact) for relative, artifact in artifact_paths.items()
            },
            "source_files": expected_calibration_source_hashes(),
        },
        "run_provenance": {
            "analysis_script_sha256": sha256(analyzer_path),
            "run_script_sha256": sha256(run_path),
            "protocol_sha256": sha256(protocol_path),
            "source_git_commit_at_run": "test-commit",
        },
    }
    (report_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def refresh_artifact_hash(calibration_dir, relative_path):
    manifest_path = calibration_dir / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifact_path = calibration_dir / relative_path
    manifest["sha256"]["artifacts"][relative_path] = sha256(artifact_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def test_calibration_gate_requires_all_ten_primary_cells(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    write_calibration_summary(summary_dir / "policy_bound_null_calibration.csv", [0.04] * 10)
    assert calibration_passes(calibration)


def test_calibration_gate_rejects_failed_or_incomplete_cells(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    write_calibration_summary(
        summary_dir / "policy_bound_null_calibration.csv", [0.04] * 9 + [0.05]
    )
    assert not calibration_passes(calibration)
    assert not calibration_passes(tmp_path / "missing")


def test_calibration_gate_rejects_duplicate_or_missing_primary_cell(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    path = summary_dir / "policy_bound_null_calibration.csv"
    write_calibration_summary(path, [0.04] * 10)
    summary = pd.read_csv(path)
    summary.loc[9, ["scenario", "method"]] = summary.loc[0, ["scenario", "method"]].to_numpy()
    summary.to_csv(path, index=False)
    refresh_artifact_hash(calibration, "analysis/policy_bound_null_calibration.csv")
    assert not calibration_passes(calibration)


def test_calibration_gate_rejects_modified_hashed_artifact(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    write_calibration_summary(summary_dir / "policy_bound_null_calibration.csv", [0.04] * 10)
    report_path = calibration / "reports/policy_bound_null_calibration.md"
    report_path.write_text("The calibration criterion is **PASS**. edited", encoding="utf-8")
    assert not calibration_passes(calibration)


def test_calibration_gate_rejects_nonregistered_configuration(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    write_calibration_summary(summary_dir / "policy_bound_null_calibration.csv", [0.04] * 10)
    manifest_path = calibration / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["configuration"]["budget_rate"] = 0.25
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert not calibration_passes(calibration)


def test_calibration_gate_rejects_changed_source_hash(tmp_path):
    calibration = tmp_path / "calibration"
    summary_dir = calibration / "analysis"
    summary_dir.mkdir(parents=True)
    write_calibration_summary(summary_dir / "policy_bound_null_calibration.csv", [0.04] * 10)
    manifest_path = calibration / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sha256"]["source_files"]["src/shiftlab/dive/hard_budget.py"] = "stale"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert not calibration_passes(calibration)


def test_holm_adjustment_preserves_order_and_is_monotone():
    assert holm_adjust([0.01, 0.04, 0.03, 0.002]) == [0.03, 0.06, 0.06, 0.008]


def test_one_sided_paired_test_uses_only_discordant_seed_pairs():
    assert paired_detection_pvalue(0, 0) == 1.0
    assert paired_detection_pvalue(8, 0) < 0.01
    assert paired_detection_pvalue(0, 8) == 1.0
    with pytest.raises(ValueError, match="nonnegative"):
        paired_detection_pvalue(-1, 1)


def test_wilson_interval_contains_the_observed_rate():
    low, high = wilson_interval(14, 40)
    assert low < 14 / 40 < high


def test_harm_analyzer_uses_the_runner_frozen_config():
    assert harm_analyzer.EXPECTED_CONFIG == json.loads(json.dumps(HARM_CONFIRMATION_CONFIG))


def test_harm_report_reads_gpu_name_from_environment_manifest():
    assert (
        gpu_name_from_manifest({"environment": {"gpu_name": "NVIDIA GeForce RTX 4060 Laptop GPU"}})
        == "NVIDIA GeForce RTX 4060 Laptop GPU"
    )


def test_harm_analyzer_rejects_modified_metric_artifacts(tmp_path, monkeypatch):
    monkeypatch.setattr(harm_analyzer, "ROOT", tmp_path)
    output = tmp_path / "confirmation"
    metrics = output / "metrics/hard_budget_comparison.parquet"
    metrics.parent.mkdir(parents=True)
    metrics.write_bytes(b"registered metrics")
    source = tmp_path / "source.py"
    source.write_text("registered source", encoding="utf-8")
    manifest = {
        "sha256": {
            "artifacts": {"metrics/hard_budget_comparison.parquet": sha256(metrics)},
            "source_files": {"source.py": sha256(source)},
        }
    }
    harm_analyzer.verify_manifest_integrity(output, manifest)
    metrics.write_bytes(b"changed metrics")
    with pytest.raises(ValueError, match="artifact failed its manifest hash"):
        harm_analyzer.verify_manifest_integrity(output, manifest)


def test_harm_analyzer_rejects_non_cuda_or_changed_runtime_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(harm_analyzer, "ROOT", tmp_path)
    monkeypatch.setattr(harm_analyzer, "PROTOCOL", Path("harm_protocol.md"))
    calibration = tmp_path / "calibration"
    monkeypatch.setattr(harm_analyzer, "CALIBRATION", calibration)
    protocol = tmp_path / "harm_protocol.md"
    protocol.write_text("locked protocol", encoding="utf-8")
    run_script = tmp_path / "scripts/run_policy_bound_harm_confirmation.py"
    run_script.parent.mkdir(parents=True)
    run_script.write_text("locked runner", encoding="utf-8")
    calibration_report = calibration / "reports/policy_bound_null_calibration.md"
    calibration_report.parent.mkdir(parents=True)
    calibration_report.write_text("passing calibration", encoding="utf-8")
    manifest = {
        "resolved_device": "cuda",
        "run_provenance": {
            "protocol_sha256": sha256(protocol),
            "run_script_sha256": sha256(run_script),
            "calibration_report_sha256": sha256(calibration_report),
            "source_git_commit_at_run": "test-commit",
        },
    }
    harm_analyzer.verify_run_provenance(tmp_path / "confirmation", manifest)
    manifest["resolved_device"] = "cpu"
    with pytest.raises(ValueError, match="resolve to CUDA"):
        harm_analyzer.verify_run_provenance(tmp_path / "confirmation", manifest)
