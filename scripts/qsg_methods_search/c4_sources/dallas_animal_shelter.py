"""Dallas Animal Services intakes (www.dallasopendata.com txcn-ne83, "FY 2000 - Present"): live release.

Event = intake (intake_date + intake_time). Label rationale (fixed before building, from documentation
and domain knowledge): y = 1 if outcome_type in {ADOPTION, RETURNED TO OWNER, TRANSFER} (live release by
the three standard routes), else 0 (euthanized, died, missing, foster, wildlife, etc.). Rows with no
outcome_type are dropped, decided before download. Expected live-release share 0.4-0.7.
Features known at intake only: animal_type, animal_breed, intake_type, intake_subtype, intake_condition,
reason (intake reason), animal_origin, council_district, census_tract, jurisdiction, intake hour/dow/month.
Excluded: all outcome_* fields, kennel_number/kennel_status (current location), due_out and hold_request
(set by shelter process after intake), chip_status and tag_type (may be updated later), receipt_number,
staff_id, ids, additional_information, month/year (fiscal labels).
Window: intakes 2015-10-01 to 2024-10-01 (FY2016-FY2024); ends > 2 years before the fetch.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://www.dallasopendata.com/resource/txcn-ne83.csv"
COLS = (
    "intake_date,intake_time,animal_type,animal_breed,intake_type,intake_subtype,intake_condition,reason,"
    "animal_origin,council_district,census_tract,jurisdiction,outcome_type"
)
WINDOW = ("2015-10-01", "2024-10-01")
LIVE = {"ADOPTION", "RETURNED TO OWNER", "TRANSFER"}
META = {
    "name": "dallas_animal_shelter",
    "url": URL,
    "license": "Open data (City of Dallas Open Data Portal, Dallas Animal Services)",
    "publisher": "City of Dallas (Dallas Animal Shelter Data Fiscal Year 2000 - Present)",
    "task": "binary: shelter intake ends in live release (adoption, return to owner, transfer)",
    "label": "outcome_type in {ADOPTION, RETURNED TO OWNER, TRANSFER}; rows without outcome_type dropped",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "intake hour/dow/month, animal type, breed, intake type/subtype/condition, reason, origin, council district, census tract, jurisdiction",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "animal_type",
    "animal_breed",
    "intake_type",
    "intake_subtype",
    "intake_condition",
    "reason",
    "animal_origin",
    "council_district",
    "census_tract",
    "jurisdiction",
]
FILE = "dallas_shelter_FY2016_FY2024.csv"


def fetch(raw: Path) -> None:
    where = f"intake_date >= '{WINDOW[0]}' AND intake_date < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "intake_date", "$limit": 1_000_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    d = d[d["outcome_type"].notna()].reset_index(drop=True)
    day = pd.to_datetime(d["intake_date"], errors="coerce").dt.normalize()
    tm = pd.to_timedelta(d["intake_time"].str.slice(0, 8), errors="coerce").fillna(pd.Timedelta(0))
    ts = day + tm
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": d["outcome_type"].isin(LIVE).astype(int),
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
        }
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"])
