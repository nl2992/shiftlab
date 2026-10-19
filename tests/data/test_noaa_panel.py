import json

import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.noaa import FEATURES, acquire, decode_fields, station_rows
from shiftlab.data.validation import validate_dataset


def test_decoded_units_quality_and_precipitation_period():
    source = pd.DataFrame(
        {
            "TMP": ["+0123,1", "+9999,9", "+0100,2"],
            "DEW": ["-0012,5", "+0050,1", "+0100,7"],
            "SLP": ["10132,1", "99999,9", "10000,3"],
            "WND": ["180,1,N,0025,1", "999,9,9,9999,9", "090,1,N,0100,6"],
            "VIS": ["012000,1,N,1", "999999,9,9,9", "001000,2,N,1"],
            "AA1": ["06,0012,9,1", "01,0000,2,1", "99,0030,9,1"],
        }
    )
    X = decode_fields(source)
    np.testing.assert_allclose(X[0], [12.3, -1.2, 1013.2, 2.5, 12000, 1.2, 6])
    assert np.isnan(X[1, [0, 2, 3, 4]]).all()
    assert X[1, 5] == 0 and X[1, 6] == 1  # Trace flag remains in raw metadata.
    assert np.isnan(X[2]).all()
    source.loc[0, "AA1"] = "06,0012,I,1"
    assert np.isnan(decode_fields(source)[0, 5])
    assert np.isnan(decode_fields(source.drop(columns=["AA1"]))[:, 5:]).all()


def test_simultaneous_reports_never_become_future_targets():
    station = "74486094789"
    source = pd.DataFrame(
        {
            "DATE": [
                "2023-01-01T00:00",
                "2023-01-01T00:00",
                "2023-01-01T01:00",
                "2023-01-01T02:00",
                "2023-01-01T03:00",
            ],
            "STATION": station,
            "TMP": ["+0100,1", "+0200,1", "+0300,1", "+0400,1", "+9999,9"],
            "DEW": "+0000,1",
        }
    )
    frame = station_rows(source, station, 2023)
    assert (frame.label_event_time > frame.event_time).all()
    assert frame.target.iloc[:3].tolist() == [30, 30, 40]
    assert np.isnan(frame.target.iloc[3])
    assert json.loads(frame.metadata.iloc[0])["source"]["TMP"] == "+0100,1"
    assert frame.prediction_time.isna().all()
    with pytest.raises(ValueError, match="different station"):
        station_rows(source, "72509014739", 2023)


def test_panel_shared_splits_no_cross_station_targets(tmp_path, monkeypatch):
    stations = ["74486094789", "72509014739"]
    paths = {}
    for i, station in enumerate(stations):
        source = pd.DataFrame(
            {
                "DATE": pd.date_range("2023-01-01", periods=30, freq="h")
                + pd.Timedelta(minutes=30 * i),
                "STATION": station,
                "TMP": f"+0{i + 1}00,1",
                "DEW": "+0000,1",
            }
        )
        paths[station] = tmp_path / f"{station}.csv"
        source.to_csv(paths[station], index=False)
    monkeypatch.setattr(
        "shiftlab.data.real.noaa.download",
        lambda url, *args, **kw: paths[url.rsplit("/", 1)[1].split(".")[0]],
    )
    output = acquire({"year": 2023, "stations": stations}, tmp_path / "out")
    frame = pd.read_parquet(output / "observations.parquet")
    assert set(frame.domain_id) == set(stations)
    assert frame.groupby("domain_id").target.first().to_dict() == {stations[0]: 10, stations[1]: 20}
    assert frame.sample_id.is_unique
    assert frame.event_time.is_monotonic_increasing
    previous_end = -np.inf
    for split in ["train", "validation", "calibration", "test"]:
        part = frame[frame.split == split]
        assert part.event_time.min() > previous_end
        previous_end = part.event_time.max()
    manifest = json.loads((output / "dataset_manifest.json").read_text())
    assert manifest["feature_names"] == FEATURES
    assert validate_dataset(output)["rows"] == 58
