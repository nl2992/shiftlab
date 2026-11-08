"""Chicago crimes (City of Chicago data portal, dataset ijzp-q8t2): was an arrest made."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

URL = "https://data.cityofchicago.org/resource/ijzp-q8t2.csv"
COLS = "date,primary_type,location_description,domestic,district,community_area,arrest"
WINDOW = ("2023-10-01T00:00:00", "2025-10-01T00:00:00")
META = {
    "name": "chicago_crimes",
    "url": URL,
    "license": "City of Chicago data portal terms (public, open data)",
    "publisher": "City of Chicago / Chicago Police Department",
    "task": "binary: arrest made for a reported incident",
    "label": "arrest == true",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "occurrence hour/day-of-week/month, primary type, location description, "
    "domestic flag, district, community area: all recorded with the incident report",
}
NUM = ["hour", "dow", "month"]
CAT = ["primary_type", "location_description", "domestic", "district", "community_area"]
FILE = "crimes_2023-10_2025-09.csv"


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    where = f"date >= '{WINDOW[0]}' AND date < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$order": "date", "$limit": 2_000_000}
    r = requests.get(URL, params=params, timeout=600)
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
    ts = pd.to_datetime(d["date"], errors="coerce")
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": d["arrest"].str.lower().map({"true": 1, "false": 0}),
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "primary_type": d["primary_type"],
            "location_description": d["location_description"],
            "domestic": d["domestic"],
            "district": d["district"],
            "community_area": d["community_area"],
        }
    )
    return out.dropna(subset=["ts", "y"])
