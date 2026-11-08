"""San Francisco 311 Cases (DataSF, data.sfgov.org, vw6y-z8j6): closed within 3 days of opening.

Label rationale (fixed before building, from documentation/domain knowledge): most SF311 cases
(graffiti, street/sidewalk cleaning, abandoned vehicles, parking) are routine and closed within
days, while a substantial tail (infrastructure, long-running work orders) stays open longer; a
72-hour threshold is expected to give a base rate in the middle of [0.2, 0.8]. Still-open and
closed-later cases are 0. The window ends months before the fetch so open status is settled.
status/closed_date/updated/notes fields are used only for the label, never as features.
agency_responsible is excluded: documentation does not say it is fixed at opening (it may be
re-routed later).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

URL = "https://data.sfgov.org/resource/vw6y-z8j6.csv"
COLS = (
    "requested_datetime,closed_date,service_name,service_subtype,source,"
    "supervisor_district,analysis_neighborhood"
)
WINDOW = ("2024-07-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 3
META = {
    "name": "sf_311",
    "url": URL,
    "license": "Open Data Commons Public Domain Dedication and License (PDDL 1.0), DataSF",
    "publisher": "City and County of San Francisco (DataSF / SF311)",
    "task": "binary: 311 case closed within 3 days of being opened",
    "label": f"closed_date present and closed_date - requested_datetime <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "request hour/dow/month, service name and subtype, intake source, "
    "supervisor district, analysis neighbourhood: all recorded at case opening",
}
NUM = ["hour", "dow", "month"]
CAT = ["service_name", "service_subtype", "source", "supervisor_district", "analysis_neighborhood"]
FILE = "sf311_2024-07_2025-06.csv"


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    where = f"requested_datetime >= '{WINDOW[0]}' AND requested_datetime < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$order": "requested_datetime", "$limit": 1_500_000}
    r = requests.get(URL, params=params, timeout=1800)
    r.raise_for_status()
    out.write_bytes(r.content)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": r.url,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": len(r.content),
                "sha256": hashlib.sha256(r.content).hexdigest(),
            },
            indent=1,
        )
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["requested_datetime"], errors="coerce")
    closed = pd.to_datetime(d["closed_date"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> False -> 0
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "service_name": d["service_name"],
            "service_subtype": d["service_subtype"],
            "source": d["source"],
            "supervisor_district": d["supervisor_district"],
            "analysis_neighborhood": d["analysis_neighborhood"],
        }
    )
    return out.dropna(subset=["ts"])
