"""Chicago Food Inspections (Chicago Dept. of Public Health, data.cityofchicago.org 4ijn-s7e5): result == 'Pass'.

Label rationale (fixed before building, from the dataset documentation/domain knowledge): each
completed inspection ends in Pass, Pass w/ Conditions or Fail. Pass is the clean outcome; a
mixed base rate (roughly 0.5-0.7) is expected. Label = 1 iff results == 'Pass'; Pass w/
Conditions and Fail are 0. Rows whose results are Out of Business, No Entry, Not Ready or
Business Not Located are dropped: the data dictionary defines them as inspections that could not
be carried out, so there is no outcome to predict. This rule was decided before downloading.
Features: facility type, risk category, inspection type, zip, and the day of week/month of the
inspection. inspection_date is date-only, so hour is not a feature; ties within a day are ordered
by inspection_id. Excluded: violations (the findings text, post-inspection), results (label),
license number, names, address and coordinates. Window 2013-01-01 to 2026-07-01.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.cityofchicago.org/resource/4ijn-s7e5.csv"
COLS = "inspection_id,inspection_date,facility_type,risk,inspection_type,zip,results"
WINDOW = ("2013-01-01T00:00:00", "2026-07-01T00:00:00")
DROP = {"Out of Business", "No Entry", "Not Ready", "Business Not Located"}
META = {
    "name": "chicago_food_inspections",
    "url": URL,
    "license": "City of Chicago open data terms of use (data.cityofchicago.org)",
    "publisher": "City of Chicago, Chicago Department of Public Health (Food Inspections)",
    "task": "binary: food inspection result is Pass (vs Fail / Pass w/ Conditions)",
    "label": "results == 'Pass'; non-inspections (Out of Business, No Entry, Not Ready, Business Not Located) dropped",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "facility type, risk, inspection type, zip, inspection dow/month; violations text excluded",
}
NUM = ["dow", "month"]
CAT = ["facility_type", "risk", "inspection_type", "zip"]
FILE = "chicago_food_2013-01_2026-06.csv"


def fetch(raw: Path) -> None:
    where = f"inspection_date >= '{WINDOW[0]}' AND inspection_date < '{WINDOW[1]}'"
    download(
        URL,
        {
            "$select": COLS,
            "$where": where,
            "$order": "inspection_date,inspection_id",
            "$limit": 1_500_000,
        },
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    d = d[~d["results"].isin(DROP) & d["results"].notna()].copy()
    day = pd.to_datetime(d["inspection_date"], errors="coerce").dt.normalize()
    d = d.assign(_day=day, _id=pd.to_numeric(d["inspection_id"], errors="coerce")).dropna(
        subset=["_day"]
    )
    d = d.sort_values(["_day", "_id"], kind="stable").reset_index(drop=True)
    within = d.groupby("_day").cumcount()
    ts = d["_day"] + pd.to_timedelta(within.clip(upper=86399), unit="s")
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": (d["results"] == "Pass").astype(int),
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
        }
    )
    for c in CAT:
        out[c] = d[c]
    return out
