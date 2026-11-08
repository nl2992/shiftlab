"""Minneapolis Public 311 incidents 2023-2024 (Open Minneapolis, City of Minneapolis ArcGIS
FeatureServers Public_311_2023 / Public_311_2024): closed within 7 days of creation.

Label rationale (fixed before downloading, from documentation/domain knowledge): Minneapolis 311
cases span quick-turnaround work (graffiti, trash/recycling, street lights, abandoned vehicles,
snow/ice) and slower housing, inspection and street-repair cases; a 7-day threshold is expected
to put the base rate inside [0.3, 0.7]. Still-open cases (no CLOSEDDATETIME) are 0;
CLOSEDDATETIME - OPENEDDATETIME <= 7 days is 1. The window ends 22 months before the fetch.
CASESTATUS, CLOSEDDATETIME, LastUpdateDate and CASEID are never features. Features are subject
(department), reason, type and title of the request (all set at intake) plus opened hour/dow/month
(America/Chicago local).
"""

from __future__ import annotations

import pandas as pd

from c4_sources._dl_arcgis import fetch_arcgis

BASE = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/ArcGIS/rest/services/Public_311_{y}/FeatureServer/0"
YEARS = (2023, 2024)
FIELDS = "SUBJECTNAME,REASONNAME,TYPENAME,TITLE,OPENEDDATETIME,CLOSEDDATETIME,OBJECTID"
WINDOW = ("2023-01-01T00:00:00", "2025-01-01T00:00:00")  # local time
THRESH_DAYS = 7
META = {
    "name": "minneapolis_311",
    "url": BASE.format(y="{2023,2024}"),
    "license": "Open Minneapolis (opendata.minneapolismn.gov), City of Minneapolis, public open data (Creative Commons)",
    "publisher": "City of Minneapolis (Public 311 incidents)",
    "task": "binary: Minneapolis 311 case closed within 7 days of opening",
    "label": f"CLOSEDDATETIME present and CLOSEDDATETIME - OPENEDDATETIME <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "subject, reason, type, title (intake), opened hour/dow/month",
}
NUM = ["hour", "dow", "month"]
CAT = ["subject", "reason", "type", "title"]


def _file(y):
    return f"minneapolis311_{y}.csv"


def fetch(raw):
    for y in YEARS:
        fetch_arcgis(BASE.format(y=y), FIELDS, "1=1", "OBJECTID", raw, _file(y), 8000)


def _dt(s):
    return (
        pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True)
        .dt.tz_convert("America/Chicago")
        .dt.tz_localize(None)
    )


def load(raw):
    d = pd.concat([pd.read_csv(raw / _file(y), dtype=str) for y in YEARS], ignore_index=True)
    ts = _dt(d["OPENEDDATETIME"])
    closed = _dt(d["CLOSEDDATETIME"])
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "subject": d["SUBJECTNAME"],
            "reason": d["REASONNAME"],
            "type": d["TYPENAME"],
            "title": d["TITLE"],
        }
    )
    out = out.dropna(subset=["ts"])
    out = out[(out.ts >= WINDOW[0]) & (out.ts < WINDOW[1])]
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
