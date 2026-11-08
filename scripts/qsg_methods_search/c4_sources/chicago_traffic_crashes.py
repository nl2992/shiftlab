"""Chicago Traffic Crashes - Crashes (data.cityofchicago.org 85ca-t3if): property damage over $1,500.

(The brief's id 85ca-s9k7 does not exist; 85ca-t3if is the official "Traffic Crashes - Crashes" dataset.)
Label rationale (fixed before building, from documentation/domain knowledge): the officer's field
estimate `damage` has three bands ("$500 OR LESS", "$501 - $1,500", "OVER $1,500"); modern vehicles make
the top band common, so a base rate inside [0.2, 0.8] is expected. y = (damage == 'OVER $1,500').
Features are conditions recorded at the scene before the outcome: posted speed limit, control device and
its condition, weather, lighting, first crash type, trafficway type, alignment, surface condition, road
defect, beat, and hour/dow/month of the crash. Excluded: damage (label), crash_type (encodes injury/tow),
all injury counts and most_severe_injury, prim/sec_contributory_cause (determined later), report_type,
date_police_notified, hit_and_run_i, num_units, location/street fields, ids.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.cityofchicago.org/resource/85ca-t3if.csv"
COLS = (
    "crash_date,damage,posted_speed_limit,traffic_control_device,device_condition,weather_condition,"
    "lighting_condition,first_crash_type,trafficway_type,alignment,roadway_surface_cond,road_defect,"
    "beat_of_occurrence"
)
WINDOW = ("2021-01-01T00:00:00", "2023-01-01T00:00:00")
META = {
    "name": "chicago_traffic_crashes",
    "url": URL,
    "license": "Open data (City of Chicago Data Portal terms of use; Chicago Police Department / CDOT)",
    "publisher": "City of Chicago (Traffic Crashes - Crashes)",
    "task": "binary: reported crash with officer-estimated damage over $1,500",
    "label": "damage == 'OVER $1,500'",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "crash hour/dow/month, posted speed limit, control device and condition, weather, "
    "lighting, first crash type, trafficway type, alignment, surface condition, road defect, beat",
}
NUM = ["hour", "dow", "month", "posted_speed_limit"]
CAT = [
    "traffic_control_device",
    "device_condition",
    "weather_condition",
    "lighting_condition",
    "first_crash_type",
    "trafficway_type",
    "alignment",
    "roadway_surface_cond",
    "road_defect",
    "beat_of_occurrence",
]
FILE = "chicago_crashes_2021_2022.csv"


def fetch(raw: Path) -> None:
    where = f"crash_date >= '{WINDOW[0]}' AND crash_date < '{WINDOW[1]}'"
    download(
        URL,
        {"$select": COLS, "$where": where, "$order": "crash_date", "$limit": 1_000_000},
        raw / FILE,
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["crash_date"], errors="coerce")
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": (d["damage"] == "OVER $1,500").astype(int).where(d["damage"].notna()),
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "posted_speed_limit": pd.to_numeric(d["posted_speed_limit"], errors="coerce"),
        }
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts", "y"])
