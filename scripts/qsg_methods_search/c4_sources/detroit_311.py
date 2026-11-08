"""Detroit Improve Detroit 311 issues (data.detroitmi.gov, ArcGIS Hub improve_detroit layer):
closed within 14 days of creation.

Label rationale (fixed before downloading, from documentation/domain knowledge): Improve Detroit
tickets are dominated by blight and public-works work orders (illegal dumping, abandoned vehicles,
tire removal, potholes, street lights, signs, graffiti, water/sewer) with multi-day to multi-week
crew scheduling, so a 14-day threshold is expected to put the base rate in the middle of
[0.2, 0.8]. Open or closed-later = 0. The window ends ~10 months before the fetch so status is
settled. closed_at is used only for the label; status, acknowledged_at, updated_at, reopened_at,
num_days_to_close and num_hours_to_close are never features. Features are set at intake: request
type, report method, priority code, neighbourhood, council district, zip code, created
hour/dow/month (America/Detroit local).
"""

from __future__ import annotations

import pandas as pd

from c4_sources._dl_arcgis import fetch_arcgis

LAYER = (
    "https://services2.arcgis.com/qvkbeam7Wirps6zC/ArcGIS/rest/services/"
    "improve_detroit/FeatureServer/0"
)
FIELDS = (
    "request_type,report_method,priority_code,neighborhood,council_district,zip_code,"
    "created_at,closed_at"
)
WINDOW = ("2024-01-01T00:00:00", "2026-01-01T00:00:00")  # local time
THRESH_DAYS = 14
META = {
    "name": "detroit_311",
    "url": LAYER,
    "license": "City of Detroit Open Data Portal (data.detroitmi.gov), public open data",
    "publisher": "City of Detroit (Improve Detroit / DoIT)",
    "task": "binary: Improve Detroit issue closed within 14 days of creation",
    "label": f"closed_at present and closed_at - created_at <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "request type, report method, priority code, neighbourhood, council "
    "district, zip, created hour/dow/month: all recorded at intake",
}
NUM = ["hour", "dow", "month"]
CAT = ["request_type", "method", "priority", "neighborhood", "council", "zip"]
FILE = "detroit311_2024_2025.csv"
TZ = "America/Detroit"


def fetch(raw):
    where = "created_at >= TIMESTAMP '2023-12-31 00:00:00' AND created_at < TIMESTAMP '2026-01-02 00:00:00'"
    fetch_arcgis(LAYER, FIELDS, where, "ObjectId", raw, FILE, 1000)


def _dt(s):
    return (
        pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True)
        .dt.tz_convert(TZ)
        .dt.tz_localize(None)
    )


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = _dt(d["created_at"])
    closed = _dt(d["closed_at"])
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "request_type": d["request_type"],
            "method": d["report_method"],
            "priority": d["priority_code"],
            "neighborhood": d["neighborhood"],
            "council": d["council_district"],
            "zip": d["zip_code"],
        }
    )
    out = out.dropna(subset=["ts"])
    out = out[(out.ts >= WINDOW[0]) & (out.ts < WINDOW[1])]
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
