"""LAPD crime data 2020-2024 (data.lacity.org, 2nrs-mtv8): was the case cleared (status != 'IC').

The portal's "2020 to Present" dataset (legacy RMS) was frozen after the March 2024 NIBRS transition
and is now titled "Crime Data from 2020 to 2024" (2nrs-mtv8; the id 2nxh-tgd4 no longer exists).
Label rationale (fixed before building): status 'IC' (Invest Cont) is the documented default; LAPD
clearance is roughly 20-25 percent in public reporting, so status != 'IC' (AA, AO, JA, JO, CC) is
expected near the lower edge of the [0.2, 0.8] target. Kept as specified; the gate decides.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests

URL = "https://data.lacity.org/resource/2nrs-mtv8.csv"
COLS = "date_occ,time_occ,area,crm_cd,premis_desc,weapon_used_cd,vict_age,vict_sex,status"
WINDOW = ("2020-01-01T00:00:00", "2025-01-01T00:00:00")  # entire frozen dataset
META = {
    "name": "la_crime",
    "url": URL,
    "license": "Creative Commons CC0 1.0 (public domain dedication), City of Los Angeles open data",
    "publisher": "City of Los Angeles / Los Angeles Police Department",
    "task": "binary: reported crime has a non-default case status (cleared) vs investigation continuing",
    "label": "status != 'IC'",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "occurrence hour/dow/month (date_occ + time_occ), area, crime code, premise, "
    "weapon-recorded flag, victim age (<=0 -> missing) and sex. status/status_desc used only for the "
    "label. Within-day order of rows with equal timestamps is the portal's order.",
}
NUM = ["hour", "dow", "month", "vict_age"]
CAT = ["area", "crm_cd", "premis_desc", "weapon_flag", "vict_sex"]
FILE = "crime_2020_2024.csv"


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    where = f"date_occ >= '{WINDOW[0]}' AND date_occ < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$order": "date_occ, time_occ", "$limit": 3_000_000}
    r = requests.get(URL, params=params, timeout=1200)
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
    t = d["time_occ"].str.zfill(4)
    ts = pd.to_datetime(
        d["date_occ"].str.slice(0, 10) + " " + t.str.slice(0, 2) + ":" + t.str.slice(2, 4),
        errors="coerce",
    )
    age = pd.to_numeric(d["vict_age"], errors="coerce")
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": (d["status"] != "IC").astype(int).where(d["status"].notna()),
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "vict_age": age.where(age > 0),
            "area": d["area"],
            "crm_cd": d["crm_cd"],
            "premis_desc": d["premis_desc"],
            "weapon_flag": np.where(d["weapon_used_cd"].notna(), "1", "0"),
            "vict_sex": d["vict_sex"],
        }
    )
    return out.dropna(subset=["ts", "y"])
