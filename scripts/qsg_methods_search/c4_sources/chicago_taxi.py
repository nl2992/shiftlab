"""City of Chicago Taxi Trips 2024- (data.cityofchicago.org, ajtu-isnz): credit-card trip tipped.

Label rationale (fixed before downloading): cash tips are not recorded, so the population is
payment_type == 'Credit Card' only. Documentation gives no tipping rate; public reporting on
Chicago taxi card trips suggests a tipped share well below NYC's, expected inside [0.2, 0.8], so
the plain threshold tips > 0 is used. Features are known at trip start; payment_type is only the
population filter. Fare, tips, miles, seconds, dropoff fields are never features.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

URL = "https://data.cityofchicago.org/resource/ajtu-isnz.csv"
COLS = "trip_start_timestamp,pickup_community_area,company,tips"
WINDOW = ("2024-01-01T00:00:00", "2024-07-01T00:00:00")
META = {
    "name": "chicago_taxi",
    "url": URL,
    "license": "City of Chicago data portal terms of use (public, open data)",
    "publisher": "City of Chicago (Business Affairs and Consumer Protection)",
    "task": "binary: credit-card taxi trip received a tip",
    "label": "payment_type == 'Credit Card'; y = tips > 0",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "trip start hour/dow/month (15-minute rounded), pickup community area, "
    "taxi company: all known at trip start",
}
NUM = ["hour", "dow", "month"]
CAT = ["pickup_community_area", "company"]
FILE = "taxi_cc_2024-01_2024-06.csv"


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    where = (
        f"trip_start_timestamp >= '{WINDOW[0]}' AND trip_start_timestamp < '{WINDOW[1]}' "
        "AND payment_type = 'Credit Card'"
    )
    params = {
        "$select": COLS,
        "$where": where,
        "$order": "trip_start_timestamp",
        "$limit": 1_000_000,
    }
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
    ts = pd.to_datetime(d["trip_start_timestamp"], errors="coerce")
    tips = pd.to_numeric(d["tips"], errors="coerce")
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": (tips > 0).astype(int).where(tips.notna()),
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "pickup_community_area": d["pickup_community_area"],
            "company": d["company"],
        }
    )
    return out.dropna(subset=["ts", "y"])
