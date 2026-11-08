"""City of Boston 311 Service Requests, calendar-year 2024 (data.boston.gov): closed within 2 days.

Label rationale (fixed before building, from documentation/domain knowledge): Boston 311 mixes
quickly handled routine requests (parking enforcement, trash/recycling pickup, street light and
sign reports, many closed same day or next day) with slower field-work requests (potholes,
sidewalk, tree work, housing). A 2-day threshold is expected to give a base rate in the middle of
[0.2, 0.8]. Still-open cases (no closed_dt) are 0. The window (2024) ended almost two years before
the fetch, so open status is settled.
closed_dt is used only for the label; case_status, closure_reason, on_time, sla_target_dt,
closed_photo are never features. queue, department and submitted_photo are excluded:
documentation does not guarantee they are fixed at intake (queue/department can be re-routed).
case_title is excluded (free-form text derived from type). Location block fields (neighborhood,
ward, district, zip) are derived from the reported location at opening.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = (
    "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/"
    "dff4d804-5031-443a-8409-8344efd0e5c8/download/lagan_311_open_data_2024_rvsd3.csv"
)
WINDOW = ("2024-01-01T00:00:00", "2025-01-01T00:00:00")
THRESH_DAYS = 2
META = {
    "name": "boston_311",
    "url": URL,
    "license": "Open Data Commons Public Domain Dedication and License (PDDL), City of Boston",
    "publisher": "City of Boston (Analyze Boston / data.boston.gov)",
    "task": "binary: 311 case closed within 2 days of being opened",
    "label": f"closed_dt present and closed_dt - open_dt <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "open hour/dow/month, subject, reason, type, source channel, neighborhood, "
    "ward, police district, city council district, zip: all recorded at case opening",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "subject",
    "reason",
    "type",
    "source",
    "neighborhood",
    "ward",
    "police_district",
    "city_council_district",
    "location_zipcode",
]
FILE = "boston311_2024.csv"
_USE = ["open_dt", "closed_dt"] + CAT


def fetch(raw: Path) -> None:
    download(URL, {}, raw / FILE)


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str, usecols=_USE)
    ts = pd.to_datetime(d["open_dt"], errors="coerce")
    closed = pd.to_datetime(d["closed_dt"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> False -> 0
    out = pd.DataFrame(
        {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"])
