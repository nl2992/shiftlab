"""Louisville Metro KY 311 Service Requests 2023-2024 (Louisville Metro open data, ArcGIS FeatureServer):
closed within 7 days of creation.

Label rationale (fixed before downloading, from documentation/domain knowledge): Louisville Metro 311
(MetroCall) requests are routed to Solid Waste, Public Works, Codes & Regulations, Animal Services
etc.; missed pickups and many service calls are closed within days, while code, tall-weed and
street-repair cases run weeks. A 7-day threshold is expected to place the base rate inside [0.3, 0.7].
Open or closed-later = 0. The window ends 22 months before the fetch so labels are settled.
closed_date is used only for the label; status_description, status_notes, updated_datetime,
description (free text), address, probyear and coordinates are never features. Features are set at
intake: service name, intake source, responsible agency (routed by type), zip code, council
district, created hour/dow/month (America/New_York local; the layer stores UTC).
Two yearly layers (2023, 2024) are concatenated.
"""

from __future__ import annotations

import pandas as pd

from c4_sources._dl_arcgis import fetch_arcgis

BASE = "https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/"
LAYERS = {
    "2023": BASE + "metro_call_311_service_requests_2023/FeatureServer/0",
    "2024": BASE + "Louisville_Metro_KY_Metro_311_Service_Requets_2024/FeatureServer/0",
}
FIELDS = "source,service_name,agency_responsible,zip_code,council_district,requested_datetime,closed_date"
WINDOW = ("2023-01-01T00:00:00", "2025-01-01T00:00:00")  # local time
THRESH_DAYS = 7
META = {
    "name": "louisville_311",
    "url": ";".join(LAYERS.values()),
    "license": "Louisville Metro Open Data (data.louisvilleky.gov), public open data",
    "publisher": "Louisville Metro Government (Metro 311 Service Requests)",
    "task": "binary: Louisville 311 request closed within 7 days of creation",
    "label": f"closed_date present and closed_date - requested_datetime <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "service name, source, responsible agency, zip, council district, "
    "hour/dow/month: all recorded at intake",
}
NUM = ["hour", "dow", "month"]
CAT = ["service_name", "source", "agency", "zip", "council"]


def _file(y):
    return f"louisville311_{y}.csv"


def fetch(raw):
    for y, layer in LAYERS.items():
        fetch_arcgis(layer, FIELDS, "1=1", "ObjectId", raw, _file(y), 1000)


def _dt(s):
    return (
        pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True)
        .dt.tz_convert("America/New_York")
        .dt.tz_localize(None)
    )


def load(raw):
    d = pd.concat([pd.read_csv(raw / _file(y), dtype=str) for y in LAYERS], ignore_index=True)
    ts = _dt(d["requested_datetime"])
    closed = _dt(d["closed_date"])
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "service_name": d["service_name"],
            "source": d["source"],
            "agency": d["agency_responsible"],
            "zip": d["zip_code"],
            "council": d["council_district"],
        }
    )
    out = out.dropna(subset=["ts"])
    out = out[(out.ts >= WINDOW[0]) & (out.ts < WINDOW[1])]
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
