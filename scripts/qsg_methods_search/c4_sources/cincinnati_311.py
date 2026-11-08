"""Cincinnati 311 (Non-Emergency) Service Requests (City of Cincinnati, data.cincinnati-oh.gov gcej-gmiw): closed within 14 days.

Label rationale (fixed before building, from documentation/domain knowledge): requests span
sanitation/trash and street work with service targets of days to a couple of weeks, and
building/code cases that take months; a two-week threshold is expected to give a base rate inside
[0.3, 0.7]. Still-open requests (no date_closed) are 0; date_closed - date_created <= 14 days
(date granularity) is 1. The window ends 16 months before the fetch. sr_status, sr_status_flag,
date_closed, date_status_change, date_last_update, date_dispatched, date_revised_completion*,
planned_* (SLA fields) and transfer counts are never features. Features are request type,
priority, group, department, division, intake channel, neighbourhood, police district and zip.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.cincinnati-oh.gov/resource/gcej-gmiw.csv"
COLS = (
    "date_created,time_received,date_closed,sr_type_desc,priority,group_title,dept_name,dept_division,method_received,neighborhood,police_district,zipcode"
    ""
)
WINDOW = ("2023-07-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 14
META = {
    "name": "cincinnati_311",
    "url": URL,
    "license": "Open data (data.cincinnati-oh.gov, City of Cincinnati)",
    "publisher": "City of Cincinnati (311 Non-Emergency Service Requests)",
    "task": "binary: Cincinnati 311 request closed within 14 days of creation",
    "label": f"date_closed present and date_closed - date_created <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "received hour/dow/month, request type, priority, group, department, division, intake channel, neighbourhood, police district, zip",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "sr_type_desc",
    "priority",
    "group_title",
    "dept_name",
    "dept_division",
    "method_received",
    "neighborhood",
    "police_district",
    "zipcode",
]
FILE = "cincinnati311_2023-07_2025-06.csv"


def fetch(raw: Path) -> None:
    where = f"date_created >= '{WINDOW[0]}' AND date_created < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "date_created", "$limit": 1_500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    day = pd.to_datetime(d["date_created"], errors="coerce").dt.normalize()
    tm = pd.to_datetime(d["time_received"], format="%I:%M %p", errors="coerce")
    secs = tm.dt.hour.fillna(0) * 3600 + tm.dt.minute.fillna(0) * 60
    ts = day + pd.to_timedelta(secs, unit="s")
    closed = pd.to_datetime(d["date_closed"], errors="coerce")
    y = ((closed - day) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": tm.dt.hour.fillna(-1),
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
        }
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"])
