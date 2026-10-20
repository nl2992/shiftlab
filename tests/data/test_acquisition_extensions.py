"""Offline source-format fixtures; fixture success is not a live acquisition claim."""

import io
import json
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.adapters import acquire
from shiftlab.data.real.api import snapshot_pages
from shiftlab.data.real.criteo import COLUMNS, conversion_rows
from shiftlab.data.real.fred import asof_vintage
from shiftlab.data.real.monash import read_tsf, tsf_chunks
from shiftlab.data.real.wilds import IDENTITIES, civilcomments_export, from_official, load_input
from shiftlab.data.schemas import validate_frame
from shiftlab.data.streaming import Label, Request, replay
from shiftlab.data.validation import validate_dataset


class Response:
    ok = True
    status_code = 200

    def __init__(self, payload):
        self.payload = payload
        self.content = json.dumps(payload).encode()

    def json(self):
        return self.payload


def test_api_pagination_receipts_and_redaction(tmp_path, monkeypatch):
    offsets = []

    def get(endpoint, params, **kwargs):
        offsets.append(params["offset"])
        values = list(range(5))[params["offset"] : params["offset"] + params["limit"]]
        return Response(
            {"count": 5, "observations": values, "request": {"api_key": "fixture-secret"}}
        )

    monkeypatch.setattr("shiftlab.data.real.api.requests.get", get)
    pages, receipt = snapshot_pages(
        "https://api.stlouisfed.org/fred/series/observations",
        {"series_id": "FIXTURE"},
        "fixture-secret",
        tmp_path,
        ("observations",),
        ("count",),
        page_size=2,
    )
    assert offsets == [0, 2, 4]
    assert all("fixture-secret" not in p.read_text() for p in [*pages, receipt])
    assert json.loads(receipt.read_text())["rows"] == 5
    assert snapshot_pages(
        "https://api.stlouisfed.org/fred/series/observations",
        {"series_id": "FIXTURE"},
        "fixture-secret",
        tmp_path,
        ("observations",),
        ("count",),
        page_size=2,
    ) == (pages, receipt)
    assert offsets == [0, 2, 4]


def test_credential_errors_do_not_expose_secrets(tmp_path, monkeypatch):
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="EIA_API_KEY"):
        acquire("eia", {}, tmp_path)
    with pytest.raises(ValueError, match="environment"):
        acquire("fred", {"api_key": "do-not-save"}, tmp_path)


def test_eia_format_and_unknown_release_times(tmp_path, monkeypatch):
    monkeypatch.setenv("EIA_API_KEY", "fixture-key")
    rows = [
        {
            "period": f"2023-01-01T{hour:02d}",
            "respondent": "NYIS",
            "type": kind,
            "value": "invalid" if hour == 2 and kind == "D" else str(10 + hour),
            "value-units": "megawatthours",
        }
        for hour in range(4)
        for kind in ["D", "DF"]
    ]
    monkeypatch.setattr(
        "shiftlab.data.real.api.requests.get",
        lambda *a, **kw: Response(
            {
                "response": {"total": str(len(rows)), "data": rows},
                "request": {"params": {"api_key": "fixture-key"}},
            }
        ),
    )
    path = acquire("eia", {"types": ["D", "DF"]}, tmp_path)
    frame = pd.read_parquet(path / "observations.parquet")
    assert len(frame) == 3
    assert frame.event_time.iloc[0] == pd.Timestamp("2023-01-01", tz="UTC").timestamp()
    assert (frame.label_event_time - frame.event_time == 3600).all()
    assert np.isfinite(frame.target.iloc[0])
    assert np.isnan(frame.target.iloc[1])
    assert np.isfinite(frame.target.iloc[2])
    assert frame.prediction_time.isna().all() and frame.label_available_time.isna().all()
    assert validate_dataset(path)["rows"] == 3
    binding = json.loads((path / "dataset_manifest.json").read_text())["task_specs"][0]
    assert binding["forecast_horizon"]["value"] == 1
    assert binding["forecast_horizon"]["unit"] == "hours"
    assert all("fixture-key" not in p.read_text() for p in tmp_path.rglob("*.json"))


def test_fred_asof_revisions_and_date_resolution(tmp_path, monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "fixture-key")
    records = [
        {
            "date": "2023-01-01",
            "value": "3.4",
            "realtime_start": "2023-02-03",
            "realtime_end": "2023-03-09",
        },
        {
            "date": "2023-01-01",
            "value": "3.5",
            "realtime_start": "2023-03-10",
            "realtime_end": "9999-12-31",
        },
    ]
    monkeypatch.setattr(
        "shiftlab.data.real.api.requests.get",
        lambda *a, **kw: Response({"count": 2, "observations": records}),
    )
    path = acquire("fred", {"series": ["UNRATE"]}, tmp_path)
    frame = pd.read_parquet(path / "observations.parquet")
    assert frame.label_available_time.iloc[0] == pd.Timestamp("2023-02-04", tz="UTC").timestamp()
    assert asof_vintage(pd.DataFrame(records), "2023-02-20").value.tolist() == ["3.4"]
    assert asof_vintage(pd.DataFrame(records), "2023-03-20").value.tolist() == ["3.5"]
    assert asof_vintage(pd.DataFrame(records), "2023-01-20").empty
    assert validate_dataset(path)["feature_missing_rate"] is None
    binding = json.loads((path / "dataset_manifest.json").read_text())["task_specs"][0]
    assert binding["task_kind"] == "source_table_not_forecast_task"
    assert binding["evaluation_metrics"] == []


TSF = """@attribute series_name string
@attribute start_timestamp date
@frequency hourly
@horizon 3
@missing true
@equallength false
@data
H1:2020-01-01 00-00-00:1,2,?,4,5,6,7,8,9,10
"""


def test_monash_tsf_official_horizon_and_fixed_origin(tmp_path):
    records = list(read_tsf(io.StringIO(TSF)))
    assert np.isnan(records[0][1][2])
    frame, _ = next(tsf_chunks(io.StringIO(TSF), {"lookback": 2, "max_series": 1}))
    test = frame[frame.split == "test"]
    assert test.target.tolist() == [8.0, 9.0, 10.0]
    assert all(np.array_equal(x, [6.0, 7.0]) for x in test.features)
    assert frame.event_time.isna().all()
    assert validate_frame(frame)["rows"] == 8
    fixture = tmp_path / "fixture.tsf"
    fixture.write_text(TSF)
    result = acquire(
        "monash",
        {"path": str(fixture), "license": "MIT synthetic fixture", "lookback": 2},
        tmp_path / "out",
    )
    assert validate_dataset(result)["rows"] == 8
    manifest = json.loads((result / "dataset_manifest.json").read_text())
    binding = manifest["task_specs"][0]
    assert binding["forecast_horizon"]["value"] == "per-series @horizon"
    stored = pd.read_parquet(result / "observations.parquet")
    holdout = stored[stored.split == "test"]
    assert [json.loads(value)["forecast_step"] for value in holdout.metadata] == [1, 2, 3]
    assert all(json.loads(value)["official_horizon"] == 3 for value in holdout.metadata)


def test_monash_holdout_keeps_incomplete_target_mask_and_declared_horizon():
    incomplete = TSF.replace("7,8,9,10", "7,8,9,?")
    frame, _ = next(tsf_chunks(io.StringIO(incomplete), {"lookback": 2, "max_series": 1}))
    holdout = frame[frame.split == "test"]
    assert len(holdout) == 3
    assert np.isfinite(holdout.target.to_numpy(dtype=float)).tolist() == [True, True, False]
    assert [json.loads(value)["forecast_step"] for value in holdout.metadata] == [1, 2, 3]
    assert all(json.loads(value)["official_horizon"] == 3 for value in holdout.metadata)


def test_criteo_feedback_and_censoring():
    original = pd.DataFrame({name: [1, 1, 1] for name in COLUMNS})
    original["sale"] = [1, 0, 1]
    original["time_delay_for_conversion"] = [100, -1, 200]
    original["click_timestamp"] = [1000, 2000, 3000]
    config = {"delay_unit": "seconds", "assume_instant_click_features": True}
    frame = conversion_rows(original, config)
    assert frame.label_available_time.iloc[0] == 1100
    assert np.isnan(frame.label_available_time.iloc[1])
    assert frame.label_available_time.iloc[2] == 3200
    observed = conversion_rows(original, {**config, "observation_end": 3_000_000})
    assert observed.label_available_time.iloc[1] == 2000 + 30 * 86400
    assert validate_frame(observed)["rows"] == 3
    right_censored = conversion_rows(original, {**config, "observation_end": 1_500})
    assert np.isfinite(right_censored.target.iloc[2])
    assert np.isnan(right_censored.label_available_time.iloc[2])
    with pytest.raises(ValueError, match="never"):
        conversion_rows(original, {**config, "feature_columns": ["sale"]})
    with pytest.raises(ValueError, match="delay_unit"):
        conversion_rows(original, {})


@pytest.mark.parametrize("window", [0, -1, np.nan, np.inf])
def test_criteo_rejects_nonpositive_or_nonfinite_followup_windows(window):
    original = pd.DataFrame({name: [1] for name in COLUMNS})
    original["sale"] = [0]
    original["time_delay_for_conversion"] = [-1]
    original["click_timestamp"] = [1000]
    with pytest.raises(ValueError, match="outcome_window_days|Outcome window"):
        conversion_rows(original, {"delay_unit": "seconds", "outcome_window_days": window})


@pytest.mark.parametrize("latency", [-1, np.nan, np.inf])
def test_criteo_rejects_negative_or_nonfinite_feedback_latency(latency):
    original = pd.DataFrame({name: [1] for name in COLUMNS})
    original["sale"] = [1]
    original["time_delay_for_conversion"] = [1]
    original["click_timestamp"] = [1000]
    with pytest.raises(ValueError, match="feedback_latency_seconds"):
        conversion_rows(
            original,
            {"delay_unit": "seconds", "feedback_latency_seconds": latency},
        )


@pytest.mark.parametrize("delay", [np.nan, np.inf, -1])
def test_criteo_positive_conversion_requires_finite_nonnegative_delay(delay):
    original = pd.DataFrame({name: [1] for name in COLUMNS})
    original["sale"] = [1]
    original["time_delay_for_conversion"] = [delay]
    original["click_timestamp"] = [1000]
    with pytest.raises(ValueError, match="delay"):
        conversion_rows(original, {"delay_unit": "seconds"})


def test_criteo_replay_hides_future_labels_and_orders_equal_time_feedback():
    original = pd.DataFrame({name: [1, 1] for name in COLUMNS})
    original["sale"] = [1, 0]
    original["time_delay_for_conversion"] = [100, -1]
    original["click_timestamp"] = [1000, 1100]
    config = {"delay_unit": "seconds", "assume_instant_click_features": True}
    frame = conversion_rows(original, config)
    events = list(replay(frame))
    assert [type(event) for event in events] == [Request, Request, Label]
    requests = [event for event in events if isinstance(event, Request)]
    label = next(event for event in events if isinstance(event, Label))
    assert requests[0].prediction_time == 1000
    assert requests[1].prediction_time == label.available_time == 1100
    assert label.sample_id == requests[0].sample_id
    assert all(not hasattr(request, "target") for request in requests)

    altered = frame.copy()
    altered.loc[1, "target"] = 1.0
    altered.loc[1, "label_available_time"] = 999_999
    future_changed_requests = [event for event in replay(altered) if isinstance(event, Request)]
    assert requests == future_changed_requests

    without_delivery_assumption = conversion_rows(
        original, {"delay_unit": "seconds", "assume_instant_click_features": False}
    )
    with pytest.raises(ValueError, match="Unknown prediction times"):
        list(replay(without_delivery_assumption))


def test_wilds_text_references_preserve_partitions_without_labels(tmp_path):
    original = pd.DataFrame(
        {
            "comment_text": ["fixture A", "fixture B", "fixture C"],
            "toxicity": [0.1, 0.8, 0.2],
            "split": ["train", "val", "test"],
            **{name: [0.0, 1.0, 0.0] for name in IDENTITIES},
        }
    )
    raw = tmp_path / "raw.csv"
    original.to_csv(raw)
    path = civilcomments_export(
        original, {"dataset": "civilcomments", "max_per_split": 1}, tmp_path, [raw]
    )
    frame = pd.read_parquet(path / "observations.parquet")
    assert frame.split.tolist() == ["train", "validation", "test"]
    assert frame.target.tolist() == [0.0, 1.0, 0.0]
    assert load_input(path, frame.feature_reference.iloc[1]) == "fixture B"
    assert pq_columns(path / "inputs.parquet") == ["text"]
    assert validate_dataset(path)["feature_missing_rate"] is None
    manifest = json.loads((path / "dataset_manifest.json").read_text())
    assert manifest["feature_kind"] == "structured_reference"
    assert manifest["task_specs"][0]["task_kind"] == "official_classification"
    assert np.isfinite(frame.target.to_numpy(dtype=float)).all()


def pq_columns(path):
    import pyarrow.parquet as pq

    return pq.read_schema(path).names


@pytest.mark.parametrize("name", ["amazon", "fmow", "iwildcam", "camelyon17"])
def test_wilds_official_export_is_lazy(tmp_path, name):
    class Official:
        split_dict: ClassVar[dict] = {"train": 0, "val": 1, "test": 2, "id_val": 3}
        y_array = np.array([0, 1, 0, 1])
        split_array = np.arange(4)
        metadata_array = np.arange(4)[:, None]
        metadata_fields: ClassVar[list] = ["hospital"]
        version = "1.0"
        data_dir = tmp_path

        def get_input(self, index):
            raise AssertionError("Images/text must not be eagerly loaded")

    path = from_official(Official(), {"dataset": name, "max_per_split": 1}, tmp_path)
    frame = pd.read_parquet(path / "observations.parquet")
    assert len(frame) == 4
    assert [json.loads(m)["official_split"] for m in frame.metadata] == [
        "train",
        "val",
        "test",
        "id_val",
    ]
    assert all(json.loads(ref)["kind"] == "wilds" for ref in frame.feature_reference)
    manifest = json.loads((path / "dataset_manifest.json").read_text())
    assert manifest["task_specs"][0]["task_kind"] == "official_classification"
    assert np.isfinite(frame.target.to_numpy(dtype=float)).all()
    assert validate_dataset(path)["rows"] == 4
