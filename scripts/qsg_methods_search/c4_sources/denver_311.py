"""Denver 311 service requests (City and County of Denver, ArcGIS Hub per-year layers): closed within 5 days.

Label rationale (fixed before building, from documentation/domain knowledge): Denver Pocketgov /
311 requests mix quick-turnaround field work (graffiti, trash, snow, abandoned vehicles, traffic
signals) and information/transfer calls with longer permit, code-enforcement and capital-project
cases, so a 5-day threshold is expected to give a base rate inside [0.3, 0.7]. Still-open requests
(no Case_Closed_dttm) are 0; Case_Closed_dttm - Case_Created_dttm <= 5 days is 1. The window
(2022-01-01 to 2024-01-01 by creation time) ends ~34 months before the fetch so labels are mature.
Case_Status, Case_Closed_Date, Case_Closed_dttm (label only), First_Call_Resolution, Case_Summary
(free text), addresses, coordinates and customer zip are never features. Features are request
type/topic/major area, agency, division, intake channel, council district, police district,
neighbourhood, incident zip and created hour/dow/month.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_arcgis import fetch_arcgis
except ImportError:
    from c4_sources._dl_arcgis import fetch_arcgis

BASE = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services"
LAYERS = {
    2022: f"{BASE}/311_Service_Requests_2022/FeatureServer/0",
    2023: f"{BASE}/311_Service_Requests_2023/FeatureServer/0",
}
FIELDS = (
    "Case_Created_dttm,Case_Closed_dttm,Case_Source,Agency,Division,Major_Area,Type,Topic,"
    "Council_District,Police_District,Neighborhood,Incident_Zip_Code"
)
WINDOW = ("2022-01-01T00:00:00", "2024-01-01T00:00:00")
THRESH_DAYS = 5
META = {
    "name": "denver_311",
    "url": LAYERS[2023],
    "license": "City and County of Denver open data (opendata-geospatialdenver.hub.arcgis.com), public use with as-is disclaimer",
    "publisher": "City and County of Denver (311 Service Requests, per-year layers 2022-2023)",
    "task": "binary: Denver 311 request closed within 5 days of creation",
    "label": f"Case_Closed_dttm present and Case_Closed_dttm - Case_Created_dttm <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "type, topic, major area, agency, division, intake channel, council/police district, neighbourhood, incident zip, created hour/dow/month",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "Case_Source",
    "Agency",
    "Division",
    "Major_Area",
    "Type",
    "Topic",
    "Council_District",
    "Police_District",
    "Neighborhood",
    "Incident_Zip_Code",
]


def fetch(raw: Path) -> None:
    for yr, url in LAYERS.items():
        fetch_arcgis(url, FIELDS, "1=1", "ObjectId", raw, f"denver311_{yr}.csv", 1000)


def load(raw: Path) -> pd.DataFrame:
    d = pd.concat(
        [pd.read_csv(raw / f"denver311_{y}.csv", dtype=str) for y in LAYERS], ignore_index=True
    )
    ts = pd.to_datetime(pd.to_numeric(d["Case_Created_dttm"], errors="coerce"), unit="ms")
    closed = pd.to_datetime(d["Case_Closed_dttm"], errors="coerce", format="mixed")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
    )
    for c in CAT:
        out[c] = d[c]
    out = out[(out["ts"] >= WINDOW[0]) & (out["ts"] < WINDOW[1])]
    return out.dropna(subset=["ts"]).sort_values("ts", kind="stable").reset_index(drop=True)
