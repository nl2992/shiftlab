"""US DOT BTS On-Time Reporting Carrier On-Time Performance (transtats.bts.gov PREZIP): arrival delay >= 15 min or cancelled/diverted.

Label rationale (fixed before building, from BTS documentation/domain knowledge): BTS defines a
delayed arrival as ArrDelay >= 15 minutes (ArrDel15); cancelled and diverted flights never arrive
on time. Label = 1 iff ArrDel15 == 1 or Cancelled == 1 or Diverted == 1. The US-wide rate of
such flights is roughly 0.2-0.3. Event = scheduled departure (FlightDate + CRSDepTime, local
time), ordered chronologically. Window = two consecutive months of monthly PREZIP files
(May and June 2025). Features known at schedule time only: reporting airline, origin, dest,
scheduled departure hour, day of week, month, distance, CRS elapsed time. Excluded: every actual
time, delay, taxi, wheels, cancellation-code and delay-cause field. The zip holds one CSV plus a readme.html (ignored, never opened); only the needed columns of that CSV are parsed.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

BASE = "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{y}_{m}.zip"
MONTHS = [(2025, 5), (2025, 6)]
WINDOW = ("2025-05-01T00:00:00", "2025-07-01T00:00:00")
META = {
    "name": "bts_ontime",
    "url": BASE,
    "license": "US Government work, public domain (US DOT Bureau of Transportation Statistics)",
    "publisher": "US DOT Bureau of Transportation Statistics (TranStats On-Time Performance)",
    "task": "binary: flight arrives >=15 min late or is cancelled/diverted",
    "label": "ArrDel15 == 1 or Cancelled == 1 or Diverted == 1",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "carrier, origin, dest, scheduled dep hour, dow, month, distance, CRS elapsed time; no actual times/delays",
}
NUM = ["hour", "dow", "month", "distance", "crs_elapsed"]
CAT = ["carrier", "origin", "dest"]
USECOLS = [
    "FlightDate",
    "Reporting_Airline",
    "Origin",
    "Dest",
    "CRSDepTime",
    "CRSElapsedTime",
    "Distance",
    "ArrDel15",
    "Cancelled",
    "Diverted",
]


def _file(y: int, m: int) -> str:
    return f"bts_ontime_{y}_{m}.zip"


def fetch(raw: Path) -> None:
    for y, m in MONTHS:
        download(BASE.format(y=y, m=m), {}, raw / _file(y, m))


def load(raw: Path) -> pd.DataFrame:
    parts = []
    for y, m in MONTHS:
        with zipfile.ZipFile(raw / _file(y, m)) as z:
            names = [i.filename for i in z.infolist() if not i.is_dir()]
            csvs = [n for n in names if n.lower().endswith(".csv")]
            others = [n for n in names if n not in csvs and not n.lower().endswith(".html")]
            if len(csvs) != 1 or others:  # the zip also ships a readme.html, never opened
                raise ValueError(f"unexpected zip contents: {names}")
            with z.open(csvs[0]) as f:
                parts.append(pd.read_csv(f, usecols=USECOLS, low_memory=False))
    d = pd.concat(parts, ignore_index=True)
    dep = pd.to_numeric(d["CRSDepTime"], errors="coerce")
    dep = dep.where(dep < 2400, 0)  # 2400 means midnight
    hh = (dep // 100).fillna(0)
    mm = (dep % 100).fillna(0)
    ts = pd.to_datetime(d["FlightDate"], errors="coerce") + pd.to_timedelta(hh * 60 + mm, unit="m")
    y = (
        (d["ArrDel15"].fillna(0) == 1)
        | (d["Cancelled"].fillna(0) == 1)
        | (d["Diverted"].fillna(0) == 1)
    ).astype(int)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": hh,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "distance": pd.to_numeric(d["Distance"], errors="coerce"),
            "crs_elapsed": pd.to_numeric(d["CRSElapsedTime"], errors="coerce"),
            "carrier": d["Reporting_Airline"],
            "origin": d["Origin"],
            "dest": d["Dest"],
        }
    )
    return out.dropna(subset=["ts"]).sort_values("ts", kind="stable").reset_index(drop=True)
