"""Sonoma County Animal Shelter Intake and Outcome (data.sonomacounty.ca.gov 924a-vesw): live release.

Event = intake (intake_date); one row per intake record, so this is an INTAKE stream, not an outcome
stream (cf. the excluded austin_animal). Label rationale (fixed before building, from documentation and
domain knowledge): y = 1 if outcome_type in {ADOPTION, RETURN TO OWNER, TRANSFER} (live release by the
three standard routes), else 0 (euthanasia, died, disposal, other/unknown routes). Shelter live-release
rates are typically 0.5-0.8. Rows with no outcome_type (still in the shelter / unrecorded) are dropped,
decided before download. NOTE: the whole dataset has ~35k rows, below the 140k needed for >= 35
episodes; it is expected to fail the size gate and is reported as such.
Features known at intake only: type, breed, color, size, intake_type, intake_subtype,
intake_condition, intake_jurisdiction, age at intake (intake_date - date_of_birth); intake time of day is
not available (date only), so dow/month only. Excluded: sex (documentation lists neutered/spayed values,
i.e. state that may be changed by the outcome process), kennel_number (current location), outcome_*,
days_in_shelter, zip_code and location (outcome jurisdiction), name, ids.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.sonomacounty.ca.gov/resource/924a-vesw.csv"
COLS = (
    "intake_date,date_of_birth,type,breed,color,size,intake_type,intake_subtype,intake_condition,"
    "intake_jurisdiction,outcome_type"
)
WINDOW = ("2014-01-01T00:00:00", "2025-01-01T00:00:00")
LIVE = {"ADOPTION", "RETURN TO OWNER", "TRANSFER"}
META = {
    "name": "sonoma_animal_shelter",
    "url": URL,
    "license": "Open data (County of Sonoma Department of Health Services, data.sonomacounty.ca.gov)",
    "publisher": "County of Sonoma Department of Health Services (Animal Shelter Intake and Outcome)",
    "task": "binary: shelter intake ends in live release (adoption, return to owner, transfer)",
    "label": "outcome_type in {ADOPTION, RETURN TO OWNER, TRANSFER}; rows without outcome_type dropped",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "intake dow/month, age at intake, type, breed, color, size, intake type/subtype/condition, jurisdiction",
}
NUM = ["dow", "month", "age_days"]
CAT = [
    "type",
    "breed",
    "color",
    "size",
    "intake_type",
    "intake_subtype",
    "intake_condition",
    "intake_jurisdiction",
]
FILE = "sonoma_shelter_2014_2024.csv"


def fetch(raw: Path) -> None:
    where = f"intake_date >= '{WINDOW[0]}' AND intake_date < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "intake_date", "$limit": 500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    d = d[d["outcome_type"].notna()].reset_index(drop=True)
    ts = pd.to_datetime(d["intake_date"], errors="coerce")
    dob = pd.to_datetime(d["date_of_birth"], errors="coerce")
    age = (ts - dob).dt.days.astype(float)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": d["outcome_type"].isin(LIVE).astype(int),
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "age_days": age.where(age >= 0),
        }
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"])
