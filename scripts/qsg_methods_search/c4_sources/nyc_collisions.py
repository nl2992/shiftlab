"""NYC Motor Vehicle Collisions - Crashes (NYC Open Data h9gi-nx95; NYPD).

Label (fixed from documentation before download): any person injured or killed in the crash;
public reporting puts this near 25-35 percent of police-reported crashes.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:  # pragma: no cover
    from c4_sources._dl_nyc import download

URL = "https://data.cityofnewyork.us/resource/h9gi-nx95.csv"
VEH = [
    "vehicle_type_code1",
    "vehicle_type_code2",
    "vehicle_type_code_3",
    "vehicle_type_code_4",
    "vehicle_type_code_5",
]
COLS = ",".join(
    [
        "crash_date",
        "crash_time",
        "borough",
        "contributing_factor_vehicle_1",
        "number_of_persons_injured",
        "number_of_persons_killed",
    ]
    + VEH
)
WINDOW = ("2022-01-01T00:00:00", "2025-10-01T00:00:00")
META = {
    "name": "nyc_collisions",
    "url": URL,
    "license": "NYC Open Data terms of use (public, open data)",
    "publisher": "City of New York / NYPD",
    "task": "binary: police-reported crash with at least one person injured or killed",
    "label": "number_of_persons_injured + number_of_persons_killed > 0",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "crash hour/dow/month, borough, contributing factor vehicle 1, vehicle type "
    "code 1, number of vehicles (non-null vehicle type codes); injured/killed counts used only "
    "for the label",
}
NUM = ["hour", "dow", "month", "n_vehicles"]
CAT = ["borough", "factor1", "vehicle_type1"]
FILE = "collisions_2022-01_2025-09.csv"


def fetch(raw: Path) -> None:
    where = f"crash_date >= '{WINDOW[0]}' AND crash_date < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$order": "crash_date", "$limit": 1_000_000}
    download(URL, params, raw / FILE)


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    t = d["crash_time"].fillna("0:00")
    ts = pd.to_datetime(d["crash_date"].str.slice(0, 10) + " " + t, errors="coerce")
    inj = pd.to_numeric(d["number_of_persons_injured"], errors="coerce")
    kil = pd.to_numeric(d["number_of_persons_killed"], errors="coerce")
    y = ((inj + kil) > 0).astype(float).where(inj.notna() & kil.notna())
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "n_vehicles": d[VEH].notna().sum(axis=1),
            "borough": d["borough"],
            "factor1": d["contributing_factor_vehicle_1"],
            "vehicle_type1": d["vehicle_type_code1"],
        }
    )
    return out.dropna(subset=["ts", "y"])
