import json

import numpy as np
import pandas as pd

from shiftlab.data.real.adapters import acquire
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
    }
    destination = acquire("licensed_local", config, tmp_path / "data")
    frame = pd.read_parquet(destination / "observations.parquet")
    assert frame.event_time.iloc[0] == pd.Timestamp("2023-01-01", tz="UTC").timestamp()
    assert json.loads(frame.metadata.iloc[0])["contract"] == "fixture-contract"
