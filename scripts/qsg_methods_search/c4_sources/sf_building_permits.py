"""San Francisco Building Permits (SF Dept. of Building Inspection, data.sfgov.org i98e-djp9): issued within 30 days of filing.

Label rationale (fixed before building, from domain knowledge): many SF permits (over-the-counter
trade permits) issue within days, while plan-review permits take months or are never issued, so a
30-day threshold is expected to give a mixed base rate inside [0.3, 0.8]. Event = filed_date
(date-only; ties ordered by record_id). Label = 1 iff issued_date is present and
issued_date - filed_date <= 30 days; no issued_date is 0. The window ends > 12 months before the
fetch so that nearly all 30-day outcomes are observed. Features are those known at filing:
permit type, neighbourhood, zip, supervisor district, proposed/existing use, proposed stories,
log estimated cost, plansets, submission method, and filing dow/month. Excluded: status,
status_date, issued/approved/completed/first_construction_document/permit_creation dates,
revised_cost (set later), last_permit_activity_date, priority fields, description text.
Window 2015-01-01 to 2025-07-01.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.sfgov.org/resource/i98e-djp9.csv"
COLS = (
    "record_id,filed_date,issued_date,permit_type_definition,neighborhoods_analysis_boundaries,"
    "zipcode,supervisor_district,proposed_use,existing_use,number_of_proposed_stories,"
    "estimated_cost,plansets,application_submission_method"
)
WINDOW = ("2015-01-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 30
META = {
    "name": "sf_building_permits",
    "url": URL,
    "license": "Open Data Commons Public Domain Dedication and License (DataSF)",
    "publisher": "City and County of San Francisco, Dept. of Building Inspection (via DataSF)",
    "task": "binary: building permit issued within 30 days of filing",
    "label": f"issued_date present and issued_date - filed_date <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "permit type, neighbourhood, zip, district, proposed/existing use, stories, log cost, plansets, submission method, filing dow/month",
}
NUM = ["dow", "month", "stories", "log_cost", "plansets"]
CAT = [
    "permit_type_definition",
    "neighborhoods_analysis_boundaries",
    "zipcode",
    "supervisor_district",
    "proposed_use",
    "existing_use",
    "application_submission_method",
]
FILE = "sf_permits_2015-01_2025-06.csv"


def fetch(raw: Path) -> None:
    where = f"filed_date >= '{WINDOW[0]}' AND filed_date < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "filed_date,record_id", "$limit": 1_500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    d["_day"] = pd.to_datetime(d["filed_date"], errors="coerce").dt.normalize()
    d = (
        d.dropna(subset=["_day"])
        .sort_values(["_day", "record_id"], kind="stable")
        .reset_index(drop=True)
    )
    ts = d["_day"] + pd.to_timedelta(d.groupby("_day").cumcount().clip(upper=86399), unit="s")
    issued = pd.to_datetime(d["issued_date"], errors="coerce")
    y = ((issued - d["_day"]) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    cost = pd.to_numeric(d["estimated_cost"], errors="coerce").clip(lower=0)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "stories": pd.to_numeric(d["number_of_proposed_stories"], errors="coerce"),
            "log_cost": np.log1p(cost),
            "plansets": pd.to_numeric(d["plansets"], errors="coerce"),
        }
    )
    for c in CAT:
        out[c] = d[c]
    return out
