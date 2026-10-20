import json

import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.adapters import _licensed_timestamp_seconds, acquire
from shiftlab.data.validation import validate_dataset


def test_opsd_utc_units_and_original_offsets(tmp_path, monkeypatch):
    """Pandas datetime resolution must never silently rescale the epoch."""
    times = pd.date_range("2018-03-24", periods=60, freq="h", tz="UTC")
    csv = tmp_path / "fixture.csv"
    pd.DataFrame(
        {
            "utc_timestamp": times.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "cet_cest_timestamp": times.tz_convert("Europe/Berlin").strftime("%Y-%m-%dT%H:%M:%S%z"),
            "load": np.arange(60.0),
        }
    ).to_csv(csv, index=False)
    meta = tmp_path / "datapackage.json"
    meta.write_text("{}")

    def fetch(url, *args, **kwargs):
        return meta if url.endswith(".json") else csv

    monkeypatch.setattr("shiftlab.data.real.opsd.download", fetch)
    path = acquire(
        "opsd", {"columns": ["load"], "start": "2018-01-01", "end": "2019-01-01"}, tmp_path / "out"
    )
    frame = pd.read_parquet(path / "observations.parquet")
    assert frame.event_time.iloc[0] == times[0].timestamp()
    assert np.all(np.diff(frame.event_time) == 3600)
    originals = [json.loads(v)["cet_cest"] for v in frame.metadata]
    assert any(v.endswith("+0100") for v in originals)
    assert any(v.endswith("+0200") for v in originals)
    assert frame.prediction_time.isna().all()
    assert validate_dataset(path)["rows"] == 59
    task = json.loads((path / "dataset_manifest.json").read_text())["task_specs"][0]
    assert task["task_id"] == "next_period_load_regression"
    assert task["forecast_horizon"]["value"] == 1
    assert task["forecast_horizon"]["unit"] == "hours"


def test_noaa_missingness_flags_and_epoch(tmp_path, monkeypatch):
    times = pd.date_range("2023-01-01", periods=30, freq="h")
    path = tmp_path / "noaa.csv"
    pd.DataFrame(
        {
            "DATE": times.astype(str),
            "TMP": ["+9999,9"] + ["+0100,1"] * 29,
            "DEW": ["+0050,1"] * 30,
            "STATION": ["74486094789"] * 30,
        }
    ).to_csv(path, index=False)
    monkeypatch.setattr("shiftlab.data.real.noaa.download", lambda *a, **kw: path)
    output = acquire("noaa", {"station": "74486094789", "year": 2023}, tmp_path / "out")
    frame = pd.read_parquet(output / "observations.parquet")
    assert frame.event_time.iloc[0] == pd.Timestamp("2023-01-01", tz="UTC").timestamp()
    assert np.isnan(frame.features.iloc[0][0])
    assert json.loads(frame.metadata.iloc[0])["source"]["TMP"] == "+9999,9"
    assert frame.label_available_time.isna().all()
    task = json.loads((output / "dataset_manifest.json").read_text())["task_specs"][0]
    assert task["forecast_horizon"]["value"] == "per row"
    assert "unknown" in task["label_availability_rule"]


def test_local_import_license_and_timestamp_units(tmp_path):
    original = pd.DataFrame(
        {
            "x": np.arange(30.0),
            "y": np.arange(30.0),
            "time": pd.date_range("2023-01-01", periods=30, freq="h").astype(str),
            "contract": ["fixture-contract"] * 30,
        }
    )
    source = tmp_path / "fixture.csv"
    original.to_csv(source, index=False)
    config = {
        "path": str(source),
        "license": "Synthetic fixture, MIT",
        "feature_columns": ["x"],
        "target_column": "y",
        "time_columns": {"event_time": "time"},
        "time_zones": {"event_time": "UTC"},
    }
    destination = acquire("licensed_local", config, tmp_path / "data")
    frame = pd.read_parquet(destination / "observations.parquet")
    assert frame.event_time.iloc[0] == pd.Timestamp("2023-01-01", tz="UTC").timestamp()
    assert json.loads(frame.metadata.iloc[0])["contract"] == "fixture-contract"


def test_licensed_numeric_epoch_requires_and_respects_declared_unit():
    seconds = [pd.Timestamp("2023-01-01", tz="UTC").timestamp()]
    assert (
        _licensed_timestamp_seconds(seconds, "event_time", {"time_units": {"event_time": "s"}})[0]
        == seconds[0]
    )
    with pytest.raises(ValueError, match="explicit time_units"):
        _licensed_timestamp_seconds(seconds, "event_time", {})


def test_licensed_naive_datetime_requires_explicit_timezone():
    with pytest.raises(ValueError, match="explicit time_zones"):
        _licensed_timestamp_seconds(["2023-01-01 09:00"], "event_time", {})
    local = _licensed_timestamp_seconds(
        ["2023-01-01 09:00"], "event_time", {"time_zones": {"event_time": "America/New_York"}}
    )
    assert local[0] == pd.Timestamp("2023-01-01 14:00", tz="UTC").timestamp()


def test_licensed_datetime_columns_preserve_their_timezone_and_epoch():
    aware = pd.Series(pd.date_range("2023-01-01", periods=1, tz="America/Los_Angeles"))
    seconds = _licensed_timestamp_seconds(aware, "event_time", {})
    assert seconds[0] == pd.Timestamp("2023-01-01 08:00", tz="UTC").timestamp()

    naive = pd.Series(pd.date_range("2023-01-01", periods=1))
    seconds = _licensed_timestamp_seconds(
        naive, "event_time", {"time_zones": {"event_time": "UTC"}}
    )
    assert seconds[0] == pd.Timestamp("2023-01-01", tz="UTC").timestamp()
