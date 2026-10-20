import json
from pathlib import Path

import pandas as pd

from shiftlab.data import report as report_module
from shiftlab.data.catalogue import SOURCES
from shiftlab.data.provenance import commit, sha256, source_hash
from shiftlab.data.report import _dataset_suitability_rows, _readiness_labels, build_report


def test_registered_real_forecast_task_is_not_reported_as_missing_a_task():
    paper1, paper2, paper3 = _readiness_labels(
        "eia",
        False,
        False,
        [{"task_kind": "regression", "label_availability_rule": "unknown"}],
    )
    assert paper1 == "retrospective; utility imposed"
    assert paper2 == "retrospective forecast/conformal task; availability unknown"
    assert paper3 == "retrospective task; release-time protocol unknown"


def test_coarse_classification_domains_are_not_misrepresented_as_online_streams():
    _, paper2, paper3 = _readiness_labels("gas_sensor", False, True, [])
    assert paper2 == "classification prediction-set protocol required"
    assert paper3 == "offline domain benchmark; release times unavailable"


def test_criteo_readiness_exposes_its_delayed_feedback_assumptions():
    paper1, paper2, paper3 = _readiness_labels(
        "criteo", False, True, [{"task_kind": "binary_classification"}]
    )
    assert paper1 == "retrospective; utility imposed"
    assert "delay-unit assumptions required" in paper2
    assert "publisher release times unverified" in paper3


def test_synthetic_streams_remain_available_for_all_three_research_tracks():
    assert _readiness_labels("concept", True, False, []) == (
        "controlled decision study",
        "regression/classification stream",
        "stream ready",
    )


def test_legacy_monash_manifest_uses_registered_horizon_without_claiming_online_availability():
    _, paper2, paper3 = _readiness_labels("monash", False, False, [], {"dataset": "m4_weekly"})
    assert paper2 == "retrospective forecast/conformal task; availability unknown"
    assert paper3 == "retrospective task; release-time protocol unknown"


def test_dataset_paper_matrix_covers_sources_and_preserves_known_limitations():
    rows = _dataset_suitability_rows(
        [
            {
                "dataset": "gas_sensor",
                "version": "fixture-version",
                "acquired_at": "2026-10-20T00:00:00+00:00",
                "n_observations": 100,
                "ground_truth": "source_observed",
                "task_specs": [],
                "processing_config": {},
            },
            {
                "dataset": "concept",
                "version": "synthetic-fixture",
                "acquired_at": "2026-10-20T00:00:00+00:00",
                "n_observations": 200,
                "ground_truth": "synthetic_known",
            },
        ]
    )
    by_name = {row["dataset"]: row for row in rows}
    assert set(by_name) == {*SOURCES, "synthetic_suite"}
    gas = by_name["gas_sensor"]
    assert gas["acquired_versions"] == 1
    assert gas["latest_version"] == "fixture-version"
    assert gas["paper2_readiness"] == "classification prediction-set protocol required"
    assert gas["paper3_readiness"] == "offline domain benchmark; release times unavailable"
    assert "no within-batch timestamps" in gas["timing_evidence"]
    assert "Research-only pending clarification" in gas["source_limitations"]
    assert by_name["fred"]["acquisition_status"] == "implemented_requires_api_key"
    assert "delay-unit assumptions required" in by_name["criteo"]["paper2_readiness"]
    assert "publisher release times unverified" in by_name["criteo"]["paper3_readiness"]
    assert by_name["synthetic_suite"]["acquired_versions"] == 1
    assert by_name["synthetic_suite"]["latest_rows"] == 200


def test_report_pipeline_emits_suitability_csv_markdown_and_provenance(tmp_path):
    report = build_report(tmp_path)
    matrix = pd.read_csv(report / "dataset_paper_suitability.csv")
    manifest = json.loads((report / "dataset_paper_suitability.manifest.json").read_text())
    assert len(matrix) == len(SOURCES) + 1
    assert manifest["source_count"] == len(SOURCES)
    assert manifest["synthetic_acquired_versions"] == 0
    assert manifest["processing_commit"] == commit()
    assert manifest["source_hash"] == source_hash()
    assert manifest["report_script_sha256"] == sha256(Path(report_module.__file__))
    assert (
        "Unknown release timing remains unknown"
        in (report / "dataset_paper_suitability.md").read_text()
    )
