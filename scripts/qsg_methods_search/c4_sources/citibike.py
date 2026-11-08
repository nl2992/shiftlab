"""Citi Bike trip histories, April 2026 (official s3 bucket tripdata): trip is on an e-bike.

Label rationale (fixed before downloading): member_casual == 'member' is about 80+ percent of
rides in public Citi Bike reporting (higher in colder months), outside the [0.2, 0.8] target, so
the natural alternative target is rideable_type == 'electric_bike' (e-bikes are a large minority
to majority of rides in public reporting, expected inside [0.2, 0.8]). rideable_type is the label
and so is not a feature. One month only because monthly zips are 160 MB to 1 GB; April 2026 is
the smallest recent month under the 400 MB cap. End time/station/duration are never features.
member_casual and start station are known at unlock.
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

MONTH = "202604"
URL = f"https://s3.amazonaws.com/tripdata/{MONTH}-citibike-tripdata.zip"
WINDOW = ("2026-04-01T00:00:00", "2026-05-01T00:00:00")
MAX_ROWS = 700_000  # keep every K-th row (file order, K = ceil(n / MAX_ROWS)) if more
META = {
    "name": "citibike",
    "url": URL,
    "license": "Citi Bike (Lyft / NYC Bike Share) Data License Agreement, public trip data",
    "publisher": "Citi Bike / Lyft (NYCBS)",
    "task": "binary: trip taken on an electric bike",
    "label": "rideable_type == 'electric_bike'",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": f"load(): every K-th row in file order with K = ceil(n_in_window/{MAX_ROWS}); "
    "then c4_build.N_MAX systematic if above 400k",
    "features_note": "start hour/dow, start station id, start lat/lng, member_casual: all known "
    "at trip start. rideable_type is the label; end time/station/duration not used.",
}
NUM = ["hour", "dow", "start_lat", "start_lng"]
CAT = ["start_station_id", "member_casual"]
FILE = f"{MONTH}-citibike-tripdata.zip"
USE = ["started_at", "rideable_type", "start_station_id", "start_lat", "start_lng", "member_casual"]


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    h = hashlib.sha256()
    n = 0
    tmp = raw / (FILE + ".part")
    with requests.get(URL, stream=True, timeout=1800) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                h.update(chunk)
                n += len(chunk)
        final_url = r.url
    tmp.rename(out)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": final_url,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": n,
                "sha256": h.hexdigest(),
            },
            indent=1,
        )
    )


def _members(z: zipfile.ZipFile) -> list[str]:
    return sorted(
        i.filename
        for i in z.infolist()
        if i.filename.lower().endswith(".csv") and "__MACOSX" not in i.filename
    )


def load(raw: Path) -> pd.DataFrame:
    lo, hi = pd.Timestamp(WINDOW[0]), pd.Timestamp(WINDOW[1])
    parts = []
    with zipfile.ZipFile(raw / FILE) as z:
        for name in _members(z):
            with z.open(name) as fh:
                for ch in pd.read_csv(
                    io.TextIOWrapper(fh, encoding="utf-8"),
                    usecols=USE,
                    dtype=str,
                    chunksize=200_000,
                ):
                    ts = pd.to_datetime(ch["started_at"], errors="coerce")
                    ch = ch[(ts >= lo) & (ts < hi)]
                    parts.append(ch)
    d = pd.concat(parts, ignore_index=True)
    k = max(1, -(-len(d) // MAX_ROWS))
    d = d.iloc[::k].reset_index(drop=True)
    ts = pd.to_datetime(d["started_at"], errors="coerce")
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": (d["rideable_type"] == "electric_bike")
            .astype(int)
            .where(d["rideable_type"].notna()),
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "start_lat": pd.to_numeric(d["start_lat"], errors="coerce"),
            "start_lng": pd.to_numeric(d["start_lng"], errors="coerce"),
            "start_station_id": d["start_station_id"],
            "member_casual": d["member_casual"],
        }
    )
    return out.dropna(subset=["ts", "y"])
