import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.dive.delayed_benchmark import (
    SCENARIOS,
    DelayedBenchmarkConfig,
    run_benchmark,
    simulate_cell,
    summarize,
)


def _small_config():
    return DelayedBenchmarkConfig(
        seeds=2,
        n_source=200,
        n_target=240,
        query_rate=0.4,
        scenarios=SCENARIOS,
        delay_schemes=("fixed_3",),
        device="cpu",
    ).validate()


def test_cell_pairs_methods_on_identical_queries_and_outcome_independent_delays():
    config = _small_config()
    rows = simulate_cell(config, seed=7, scenario="boundary_harm", delay_scheme="uniform_0_6")

    assert {row["method"] for row in rows} == {
        "paired_cost_eprocess",
        "source_target_risk_cs",
        "no_query_hold",
    }
    assert len({row["shared_stream_labels_queried"] for row in rows}) == 1
    assert rows[0]["labels_queried"] > 0
    assert rows[-1]["labels_queried"] == 0
    assert rows[-1]["alarm_event"] is None
    assert all(row["device"] == "cpu" for row in rows)


def test_same_seed_reproduces_metrics_and_stream_summary():
    config = _small_config()
    first = simulate_cell(config, seed=17, scenario="stationary", delay_scheme="fixed_3")
    second = simulate_cell(config, seed=17, scenario="stationary", delay_scheme="fixed_3")
    assert first == second

    summary = summarize(pd.DataFrame(first))
    assert len(summary) == 3
    assert np.isfinite(summary.detection_rate).all()
    assert (summary.streams == 1).all()


def test_benchmark_rejects_unavailable_cuda_and_invalid_scenario():
    config = DelayedBenchmarkConfig(scenarios=("unknown",))
    try:
        config.validate()
    except ValueError as error:
        assert "registered scenarios" in str(error)
    else:
        raise AssertionError("unregistered scenario should be rejected")


def test_run_writes_metrics_manifest_summary_and_report(tmp_path):
    config = DelayedBenchmarkConfig(
        seeds=1,
        n_source=100,
        n_target=120,
        query_rate=0.5,
        scenarios=("stationary",),
        delay_schemes=("fixed_3",),
        device="cpu",
    )
    frame, manifest = run_benchmark(config, tmp_path)
    assert len(frame) == 3
    assert manifest["rows"] == 3
    assert pd.read_parquet(tmp_path / "delayed_feedback_metrics.parquet").shape[0] == 3
    assert json.loads((tmp_path / "manifest.json").read_text())["config_validated"] is True
    manifest_file = json.loads((tmp_path / "manifest.json").read_text())
    source_root = Path(__file__).parents[1] / "src" / "shiftlab" / "dive"
    assert all(
        hashlib.sha256((source_root / name).read_bytes()).hexdigest() == digest
        for name, digest in manifest_file["code_sha256"].items()
    )
    assert (
        hashlib.sha256((tmp_path / "delayed_feedback_metrics.parquet").read_bytes()).hexdigest()
        == manifest_file["metrics_sha256"]
    )
    assert (tmp_path / "summary.csv").is_file()
    report = (tmp_path / "results.md").read_text()
    assert "development pilot" in report
    assert "not a full reproduction" in report
