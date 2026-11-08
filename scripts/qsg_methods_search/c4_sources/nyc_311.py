"""NYC 311 Service Requests (NYC Open Data erm2-nwe9; NYC 311 / OTI, formerly DoITT).

Label rationale (fixed from documentation before any download): the 7-day closure rate is
expected to be high (most 311 requests, notably NYPD and DSNY ones, are closed within hours or
days), so the threshold is tightened to 1 day: y = closed_date - created_date <= 1 day (open
requests count as 0). Expected rate roughly 0.4-0.6.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:  # pragma: no cover
    from c4_sources._dl_nyc import download

URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
COLS = (
    "created_date,closed_date,complaint_type,agency,borough,location_type,incident_zip,"
    "open_data_channel_type"
)
WINDOW = ("2025-01-01T00:00:00", "2025-04-01T00:00:00")
META = {
    "name": "nyc_311",
    "url": URL,
    "license": "NYC Open Data terms of use (public, open data)",
    "publisher": "City of New York / NYC 311 (Office of Technology and Innovation)",
    "task": "binary: 311 request closed within 1 day of creation",
    "label": "closed_date - created_date <= 1 day (open requests = 0)",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "creation hour/dow/month, complaint type, agency, borough, location type, "
    "zip 3-digit prefix, channel; closed_date/status/resolution used only for the label",
}
NUM = ["hour", "dow", "month"]
CAT = ["complaint_type", "agency", "borough", "location_type", "zip3", "channel"]
FILE = "311_2025-01_2025-03.csv"


def fetch(raw: Path) -> None:
    where = f"created_date >= '{WINDOW[0]}' AND created_date < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$order": "created_date", "$limit": 1_000_000}
    download(URL, params, raw / FILE)


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["created_date"], errors="coerce")
    closed = pd.to_datetime(d["closed_date"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=1)).astype(int)  # NaT -> False -> 0
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "complaint_type": d["complaint_type"],
            "agency": d["agency"],
            "borough": d["borough"],
            "location_type": d["location_type"],
            "zip3": d["incident_zip"].str.slice(0, 3),
            "channel": d["open_data_channel_type"],
        }
    )
    return out.dropna(subset=["ts"])
