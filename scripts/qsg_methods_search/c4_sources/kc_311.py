"""Kansas City 311 Call Center Reported Issues (MyKCMO, data.kcmo.org d4px-6rwg): resolved within 7 days.

Label rationale (fixed before building, from documentation/domain knowledge): the dataset
documents days_to_close (days between opening and closing, rounded down). KC 311 mixes quick
administrative/service requests with slower public-works work orders (potholes took weeks in the
documented examples); a 7-day (one-week) threshold is expected to give a base rate inside
[0.2, 0.8]. Still-open issues (no resolved_date) are 0; any issue with a resolved_date within
7 days (including canceled) is 1. The window ends over a year before the fetch so status has
settled. current_status, resolved_date, days_to_close, last_updated, workorder_ are never
features. department_work_group is documented as the work group assigned *by default* to the
issue type/subtype, i.e. determined at intake from the type, so it is included.
additional_questions is excluded (free text). zip_region is the trailing 5-digit zip of the reported
incident_address (the computed-region columns are not selectable via SoQL).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.kcmo.org/resource/d4px-6rwg.csv"
COLS = (
    "open_date_time,resolved_date,report_source,source_category,issue_type,issue_sub_type,"
    "department_work_group,council_district,incident_address"
)
WINDOW = ("2023-07-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 7
META = {
    "name": "kc_311",
    "url": URL,
    "license": "Public Domain (data.kcmo.org, City of Kansas City, Missouri)",
    "publisher": "City of Kansas City, Missouri (311 Call Center / MyKCMO)",
    "task": "binary: 311 issue resolved within 7 days of being reported",
    "label": f"resolved_date present and resolved_date - open_date_time <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "open hour/dow/month, report source and source category, issue type and "
    "sub-type, default department work group, council district, zip parsed from reported address",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "report_source",
    "source_category",
    "issue_type",
    "issue_sub_type",
    "department_work_group",
    "council_district",
    "zip_region",
]
FILE = "kc311_2023-07_2025-06.csv"


def fetch(raw: Path) -> None:
    where = f"open_date_time >= '{WINDOW[0]}' AND open_date_time < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "open_date_time", "$limit": 1_500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["open_date_time"], errors="coerce")
    closed = pd.to_datetime(d["resolved_date"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
    )
    for c in CAT[:-1]:
        out[c] = d[c]
    out["zip_region"] = d["incident_address"].str.extract(r"(\d{5})\s*$")[0]
    return out.dropna(subset=["ts"])
