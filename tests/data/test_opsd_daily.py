import json

import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.opsd import acquire, prepare
from shiftlab.data.validation import validate_dataset


def source_frame():
    dates = pd.date_range("2019-03-29", periods=24 * 10, freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "utc_timestamp": dates.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "cet_cest_timestamp": dates.tz_convert("Europe/Berlin").strftime("%Y-%m-%dT%H:%M:%S%z"),
            "load": np.arange(len(dates), dtype=float),
            "price": np.full(len(dates), -3.0),
        }
    )


def test_complete_utc_day_means_keep_missingness_and_dst():
    original = source_frame()
    original.loc[24 + 3, "price"] = np.nan
    frame = prepare(original, ["load", "price"], "load", "daily", "joint", {})
    assert len(frame) == 9
    assert frame.features.iloc[0][0] == 11.5
    assert frame.target.iloc[0] == 35.5
    assert np.isnan(frame.features.iloc[1][1])
    assert frame.features.iloc[2][1] == -3  # Negative market prices are valid.
    assert (frame.label_event_time - frame.event_time == 2 * 86400).all()
    metadata = [json.loads(v) for v in frame.metadata]
    assert all(len(row["source_utc_timestamps"]) == 24 for row in metadata)
    offsets = {v[-5:] for row in metadata for v in row["source_cet_cest_timestamps"]}
    assert offsets == {"+0100", "+0200"}
    assert frame.prediction_time.isna().all()
    partial = prepare(original.iloc[6:], ["load", "price"], "load", "daily", "joint", {})
    assert partial.event_time.iloc[0] == pd.Timestamp("2019-03-30", tz="UTC").timestamp()


def test_daily_next_period_target_mask_excludes_incomplete_target_day():
    original = source_frame()
    original.loc[24 + 3, "load"] = np.nan
    frame = prepare(original, ["load"], "load", "daily", "domain", {})
    assert frame.label_event_time.iloc[0] - frame.event_time.iloc[0] == 2 * 86400
    assert np.isnan(frame.target.iloc[0])
    assert np.isfinite(frame.target.iloc[1])


def test_calendar_gaps_and_local_utc_disagreement_rejected():
    source = source_frame()
    with pytest.raises(ValueError, match="gaps"):
        prepare(source.drop(index=10), ["load"], "load", "daily", "domain", {})
    source.loc[0, "cet_cest_timestamp"] = "2019-03-29T03:00:00+0100"
    with pytest.raises(ValueError, match="disagree"):
        prepare(source, ["load"], "load", "hourly", "domain", {})


def test_daily_adapter_provenance_and_outcome_purging(tmp_path, monkeypatch):
    source = source_frame()
    csv = tmp_path / "hourly.csv"
    source.to_csv(csv, index=False)
    schema = tmp_path / "datapackage.json"
    schema.write_text(
        json.dumps(
            {
                "resources": [
                    {
                        "path": "time_series_60min_singleindex.csv",
                        "schema": {"fields": [{"name": "load", "unit": "MW"}]},
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(
        "shiftlab.data.real.opsd.download",
        lambda url, *a, **kw: schema if url.endswith("json") else csv,
    )
    path = acquire(
        {
            "columns": ["load", "price"],
            "frequency": "daily",
            "start": "2019-01-01",
            "end": "2020-01-01",
            "domain": "joint",
        },
        tmp_path / "out",
    )
    frame = pd.read_parquet(path / "observations.parquet")
    assert (path / "source_datapackage.json").read_bytes() == schema.read_bytes()
    first_test = frame.loc[frame.split == "test", "event_time"].min()
    calibration = frame.loc[frame.split == "calibration"]
    assert (calibration.label_event_time < first_test).all()
    assert (frame.split == "unassigned").any()
    assert validate_dataset(path)["rows"] == 9
