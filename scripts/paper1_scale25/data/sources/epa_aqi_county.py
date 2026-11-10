"""EPA AirData daily AQI by county (US EPA AQS, public domain): will tomorrow's AQI category be worse than Good?

Event = one county-day (date t, county c). Label y = 1 if the county's AQI on day t+1 exceeds 50 (category
not "Good"); rows with no observation on t+1 are dropped. Known at day t (all recorded by end of day t):
AQI, category, defining pollutant, number of reporting sites on day t, AQI on day t-1 and t-7 for the same
county, state, county code, month, day of week. The label (next-day observation) is published a day later,
so the natural label delay is about one day of events (about 1000 county-days); META delay is 1000 to
respect that, not the 100-event default (documented override).

Window (protocol rule, annual vintages): DEV = event dates 2023-07-01 .. 2025-06-30 (annual zips 2023-2025);
CONFIRM = 2025-07-01 .. 2026-06-30. Metadata count of the DEV window is about 650k county-days (24 months,
<= 800k).
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

URL = "https://aqs.epa.gov/aqsweb/airdata/daily_aqi_by_county_{y}.zip"
YEARS = (2023, 2024, 2025)
WINDOW = ("2023-07-01T00:00:00", "2025-07-01T00:00:00")
META = {
    "name": "epa_aqi_county",
    "url": URL,
    "license": "US EPA AirData: US Government work, public domain",
    "publisher": "US Environmental Protection Agency (AQS AirData daily AQI by county)",
    "task": "binary: next-day AQI category is worse than Good (AQI > 50) for the same county",
    "label": "AQI(county, t+1) > 50; rows without a t+1 observation dropped",
    "delay": 1000,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "AQI, category, defining parameter, sites reporting on day t; AQI at t-1 and t-7; state, county code, month, dow",
}
NUM = ["aqi", "aqi_l1", "aqi_l7", "n_sites", "month", "dow"]
CAT = ["category", "param", "state", "county"]


def fetch(raw: Path) -> None:
    for y in YEARS:
        out = raw / f"daily_aqi_by_county_{y}.zip"
        if out.exists():
            continue
        r = requests.get(URL.format(y=y), timeout=600)
        r.raise_for_status()
        out.write_bytes(r.content)
        (raw / f"{out.name}.receipt.json").write_text(
            json.dumps(
                {
                    "url": URL.format(y=y),
                    "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                    "bytes": len(r.content),
                    "sha256": hashlib.sha256(r.content).hexdigest(),
                },
                indent=1,
            )
        )


def load(raw: Path) -> pd.DataFrame:
    fr = []
    for y in YEARS:
        z = zipfile.ZipFile(raw / f"daily_aqi_by_county_{y}.zip")
        fr.append(pd.read_csv(io.BytesIO(z.read(z.namelist()[0]))))
    d = pd.concat(fr, ignore_index=True)
    d["date"] = pd.to_datetime(d["Date"])
    d["cid"] = d["State Code"].astype(str).str.zfill(2) + d["County Code"].astype(str).str.zfill(3)
    d = d.sort_values(["cid", "date"]).drop_duplicates(["cid", "date"])
    idx = d.set_index(["cid", "date"])["AQI"]

    def shift(days):
        k = pd.MultiIndex.from_arrays([d["cid"], d["date"] + pd.Timedelta(days=days)])
        return idx.reindex(k).to_numpy()

    d["aqi_next"] = shift(1)
    d["aqi_l1"] = shift(-1)
    d["aqi_l7"] = shift(-7)
    d = d[d["aqi_next"].notna() & (d["date"] >= WINDOW[0]) & (d["date"] < WINDOW[1])]
    o = pd.DataFrame(
        {
            "ts": d["date"],
            "y": (d["aqi_next"] > 50).astype(int),
            "aqi": d["AQI"],
            "aqi_l1": d["aqi_l1"],
            "aqi_l7": d["aqi_l7"],
            "n_sites": d["Number of Sites Reporting"],
            "month": d["date"].dt.month,
            "dow": d["date"].dt.dayofweek,
            "category": d["Category"],
            "param": d["Defining Parameter"],
            "state": d["State Name"],
            "county": d["cid"],
        }
    )
    return o.sort_values(["ts", "county"], kind="stable").reset_index(drop=True)
