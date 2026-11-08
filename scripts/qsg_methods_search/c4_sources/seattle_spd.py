"""Seattle Police Department Call Data (data.seattle.gov, dataset 33kz-ixgy): officer arrived.

Label (chosen from dataset documentation, before any download): y = 1 if the CAD event has an
arrival timestamp (cad_event_arrived_time not null; "the timestamp when the first Call Sign
arrives at the scene"), else 0. Calls for service range from emergencies to information-only,
duplicate, alarm and phone-resolved events, so a large share of events close with no officer
arrival; domain expectation is a substantial minority-to-majority split, base rate within
[0.2, 0.8]. Only the arrival field is used for the label.

Leakage control: dispatch_precinct/sector/beat/neighborhood/reporting_area describe where an
officer *was dispatched*, which is only populated after dispatch, so they are NOT used. Features
are fields known when the call is queued/classified: queued-time hour/day-of-week/month, call
type (reception method), initial call type, priority (CAD-assigned).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

URL = "https://data.seattle.gov/resource/33kz-ixgy.csv"
COLS = "cad_event_original_time_queued,cad_event_arrived_time,call_type,initial_call_type,priority"
WINDOW = ("2025-10-01T00:00:00", "2026-10-01T00:00:00")
META = {
    "name": "seattle_spd",
    "url": URL,
    "license": "Public Domain (data.seattle.gov, City of Seattle open data)",
    "publisher": "City of Seattle / Seattle Police Department",
    "task": "binary: an officer arrived at the scene of a call for service",
    "label": "cad_event_arrived_time is not null",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "queued-time hour/day-of-week/month, call type, initial call type, priority; "
    "dispatch location fields excluded as post-dispatch (label leakage)",
}
NUM = ["hour", "dow", "month"]
CAT = ["call_type", "initial_call_type", "priority"]
FILE = "calls_2025-10_2026-09.csv"
PAGE = 200_000


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    raw.mkdir(parents=True, exist_ok=True)
    where = (
        f"cad_event_original_time_queued >= '{WINDOW[0]}' AND "
        f"cad_event_original_time_queued < '{WINDOW[1]}'"
    )
    chunks, off, url = [], 0, None
    while True:
        params = {
            "$select": COLS,
            "$where": where,
            "$order": "cad_event_original_time_queued,cad_event_number",
            "$limit": PAGE,
            "$offset": off,
        }
        # cad_event_number is only used for a stable page order
        r = requests.get(URL, params=params, timeout=600)
        r.raise_for_status()
        url = url or r.url
        lines = r.content.splitlines(keepends=True)
        if len(lines) <= 1:
            break
        chunks.append(r.content if not chunks else b"".join(lines[1:]))
        if len(lines) - 1 < PAGE:
            break
        off += PAGE
    data = b"".join(chunks)
    out.write_bytes(data)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": url,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            },
            indent=1,
        )
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["cad_event_original_time_queued"], errors="coerce")
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": d["cad_event_arrived_time"].notna().astype(float),
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "call_type": d["call_type"],
            "initial_call_type": d["initial_call_type"],
            "priority": d["priority"],
        }
    )
    return out.dropna(subset=["ts"])
