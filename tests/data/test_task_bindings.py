import json

import numpy as np
import pytest

from shiftlab.data.real.adapters import standardize
from shiftlab.data.schemas import DatasetTaskSpec, Manifest
from shiftlab.data.storage import save_dataset
from shiftlab.data.tasks import dataset_task_specs


@pytest.mark.parametrize(
    "dataset,config",
    [
        ("opsd", {"frequency": "hourly", "target_column": "load"}),
        ("noaa", {"year": 2023}),
        ("monash", {"dataset": "m4_weekly"}),
        ("eia", {"horizon": 3, "target": "D"}),
        ("binance", {"interval": "1h"}),
        ("criteo", {"outcome_window_days": 30, "delay_unit": "hours"}),
        ("gas_sensor", {}),
        ("folktables", {"tasks": ["ACSIncome"]}),
        ("wilds", {"dataset": "civilcomments"}),
        ("fred", {"series": ["CPIAUCSL"]}),
        ("licensed_local", {"target_column": "outcome"}),
        ("synthetic", {"scenario": "target_variance"}),
    ],
)
def test_dataset_task_bindings_have_complete_common_contract(dataset, config):
    binding = dataset_task_specs(dataset, config)[0]
    DatasetTaskSpec.model_validate(binding)
    assert binding["task_id"]
    assert binding["task_kind"]
    assert binding["target_definition"]
    assert "valid_target_mask" in binding
    assert isinstance(binding["evaluation_metrics"], list)
    assert "label_availability_rule" in binding
    assert binding["utility_provenance"]


def test_source_bindings_state_horizon_masks_and_utility_without_inventing_availability():
    hourly = dataset_task_specs("opsd", {"frequency": "hourly", "target_column": "load"})[0]
    daily = dataset_task_specs("opsd", {"frequency": "daily", "target_column": "load"})[0]
    assert hourly["forecast_horizon"] == {
        "value": 1,
        "unit": "hours",
        "event_semantics": "target event is the end of the next hourly observation or complete UTC day",
    }
    assert daily["forecast_horizon"]["unit"] == "days"
    assert "unknown" in hourly["label_availability_rule"]

    noaa = dataset_task_specs("noaa", {})[0]
    assert noaa["forecast_horizon"]["value"] == "per row"
    assert "not a fixed hourly horizon" in noaa["forecast_horizon"]["event_semantics"]

    assert (
        dataset_task_specs("monash", {"dataset": "m4_weekly"})[0]["forecast_horizon"]["value"] == 13
    )
    assert (
        dataset_task_specs("monash", {"dataset": "m4_daily"})[0]["forecast_horizon"]["value"] == 14
    )
    electricity = dataset_task_specs(
        "monash",
        {
            "dataset": "electricity_hourly",
            "forecast_horizon": 168,
            "forecast_horizon_source": "paper",
        },
    )[0]
    weather = dataset_task_specs(
        "monash", {"dataset": "weather", "forecast_horizon": 30, "forecast_horizon_source": "paper"}
    )[0]
    assert electricity["forecast_horizon"]["value"] == 168
    assert weather["forecast_horizon"]["value"] == 30
    assert "source: paper" in weather["forecast_horizon"]["event_semantics"]

    criteo = dataset_task_specs("criteo", {"outcome_window_days": 30})[0]
    assert "label_available_time is finite" in criteo["valid_target_mask"]
    assert "incomplete negative follow-up" in criteo["valid_target_mask"]
    assert "No application-grounded" in criteo["utility_provenance"]

    fred = dataset_task_specs("fred", {})[0]
    assert fred["task_kind"] == "source_table_not_forecast_task"
    assert fred["evaluation_metrics"] == []


def test_task_binding_is_written_into_dataset_manifest(tmp_path):
    frame = standardize(
        np.arange(12, dtype=float).reshape(6, 2),
        np.arange(6, dtype=float),
        "DE",
        "fixture",
        split=np.full(6, "unassigned"),
    )
    provenance = {
        "publisher": "fixture",
        "source_url": "local://fixture",
        "citation": "fixture",
        "license": "CC0",
        "permitted_use": "test",
        "feature_names": ["load", "wind"],
    }
    path = save_dataset(
        [(frame, None)],
        "opsd",
        tmp_path,
        provenance,
        {"frequency": "hourly", "target_column": "load"},
    )
    manifest = json.loads((path / "dataset_manifest.json").read_text())
    assert manifest["task_specs"][0]["task_id"] == "next_period_load_regression"
    assert manifest["task_specs"][0]["forecast_horizon"]["value"] == 1


def test_invalid_opsd_frequency_cannot_receive_a_task_binding():
    with pytest.raises(ValueError, match="frequency must be hourly or daily"):
        dataset_task_specs("opsd", {"frequency": "weekly"})


@pytest.mark.parametrize("window", [0, -1, True, "30", np.nan, np.inf])
def test_criteo_task_binding_rejects_invalid_followup_window(window):
    with pytest.raises(ValueError, match="Criteo outcome_window_days"):
        dataset_task_specs("criteo", {"outcome_window_days": window})


@pytest.mark.parametrize("horizon", [0, -1, True, 1.5, np.inf, "2"])
def test_eia_task_binding_rejects_noninteger_horizons(horizon):
    with pytest.raises(ValueError, match="positive integer"):
        dataset_task_specs("eia", {"horizon": horizon})


def test_historical_manifest_without_task_specs_remains_loadable():
    manifest = Manifest(
        dataset="fixture",
        version="old",
        publisher="fixture",
        source_url="local://fixture",
        citation="fixture",
        license="CC0",
        permitted_use="test",
        acquired_at="2026-01-01T00:00:00Z",
        source_hash="abc",
        n_observations=0,
        feature_names=[],
        time_coverage=[],
        domains=[],
        missingness={},
        limitations=[],
        ground_truth="none",
        files={},
    )
    assert manifest.task_specs == []
