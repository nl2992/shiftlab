from collections import Counter

import pandas as pd

from scripts.build_crsp_study_panel import _attach_next, _to_observations


def _crsp_rows(records):
    rows = []
    for permno, date, ret, missflag, duration in records:
        rows.append(
            {
                "permno": permno,
                "permco": permno,
                "dlycaldt": date,
                "ticker": "TST",
                "securitytype": "EQTY",
                "securitysubtype": "COM",
                "sharetype": "NS",
                "primaryexch": "N",
                "tradingstatusflg": "A",
                "dlydelflg": "",
                "dlyret": ret,
                "dlyretx": ret,
                "dlyreti": ret,
                "dlyretmissflg": missflag,
                "dlyretdurflg": duration,
                "dlyprc": 10.0,
                "dlyprcflg": "",
                "dlyprevprc": 10.0,
                "dlyprevprcflg": "",
                "dlyvol": 100.0,
                "dlycap": 1000.0,
                "dlycapflg": "",
                "dlynumtrd": 5,
                "vwretd": ret,
                "vwretx": ret,
                "ewretd": ret,
                "ewretx": ret,
                "sprtrn": ret,
            }
        )
    return pd.DataFrame(rows)


def test_next_return_stays_with_permno_and_connects_year_boundary():
    frame = _crsp_rows(
        [
            (1, "2000-12-29", 0.01, "NA", "D1"),
            (2, "2000-12-29", 0.02, "NA", "D1"),
        ]
    )
    boundary = {
        (2000, 1): {
            "date": "2001-01-02",
            "ret": 0.03,
            "missflag": "NA",
            "duration": "D1",
            "delflag": "",
        },
        (2000, 2): {
            "date": "2001-01-03",
            "ret": 0.04,
            "missflag": "NA",
            "duration": "D1",
            "delflag": "",
        },
    }

    result = _attach_next(frame, 2000, boundary)

    assert result["_target_return"].tolist() == [0.03, 0.04]
    assert result["_target_date"].tolist() == ["2001-01-02", "2001-01-03"]


def test_bad_immediate_target_is_dropped_without_skipping_ahead():
    frame = _crsp_rows(
        [
            (1, "2000-01-03", 0.01, "NA", "D1"),
            (1, "2000-01-04", 0.02, "MP", "MR"),
            (1, "2000-01-05", 0.03, "NA", "D1"),
        ]
    )
    boundary = {
        (2000, 1): {
            "date": "2000-01-06",
            "ret": 0.04,
            "missflag": "NA",
            "duration": "D1",
            "delflag": "",
        }
    }

    result = _to_observations(frame, 2000, boundary, Counter())

    # Jan 3's immediate next record is invalid, so Jan 3 is not relabeled with Jan 5's return.
    assert result["dlycaldt"].tolist() == ["2000-01-04", "2000-01-05"]
    assert result["target"].tolist() == [0.03, 0.04]


def test_target_crossing_a_chronological_split_is_unassigned():
    frame = _crsp_rows([(1, "2014-12-31", 0.01, "NA", "D1")])
    boundary = {
        (2014, 1): {
            "date": "2015-01-02",
            "ret": 0.02,
            "missflag": "NA",
            "duration": "D1",
            "delflag": "",
        }
    }

    result = _to_observations(frame, 2014, boundary, Counter())

    assert result["split"].tolist() == ["unassigned"]
    assert result["target_date"].tolist() == ["2015-01-02"]
