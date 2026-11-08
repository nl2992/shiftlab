"""Seattle Building Permits (Seattle SDCI, data.seattle.gov 76t5-zqzr): issued within 60 days of application.

Label rationale (fixed before building, from domain knowledge): SDCI permits range from
over-the-counter/express review to multi-cycle plan review taking many months; a 60-day threshold
is expected to give a mixed base rate inside [0.3, 0.8]. Event = applieddate (date-only; ties
ordered by permitnum). Label = 1 iff issueddate present and issueddate - applieddate <= 60 days;
no issueddate is 0. The window ends > 12 months before the fetch. Features known at application:
permit class/type fields, declared housing units (existing/removed/added), estimated project
cost (log), zip, zoning, dwelling unit type, housing category, standard plan flag, dependent
building flag, related-MUP flag, and application dow/month. Excluded: statuscurrent,
issued/expires/completed dates, all plan-review timing and cycle-count fields, ready-to-issue
date, contractor name, free-text description, address/coordinates.
Window 2016-01-01 to 2025-07-01.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.seattle.gov/resource/76t5-zqzr.csv"
COLS = (
    "permitnum,applieddate,issueddate,permitclass,permitclassmapped,permittypemapped,"
    "permittypedesc,housingunits,housingunitsremoved,housingunitsadded,estprojectcost,"
    "originalzip,zoning,dwellingunittype,housingcategory,standardplan,dependentbuilding,relatedmup"
)
WINDOW = ("2016-01-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 60
META = {
    "name": "seattle_building_permits",
    "url": URL,
    "license": "Public Domain (City of Seattle open data)",
    "publisher": "City of Seattle, Seattle Department of Construction and Inspections",
    "task": "binary: building permit issued within 60 days of application",
    "label": f"issueddate present and issueddate - applieddate <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "permit class/type, housing units, log cost, zip, zoning, dwelling unit type, housing category, flags, application dow/month",
}
NUM = ["dow", "month", "housingunits", "housingunitsremoved", "housingunitsadded", "log_cost"]
CAT = [
    "permitclass",
    "permitclassmapped",
    "permittypemapped",
    "permittypedesc",
    "originalzip",
    "zoning",
    "dwellingunittype",
    "housingcategory",
    "standardplan",
    "dependentbuilding",
    "relatedmup_present",
]
FILE = "seattle_permits_2016-01_2025-06.csv"


def fetch(raw: Path) -> None:
    where = f"applieddate >= '{WINDOW[0]}' AND applieddate < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "applieddate,permitnum", "$limit": 1_500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    d["_day"] = pd.to_datetime(d["applieddate"], errors="coerce").dt.normalize()
    d = (
        d.dropna(subset=["_day"])
        .sort_values(["_day", "permitnum"], kind="stable")
        .reset_index(drop=True)
    )
    ts = d["_day"] + pd.to_timedelta(d.groupby("_day").cumcount().clip(upper=86399), unit="s")
    issued = pd.to_datetime(d["issueddate"], errors="coerce")
    y = ((issued - d["_day"]) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    cost = pd.to_numeric(d["estprojectcost"], errors="coerce").clip(lower=0)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "housingunits": pd.to_numeric(d["housingunits"], errors="coerce"),
            "housingunitsremoved": pd.to_numeric(d["housingunitsremoved"], errors="coerce"),
            "housingunitsadded": pd.to_numeric(d["housingunitsadded"], errors="coerce"),
            "log_cost": np.log1p(cost),
        }
    )
    for c in CAT:
        if c == "relatedmup_present":
            out[c] = d["relatedmup"].notna().astype(str)
        else:
            out[c] = d[c]
    return out
