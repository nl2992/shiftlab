"""Austin 311 Public Data (City of Austin, data.austintexas.gov xwdj-i9he): closed within 7 days.

Label rationale (fixed before building, from documentation/domain knowledge): Austin 311 mixes
same-day/first-days police, fire and resource-recovery requests with slower code-compliance and
public-works work; a one-week threshold is expected to give a base rate inside [0.3, 0.7].
Still-open requests (no sr_closed_date) are 0; closed within 7 days of creation is 1. The window
ends 16 months before the fetch so status has settled. sr_status_desc, sr_status_date,
sr_updated_date and sr_closed_date are never features. Features are request type, handling
department, intake channel, council district, zip, and created time parts.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.austintexas.gov/resource/xwdj-i9he.csv"
COLS = (
    "sr_created_date,sr_closed_date,sr_type_desc,sr_department_desc,sr_method_received_desc,sr_location_council_district,sr_location_zip_code"
    ""
)
WINDOW = ("2024-01-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 7
META = {
    "name": "austin_311",
    "url": URL,
    "license": "Open data (data.austintexas.gov, City of Austin)",
    "publisher": "City of Austin (Austin 311 Unified Data)",
    "task": "binary: Austin 311 service request closed within 7 days of creation",
    "label": f"sr_closed_date present and sr_closed_date - sr_created_date <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "created hour/dow/month, request type, department, intake channel, council district, zip",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "sr_type_desc",
    "sr_department_desc",
    "sr_method_received_desc",
    "sr_location_council_district",
    "sr_location_zip_code",
]
FILE = "austin311_2024-01_2025-06.csv"


def fetch(raw: Path) -> None:
    where = f"sr_created_date >= '{WINDOW[0]}' AND sr_created_date < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "sr_created_date", "$limit": 1_500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["sr_created_date"], errors="coerce")
    closed = pd.to_datetime(d["sr_closed_date"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"])
