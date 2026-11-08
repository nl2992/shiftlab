"""Gainesville FL 311 myGNV service requests (data.cityofgainesville.org 78uv-94ar): closed within 3 days.

Label rationale (fixed before building, from documentation/domain knowledge): the portal states
CLOSED means the request was turned into a work order or resolved with the requester, so closure
is a staff triage event rather than field completion, and is expected to be fairly quick;
a 3-day threshold is expected to give a base rate inside [0.3, 0.7]. Requests with no `closed`
timestamp are 0; closed - created <= 3 days is 1. The published data end 2021-06-18 (platform
change, per the dataset disclaimer), so the window is 2019-06-01 to 2021-06-01 by creation time
(>5 years before the fetch). The dataset is small (16k rows in total), so the builder's episode
gate may exclude it; that outcome is accepted and not worked around.
status, last_updated, acknowledged, reopened, closed (label only), minutes_to_*, days_to_close,
assigned_to (assigned after intake), description/location_detail (free text), reporter_display
(may be a user name) and coordinates are never features. Features are request type, mobile flag,
police sector, commission district and created hour/dow/month.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.cityofgainesville.org/resource/78uv-94ar.csv"
COLS = "created,closed,request_type,reported_using_mobile,police_sector,commission_district"
WINDOW = ("2019-06-01T00:00:00", "2021-06-01T00:00:00")
THRESH_DAYS = 3
META = {
    "name": "gainesville_311",
    "url": URL,
    "license": "Public Domain (City of Gainesville open data, per Socrata metadata)",
    "publisher": "City of Gainesville FL (myGNV 311 Service Requests)",
    "task": "binary: Gainesville 311 request closed within 3 days of creation",
    "label": f"closed present and closed - created <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "request type, mobile flag, police sector, commission district, created hour/dow/month",
}
NUM = ["hour", "dow", "month"]
CAT = ["request_type", "reported_using_mobile", "police_sector", "commission_district"]
FILE = "gainesville311_2019-06_2021-05.csv"


def fetch(raw: Path) -> None:
    where = f"created >= '{WINDOW[0]}' AND created < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "created", "$limit": 1_000_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["created"], errors="coerce")
    closed = pd.to_datetime(d["closed"], errors="coerce", format="mixed")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"]).sort_values("ts", kind="stable").reset_index(drop=True)
