"""Buffalo 311 Service Requests (City of Buffalo, data.buffalony.gov whkc-e5vr, July 2008 - May 2024): closed within 7 days.

Label rationale (fixed before building, from documentation/domain knowledge): Buffalo 311 mixes
Public Works sanitation/pick-up requests that close in days with code, streets and inspection
cases that stay open for weeks; a one-week threshold is expected to give a base rate inside
[0.3, 0.7]. Still-open requests (no closed_date) are 0; closed within 7 days is 1. The window is
the last 35 months of the archived dataset (frozen at May 2024; the successor dataset has a
different schema and is not used). status and closed_date are never features. Features are
subject (department), reason, type, object type, council district, police district, neighbourhood,
zip and opened time parts.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.buffalony.gov/resource/whkc-e5vr.csv"
COLS = (
    "open_date,closed_date,subject,reason,type,object_type,council_district,police_district,neighborhood,zip_code"
    ""
)
WINDOW = ("2021-06-01T00:00:00", "2024-05-01T00:00:00")
THRESH_DAYS = 7
META = {
    "name": "buffalo_311",
    "url": URL,
    "license": "Open data (data.buffalony.gov, City of Buffalo)",
    "publisher": "City of Buffalo (311 Call and Resolution Center)",
    "task": "binary: Buffalo 311 request closed within 7 days of opening",
    "label": f"closed_date present and closed_date - open_date <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "open hour/dow/month, subject, reason, type, object type, council district, police district, neighbourhood, zip",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "subject",
    "reason",
    "type",
    "object_type",
    "council_district",
    "police_district",
    "neighborhood",
    "zip_code",
]
FILE = "buffalo311_2021-06_2024-04.csv"


def fetch(raw: Path) -> None:
    where = f"open_date >= '{WINDOW[0]}' AND open_date < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "open_date", "$limit": 1_500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["open_date"], errors="coerce")
    closed = pd.to_datetime(d["closed_date"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"])
