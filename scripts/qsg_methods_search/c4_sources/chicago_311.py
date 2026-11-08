"""Chicago 311 Service Requests (data.cityofchicago.org v6vf-nfxy): closed within 7 days of creation.

Label rationale (fixed before downloading, from documentation/domain knowledge): Chicago 311
requests mix information-only calls and quick service tickets (closed same day), streets and
sanitation requests (days to a couple of weeks) and building/forestry/rodent work (weeks). A 7-day
threshold is expected to place the base rate inside [0.3, 0.7]. Still-open (no closed_date) = 0.
Window is one calendar year (2024; ~1.9M rows, to stay under the 400 MB raw limit) ending more
than 22 months before the fetch; the builder subsamples to N_MAX. closed_date is used only for the
label; status, last_modified_date, owner_department (reassigned after intake), duplicate,
parent_sr_number, legacy fields, street address and coordinates are never features. Features:
SR type, creating department, intake origin, zip, community area, ward, police district, created
hour/dow/month (timestamps are local Chicago time as published).
"""

from __future__ import annotations

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.cityofchicago.org/resource/v6vf-nfxy.csv"
COLS = (
    "created_date,closed_date,sr_type,created_department,origin,zip_code,community_area,ward,"
    "police_district"
)
WINDOW = ("2024-01-01T00:00:00", "2025-01-01T00:00:00")
THRESH_DAYS = 7
META = {
    "name": "chicago_311",
    "url": URL,
    "license": "City of Chicago Data Portal terms of use (public open data)",
    "publisher": "City of Chicago (311 Service Requests)",
    "task": "binary: Chicago 311 request closed within 7 days of creation",
    "label": f"closed_date present and closed_date - created_date <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "SR type, creating department, origin, zip, community area, ward, police district, hour/dow/month: intake-time",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "sr_type",
    "created_department",
    "origin",
    "zip_code",
    "community_area",
    "ward",
    "police_district",
]
FILE = "chicago311_2024.csv"


def fetch(raw):
    where = f"created_date >= '{WINDOW[0]}' AND created_date < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "created_date", "$limit": 3_000_000},
        raw / FILE,
    )


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["created_date"], errors="coerce")
    closed = pd.to_datetime(d["closed_date"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
        }
    )
    for c in CAT:
        out[c] = d[c]
    out = out.dropna(subset=["ts"])
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
