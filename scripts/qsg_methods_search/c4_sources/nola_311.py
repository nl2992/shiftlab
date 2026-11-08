"""New Orleans 311 OPCD Calls (City of New Orleans, data.nola.gov 2jgv-pqrq): closed within 7 days.

Label rationale (fixed before building, from documentation/domain knowledge): New Orleans 311
mixes quick sanitation/information/drainage cases with slower public-works, blight and
permitting work; a one-week threshold is expected to give a base rate inside [0.3, 0.7].
Still-open cases (no case_close_date) are 0; closed within 7 days of creation is 1. The window
ends 16 months before the fetch. request_status, status, date_modified, case_close_date,
contractor and contractor_action are never features. responsible_agency is the agency the request
type routes to at intake and is included. Features: request type/reason, agency, council district
(address_councildis), created time parts.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.nola.gov/resource/2jgv-pqrq.csv"
COLS = (
    "date_created,case_close_date,request_type,request_reason,responsible_agency,address_councildis"
)
WINDOW = ("2023-01-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 7
META = {
    "name": "nola_311",
    "url": URL,
    "license": "Open data (data.nola.gov, City of New Orleans)",
    "publisher": "City of New Orleans (311 / OPCD)",
    "task": "binary: New Orleans 311 case closed within 7 days of creation",
    "label": f"case_close_date present and case_close_date - date_created <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "created hour/dow/month, request type, request reason, responsible agency, council district",
}
NUM = ["hour", "dow", "month"]
CAT = ["request_type", "request_reason", "responsible_agency", "address_councildis"]
FILE = "nola311_2023-01_2025-06.csv"


def fetch(raw: Path) -> None:
    where = f"date_created >= '{WINDOW[0]}' AND date_created < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "date_created", "$limit": 1_500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["date_created"], errors="coerce")
    closed = pd.to_datetime(d["case_close_date"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"])
