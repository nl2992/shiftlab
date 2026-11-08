"""Austin Animal Center Outcomes (data.austintexas.gov, dataset 9t4d-g238): was the animal adopted."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

URL = "https://data.austintexas.gov/resource/9t4d-g238.csv"
COLS = "datetime,outcome_type,animal_type,sex_upon_outcome,age_upon_outcome,breed,color"
WINDOW = ("2013-10-01T00:00:00", "2025-06-01T00:00:00")  # full published history
META = {
    "name": "austin_animal",
    "url": URL,
    "license": "City of Austin open data portal terms (public, open data)",
    "publisher": "City of Austin / Austin Animal Center",
    "task": "binary: animal outcome is an adoption",
    "label": "outcome_type == 'Adoption' (expected base rate ~0.35-0.45 from public reporting)",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "none (full history < c4_build.N_MAX)",
    "features_note": "outcome hour/dow/month (hour is 0 for date-only early records; within-day order "
    "arbitrary), animal type, sex upon outcome (includes neutered/spayed state at outcome), age at "
    "outcome in days, primary breed, primary colour. outcome_type/outcome_subtype excluded.",
}
NUM = ["hour", "dow", "month", "age_days"]
CAT = ["animal_type", "sex_upon_outcome", "breed", "color"]
FILE = "outcomes_full.csv"
_UNIT = {"day": 1, "week": 7, "month": 30.4375, "year": 365.25}


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    where = f"datetime >= '{WINDOW[0]}' AND datetime < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$order": "datetime", "$limit": 1_000_000}
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


def _age_days(s: pd.Series) -> pd.Series:
    p = s.str.extract(r"^\s*(-?\d+)\s+(day|week|month|year)s?\s*$")
    return pd.to_numeric(p[0]) * p[1].map(_UNIT)


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["datetime"].str.slice(0, 19), errors="coerce")
    age = _age_days(d["age_upon_outcome"])
    breed = d["breed"].str.replace(r"\s+Mix$", "", regex=True).str.split("/").str[0].str.strip()
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": (d["outcome_type"] == "Adoption").astype(int).where(d["outcome_type"].notna()),
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "age_days": age.where(age >= 0),
            "animal_type": d["animal_type"],
            "sex_upon_outcome": d["sex_upon_outcome"],
            "breed": breed,
            "color": d["color"].str.split("/").str[0].str.strip(),
        }
    )
    return out.dropna(subset=["ts", "y"])
