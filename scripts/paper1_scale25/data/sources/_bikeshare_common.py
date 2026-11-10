"""Shared factory for Lyft-operated bikeshare trip archives (Divvy, Capital Bikeshare, Bluebikes).

Task: binary, rider is a subscriber ("member") rather than a casual rider. Known at unlock: bike type,
start station/location and start time. End time, end station and duration are never features.
Window (protocol rule for archive-vintage sources): DEV = the 12 monthly archives 2024-07..2025-06
(the last 12 months of [2023-07-01, 2025-07-01) because the system carries more than 400k trips per
year); CONFIRM = 2025-07..2026-06. Deterministic thinning: every K-th row in file order per month with
K = ceil(n_month / 70000), then the builder subsamples to 400k.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

MONTHS = [f"{y}{m:02d}" for y, m in [(2024, m) for m in range(7, 13)] + [(2025, m) for m in range(1, 7)]]
PER_MONTH = 70_000
WINDOW = ("2024-07-01T00:00:00", "2025-07-01T00:00:00")


def make_module(name, publisher, url_tmpl, lic, page) -> dict:
    META = {
        "name": name,
        "url": url_tmpl.format(m="YYYYMM"),
        "license": lic,
        "publisher": publisher,
        "task": "binary: trip taken by a subscribed member (not a casual rider)",
        "label": "member_casual == 'member'",
        "delay": 100,
        "window": WINDOW,
        "subsample_rule": f"load(): every K-th row per month, K=ceil(n/{PER_MONTH}); then c4_build.N_MAX systematic",
        "features_note": "rideable_type, start station id, start lat/lng (3 dp), start hour/dow/month: known at unlock; "
        "end time/station/duration unused; member_casual is the label",
    }
    NUM = ["hour", "dow", "month", "lat", "lng"]
    CAT = ["rideable_type", "start_station_id"]

    def fetch(raw: Path) -> None:
        for m in MONTHS:
            out = raw / f"{m}.zip"
            if out.exists():
                continue
            r = requests.get(url_tmpl.format(m=m), timeout=(20, 900))
            r.raise_for_status()
            out.write_bytes(r.content)
            (raw / f"{m}.zip.receipt.json").write_text(
                json.dumps(
                    {
                        "url": url_tmpl.format(m=m),
                        "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                        "bytes": len(r.content),
                        "sha256": hashlib.sha256(r.content).hexdigest(),
                    },
                    indent=1,
                )
            )

    def load(raw: Path) -> pd.DataFrame:
        frames = []
        for m in MONTHS:
            z = zipfile.ZipFile(raw / f"{m}.zip")
            f = next(i for i in z.infolist() if i.filename.endswith(".csv") and not i.filename.startswith("__"))
            with z.open(f) as fh:
                d = pd.read_csv(
                    io.TextIOWrapper(fh, encoding="utf-8"),
                    usecols=["rideable_type", "started_at", "start_station_id", "start_lat", "start_lng", "member_casual"],
                    dtype={"start_station_id": str, "rideable_type": str, "member_casual": str},
                )
            k = max(1, math.ceil(len(d) / PER_MONTH))
            frames.append(d.iloc[::k])
        d = pd.concat(frames, ignore_index=True)
        ts = pd.to_datetime(d["started_at"], errors="coerce")
        y = d["member_casual"].map({"member": 1, "casual": 0})
        o = pd.DataFrame(
            {
                "ts": ts,
                "y": y,
                "hour": ts.dt.hour,
                "dow": ts.dt.dayofweek,
                "month": ts.dt.month,
                "lat": pd.to_numeric(d["start_lat"], errors="coerce").round(3),
                "lng": pd.to_numeric(d["start_lng"], errors="coerce").round(3),
                "rideable_type": d["rideable_type"],
                "start_station_id": d["start_station_id"],
            }
        )
        o = o.dropna(subset=["ts", "y"])
        return o[(o["ts"] >= WINDOW[0]) & (o["ts"] < WINDOW[1])]

    return {"META": META, "NUM": NUM, "CAT": CAT, "WINDOW": WINDOW, "fetch": fetch, "load": load}
