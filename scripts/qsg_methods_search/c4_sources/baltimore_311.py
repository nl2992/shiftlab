"""Baltimore 311 Customer Service Requests 2024 (Open Baltimore, ArcGIS Hub data.baltimorecity.gov):
closed within 7 days of creation.

Label rationale (fixed before downloading, from documentation/domain knowledge): Baltimore 311
requests are routed to DPW/Transportation/Housing/Health/etc. work orders whose published
service-level targets range from same-day to a few weeks (trash and cleaning in days, housing
and rodent complaints in 1-3 weeks). A 7-day threshold is expected to put the base rate in the
middle of [0.2, 0.8]. Open or closed-later = 0. The 2024 layer is fetched ~2 years later so
status is settled. CloseDate is used only for the label; SRStatus, StatusDate, DueDate,
LastActivity, LastActivityDate and Outcome are never features. Features are set at intake: request
type, intake method, agency (derived from request type), neighbourhood, council and police
district, zip code, created hour/dow/month (America/New_York local).
"""

from __future__ import annotations

import pandas as pd

from c4_sources._dl_arcgis import fetch_arcgis

LAYER = (
    "https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/"
    "311_Customer_Service_Requests_2024/FeatureServer/0"
)
FIELDS = (
    "SRType,MethodReceived,Agency,Neighborhood,CouncilDistrict,PoliceDistrict,ZipCode,"
    "CreatedDate,CloseDate"
)
WINDOW = ("2024-09-01T00:00:00", "2025-01-01T00:00:00")  # local time
THRESH_DAYS = 7
META = {
    "name": "baltimore_311",
    "url": LAYER,
    "license": "Open Baltimore (data.baltimorecity.gov), City of Baltimore, public open data",
    "publisher": "City of Baltimore (Open Baltimore / 311)",
    "task": "binary: 311 service request closed within 7 days of creation",
    "label": f"CloseDate present and CloseDate - CreatedDate <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "request type, method received, agency, neighbourhood, council/police "
    "district, zip, created hour/dow/month: all recorded at intake",
}
NUM = ["hour", "dow", "month"]
CAT = ["sr_type", "method", "agency", "neighborhood", "council", "police", "zip"]
FILE = "baltimore311_2024-09_2024-12.csv"


def fetch(raw):
    # server filter is UTC and slightly wider than the local window; load() applies the exact one
    where = "CreatedDate >= TIMESTAMP '2024-08-31 00:00:00' AND CreatedDate < TIMESTAMP '2025-01-02 00:00:00'"
    fetch_arcgis(LAYER, FIELDS, where, "RowID", raw, FILE, 2000)


def _dt(s):
    return (
        pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True)
        .dt.tz_convert("America/New_York")
        .dt.tz_localize(None)
    )


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = _dt(d["CreatedDate"])
    closed = _dt(d["CloseDate"])
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "sr_type": d["SRType"],
            "method": d["MethodReceived"],
            "agency": d["Agency"],
            "neighborhood": d["Neighborhood"],
            "council": d["CouncilDistrict"],
            "police": d["PoliceDistrict"],
            "zip": d["ZipCode"],
        }
    )
    out = out.dropna(subset=["ts"])
    out = out[(out.ts >= WINDOW[0]) & (out.ts < WINDOW[1])]
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
