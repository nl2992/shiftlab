"""Miami-Dade County 311 Service Requests 2022-2023 (Miami-Dade Open Data Hub, ArcGIS
FeatureServers data_311_2022 / data_311_2023): closed within 7 days of creation.

Label rationale (fixed before downloading, from documentation/domain knowledge): Miami-Dade 311
tickets are routed to solid waste, public works, animal services, regulatory/code and
information-style handling with goal days from same-day to a few weeks; a 7-day threshold is
expected to put the base rate inside [0.3, 0.7]. Tickets without ticket_closed_date_time are 0;
closed - created <= 7 days is 1. The window ends 22 months before the fetch.
ticket_status, ticket_closed_date_time, ticket__last_update_date_time, actual_completed_days and
goal_days (SLA) are never features. Features are issue type/description, owning department,
zip, neighbourhood district, intake channel, priority, and created hour/dow/month
(America/New_York local).
"""

from __future__ import annotations

import pandas as pd

from c4_sources._dl_arcgis import fetch_arcgis

BASE = (
    "https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/data_311_{y}/FeatureServer/0"
)
YEARS = (2022, 2023)
FIELDS = (
    "issue_type,issue_description,case_owner,zip_code,neighborhood_district,method_received,"
    "sr_priority,ticket_created_date_time,ticket_closed_date_time,ObjectId"
)
WINDOW = ("2022-01-01T00:00:00", "2024-01-01T00:00:00")  # local time
THRESH_DAYS = 7
META = {
    "name": "miamidade_311",
    "url": BASE.format(y="{2022,2023}"),
    "license": "Miami-Dade County Open Data Hub (gis-mdc.opendata.arcgis.com), public open data",
    "publisher": "Miami-Dade County (311 Service Requests)",
    "task": "binary: Miami-Dade 311 ticket closed within 7 days of creation",
    "label": f"ticket_closed_date_time present and closed - created <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "issue type/description, case owner, zip, neighbourhood district, intake channel, priority, created hour/dow/month",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "issue_type",
    "issue_description",
    "case_owner",
    "zip",
    "neighborhood_district",
    "method",
    "priority",
]


def _file(y):
    return f"miamidade311_{y}.csv"


def fetch(raw):
    for y in YEARS:
        fetch_arcgis(BASE.format(y=y), FIELDS, "1=1", "ObjectId", raw, _file(y), 1000)


def _dt(s):
    return (
        pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True)
        .dt.tz_convert("America/New_York")
        .dt.tz_localize(None)
    )


def load(raw):
    d = pd.concat([pd.read_csv(raw / _file(y), dtype=str) for y in YEARS], ignore_index=True)
    ts = _dt(d["ticket_created_date_time"])
    closed = _dt(d["ticket_closed_date_time"])
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "issue_type": d["issue_type"],
            "issue_description": d["issue_description"],
            "case_owner": d["case_owner"],
            "zip": d["zip_code"],
            "neighborhood_district": d["neighborhood_district"],
            "method": d["method_received"],
            "priority": d["sr_priority"],
        }
    )
    out = out.dropna(subset=["ts"])
    out = out[(out.ts >= WINDOW[0]) & (out.ts < WINDOW[1])]
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
