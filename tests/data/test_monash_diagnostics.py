import json

import numpy as np
import pandas as pd
import pytest

from scripts.monash_forecast_diagnostics import (
    diagnose_entity,
    plot_forecast_steps,
    summarize_forecast_steps,
)


def _fixed_origin_fixture():
    values = np.arange(40, dtype=float)
    rows = []
    for index in range(8, 30):
        rows.append(
            {
                "entity_id": "series-a",
                "split": "train",
                "target": values[index],
                "features": values[index - 8 : index],
                "sequence_index": index,
                "metadata": json.dumps({"origin_index": 30, "official_horizon": 3}),
            }
        )
    for step in range(1, 4):
        rows.append(
            {
                "entity_id": "series-a",
                "split": "test",
                "target": values[30 + step - 1],
                "features": values[22:30],
                "sequence_index": 30 + step - 1,
                "metadata": json.dumps(
                    {"origin_index": 30, "official_horizon": 3, "forecast_step": step}
                ),
            }
        )
    return pd.DataFrame(rows)


def test_official_multistep_holdout_is_scored_by_step_against_train_only_baselines():
    result = diagnose_entity(_fixed_origin_fixture())
    assert result["origin_index"] == 30
    assert result["official_horizon"] == 3
    assert [row["forecast_step"] for row in result["by_step"]] == [1, 2, 3]
    assert set(result["metrics"]) == {"ridge", "last_value", "training_mean"}
    assert result["metrics"]["last_value"]["mae"] == pytest.approx(2.0)


def test_multistep_diagnostic_rejects_training_targets_at_or_after_origin():
    frame = _fixed_origin_fixture()
    frame.loc[frame.split == "train", "sequence_index"] = 31
    with pytest.raises(ValueError, match="must not exceed"):
        diagnose_entity(frame)


def test_multistep_diagnostic_rejects_future_features_varying_by_holdout_step():
    frame = _fixed_origin_fixture()
    frame.at[frame.index[-1], "features"] = np.arange(8, dtype=float)
    with pytest.raises(ValueError, match="identical across forecast steps"):
        diagnose_entity(frame)


def test_multistep_diagnostic_preserves_missing_official_horizon_target():
    frame = _fixed_origin_fixture()
    frame.loc[frame.index[-2], "target"] = np.nan
    result = diagnose_entity(frame)
    assert result["official_horizon"] == 3
    assert [row["forecast_step"] for row in result["by_step"]] == [1, 3]
    assert result["n_test"] == 2


def test_step_summary_and_plot_use_per_series_errors_and_descriptive_iqr(tmp_path):
    datasets = [
        {
            "dataset": "fixture",
            "entities": 2,
            "series_metrics": [
                {
                    "by_step": [
                        {
                            "forecast_step": 1,
                            "absolute_errors": {"ridge": 1, "last_value": 2, "training_mean": 3},
                        },
                        {
                            "forecast_step": 2,
                            "absolute_errors": {"ridge": 2, "last_value": 3, "training_mean": 4},
                        },
                    ]
                },
                {
                    "by_step": [
                        {
                            "forecast_step": 1,
                            "absolute_errors": {"ridge": 3, "last_value": 4, "training_mean": 5},
                        }
                    ]
                },
            ],
        }
    ]
    summary = summarize_forecast_steps(datasets)
    assert summary[0]["series_count"] == 2
    assert summary[0]["models"]["ridge"]["mean_absolute_error"] == pytest.approx(2)
    assert summary[0]["models"]["ridge"]["median_absolute_error"] == pytest.approx(2)
    assert summary[1]["series_count"] == 1
    output = tmp_path / "monash.png"
    plot_forecast_steps(datasets, summary, output)
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
