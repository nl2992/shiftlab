"""Montgomery County, MD Traffic Violations (data.montgomerycountymd.gov 4mse-ku6q): Citation vs other.

Label rationale (fixed before building, from domain knowledge/documentation): every electronic
violation record has violation_type in {Warning, Citation, SERO, ESERO}; Montgomery County
police issue roughly as many warnings as citations, so P(Citation) is expected near 0.4-0.6.
Label = 1 iff violation_type == 'Citation'.
Features: only what is observable at the stop: time, sub-agency (district), violation description
(text, high cardinality), vehicle type/year/make/model/colour, vehicle registration state, and the
stop condition flags accident/belts/personal_injury/property_damage/fatal/commercial_license/
hazmat/commercial_vehicle/alcohol/work_zone. Excluded: violation_type (label), charge/article
(encode the legal basis chosen with the outcome), contributed_to_accident, arrest_type, any
search fields, and demographic fields (race, gender, driver city/state, dl_state) and location
coordinates. Window 2024-07-01 to 2026-07-01 (recent contiguous, ~200k records).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.montgomerycountymd.gov/resource/4mse-ku6q.csv"
FLAGS = [
    "accident",
    "belts",
    "personal_injury",
    "property_damage",
    "fatal",
    "commercial_license",
    "hazmat",
    "commercial_vehicle",
    "alcohol",
    "work_zone",
]
COLS = (
    "date_of_stop,time_of_stop,subagency,description,state,vehicle_type,year,make,model,color,"
    "violation_type," + ",".join(FLAGS)
)
WINDOW = ("2024-07-01T00:00:00", "2026-07-01T00:00:00")
META = {
    "name": "montgomery_traffic",
    "url": URL,
    "license": "Open data, Montgomery County Maryland (dataMontgomery)",
    "publisher": "Montgomery County, Maryland (Department of Police / dataMontgomery)",
    "task": "binary: traffic violation resulted in a Citation (vs warning/other)",
    "label": "violation_type == 'Citation'",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "stop hour/dow/month, sub-agency, violation description, vehicle "
    "type/year/make/model/colour/state, stop condition flags; demographics, search, "
    "charge/article, arrest type excluded",
}
NUM = ["hour", "dow", "month", "vehicle_year"]
CAT = ["subagency", "description", "state", "vehicle_type", "make", "model", "color"] + FLAGS
FILE = "montgomery_traffic_2024-07_2026-06.csv"


def fetch(raw: Path) -> None:
    where = f"date_of_stop >= '{WINDOW[0]}' AND date_of_stop < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "date_of_stop", "$limit": 1_500_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    day = pd.to_datetime(d["date_of_stop"], errors="coerce")
    t = pd.to_timedelta(d["time_of_stop"], errors="coerce")
    ts = day + t
    y = (d["violation_type"] == "Citation").astype(int)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "vehicle_year": pd.to_numeric(d["year"], errors="coerce"),
        }
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"])
