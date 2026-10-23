from pathlib import Path

import pandas as pd

from shiftlab.decision_harm_experiment import ExperimentConfig, run_experiment


def test_quick_benchmark_writes_reproducible_artifacts(tmp_path: Path):
    config = ExperimentConfig(
        n=800,
        d=4,
        evaluation_seeds=1,
        calibration_seeds=6,
        calibration_start=200,
        window=32,
        stride=32,
        seed_offset=9876,
    )
    output = run_experiment(config, tmp_path / "run")
    for name in [
        "manifest.json",
        "baseline_report.md",
        "metrics.parquet",
        "alarm_metrics.parquet",
        "monitor_trace.parquet",
        "estimands_by_scenario.png",
        "alarms_and_delay.png",
        "cumulative_regret.png",
    ]:
        assert (output / name).is_file()
    metrics = pd.read_parquet(output / "metrics.parquet")
    assert len(metrics) == 6
    assert set(metrics.scenario) == {
        "stationary",
        "benign_nuisance",
        "boundary_local_harm",
        "residual_variance",
        "recurring_regimes",
        "harmful_adaptation",
    }
    assert metrics.cumulative_regret_vs_oracle.notna().all()
    by_scenario = metrics.set_index("scenario")
    assert (
        by_scenario.loc["stationary", "decision_harm_vs_reference"]
        == by_scenario.loc["benign_nuisance", "decision_harm_vs_reference"]
    )
    assert (
        by_scenario.loc["boundary_local_harm", "decision_harm_vs_reference"]
        > by_scenario.loc["stationary", "decision_harm_vs_reference"] + 0.1
    )
    assert (
        by_scenario.loc["harmful_adaptation", "decision_harm_vs_reference"]
        > by_scenario.loc["stationary", "decision_harm_vs_reference"] + 0.1
    )
