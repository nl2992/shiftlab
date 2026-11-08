"""DOHMH New York City Restaurant Inspection Results (NYC Open Data 43nn-pn8j; NYC DOHMH).

Label (fixed from documentation before download): the inspection score falls in the Grade A
range (score <= 13; lower is better). Grade itself is blank on many inspections (assigned only
after re-inspection or grading rules), so the documented A threshold on the score is used.
Inspections recorded as "No violations were recorded" with a blank score count as score 0.
Other blank-score rows are dropped. Expected rate roughly 0.4-0.7 over all inspection types.
One row per (camis, inspection_date, inspection_type); event time = inspection_date (midnight).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:  # pragma: no cover
    from c4_sources._dl_nyc import download

URL = "https://data.cityofnewyork.us/resource/43nn-pn8j.csv"
COLS = "camis,inspection_date,inspection_type,cuisine_description,boro,zipcode,score,action"
WINDOW = ("2022-01-01T00:00:00", "2026-10-01T00:00:00")
META = {
    "name": "nyc_restaurant_inspections",
    "url": URL,
    "license": "NYC Open Data terms of use (public, open data)",
    "publisher": "City of New York / DOHMH",
    "task": "binary: inspection score within Grade A range (<= 13)",
    "label": "score <= 13 (blank score with 'No violations were recorded' = 0; other blanks dropped)",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "cuisine, borough, inspection type, zip 3-digit prefix, month/dow, the same "
    "restaurant's previous inspection score (strictly earlier inspection date, within the window); "
    "score/action/grade used only for the label",
}
NUM = ["month", "dow", "prev_score"]
CAT = ["cuisine", "boro", "inspection_type", "zip3"]
FILE = "inspections_2022-01_2026-09.csv"


def fetch(raw: Path) -> None:
    where = f"inspection_date >= '{WINDOW[0]}' AND inspection_date < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$limit": 1_000_000}
    download(URL, params, raw / FILE)


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    d["ts"] = pd.to_datetime(d["inspection_date"], errors="coerce")
    d["score_n"] = pd.to_numeric(d["score"], errors="coerce")
    nov = d["action"].fillna("").str.contains("No violations were recorded", case=False)
    d.loc[d["score_n"].isna() & nov, "score_n"] = 0.0
    d = d.dropna(subset=["ts", "score_n", "camis"])
    d = d.sort_values(["ts", "camis", "inspection_type"], kind="stable")
    d = d.drop_duplicates(["camis", "ts", "inspection_type"], keep="first").reset_index(drop=True)
    # previous score: last score of this restaurant on a strictly earlier date
    day = d.groupby(["camis", "ts"], sort=False)["score_n"].last().reset_index()
    day = day.sort_values(["camis", "ts"], kind="stable")
    day["prev_score"] = day.groupby("camis")["score_n"].shift(1)
    d = d.merge(day[["camis", "ts", "prev_score"]], on=["camis", "ts"], how="left")
    return pd.DataFrame(
        {
            "ts": d["ts"],
            "y": (d["score_n"] <= 13).astype(int),
            "month": d["ts"].dt.month,
            "dow": d["ts"].dt.dayofweek,
            "prev_score": d["prev_score"],
            "cuisine": d["cuisine_description"],
            "boro": d["boro"],
            "inspection_type": d["inspection_type"],
            "zip3": d["zipcode"].str.slice(0, 3),
        }
    )
