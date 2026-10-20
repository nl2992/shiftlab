import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.eia import _bulk_records, _retrospective_splits_if_feasible


def test_eia_bulk_extracts_requested_utc_hourly_series(tmp_path):
    archive_path = tmp_path / "EBA.zip"
    payloads = [
        {
            "series_id": "EBA.NYIS-ALL.D.H",
            "f": "H",
            "data": [
                ["20230103T00", "30"],
                ["20230102T23", "20"],
                ["20230102T22", "10"],
            ],
        },
        {
            "series_id": "EBA.NYIS-ALL.DF.H",
            "f": "H",
            "data": [["20230102T23", "21"], ["20230102T22", "11"]],
        },
        {
            "series_id": "EBA.CAL-ALL.D.H",
            "f": "H",
            "data": [["20230102T23", "999"]],
        },
    ]
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("EBA.txt", "".join(json.dumps(row) + "\n" for row in payloads))

    rows = _bulk_records(
        archive_path,
        respondents=["NYIS"],
        types=["D", "DF"],
        start="2023-01-02T22",
        end="2023-01-02T23",
        max_records=10,
    )

    assert {(row["respondent"], row["type"], row["period"], row["value"]) for row in rows} == {
        ("NYIS", "D", "20230102T22", "10"),
        ("NYIS", "D", "20230102T23", "20"),
        ("NYIS", "DF", "20230102T22", "11"),
        ("NYIS", "DF", "20230102T23", "21"),
    }


def test_eia_bulk_requires_every_requested_series(tmp_path):
    archive_path = tmp_path / "EBA.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "EBA.txt",
            json.dumps({"series_id": "EBA.NYIS-ALL.D.H", "f": "H", "data": []}) + "\n",
        )

    with pytest.raises(ValueError, match="lacks requested series"):
        _bulk_records(
            archive_path,
            respondents=["NYIS"],
            types=["D", "DF"],
            start="2023-01-02T22",
            end="2023-01-02T23",
            max_records=10,
        )


def test_eia_bulk_rejects_non_utc_hourly_series(tmp_path):
    archive_path = tmp_path / "EBA.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "EBA.txt",
            json.dumps({"series_id": "EBA.NYIS-ALL.D.H", "f": "HL", "data": []}) + "\n",
        )

    with pytest.raises(ValueError, match="Expected UTC hourly"):
        _bulk_records(
            archive_path,
            respondents=["NYIS"],
            types=["D"],
            start="2023-01-02T22",
            end="2023-01-02T23",
            max_records=10,
        )


def test_eia_bulk_normalizes_offset_bounds_to_utc(tmp_path):
    archive_path = tmp_path / "EBA.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "EBA.txt",
            json.dumps(
                {
                    "series_id": "EBA.NYIS-ALL.D.H",
                    "f": "H",
                    "data": [["20230102T03", "12"]],
                }
            )
            + "\n",
        )

    rows = _bulk_records(
        archive_path,
        respondents=["NYIS"],
        types=["D"],
        start="2023-01-01T22:00:00-05:00",
        end="2023-01-02T03:00:00Z",
        max_records=10,
    )

    assert [row["period"] for row in rows] == ["20230102T03"]


def test_eia_retrospective_splits_purge_one_hour_boundary_targets():
    event_times = np.arange(100, dtype=float) * 3600
    frame = pd.DataFrame({"event_time": event_times, "label_event_time": event_times + 3600})

    result = _retrospective_splits_if_feasible(frame)

    assert set(result.split) == {"train", "validation", "calibration", "test", "unassigned"}
    for earlier, later in [
        ("train", "validation"),
        ("validation", "calibration"),
        ("calibration", "test"),
    ]:
        early_rows = result[result.split == earlier]
        late_rows = result[result.split == later]
        assert early_rows.label_event_time.max() < late_rows.event_time.min()


def test_eia_tiny_fixture_rows_remain_unassigned():
    frame = pd.DataFrame(
        {
            "event_time": [0.0, 3600.0],
            "label_event_time": [3600.0, 7200.0],
            "split": ["unassigned", "unassigned"],
        }
    )

    result = _retrospective_splits_if_feasible(frame)

    assert result.split.tolist() == ["unassigned", "unassigned"]
