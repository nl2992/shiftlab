"""NOAA GHCN-Daily (NCEI, public domain), US land stations: will it record precipitation tomorrow?

Event = one station-day (station s, date t). Label y = 1 if PRCP(s, t+1) > 0 (any recorded precipitation);
rows with no quality-clean PRCP on t+1 are dropped. Known at day t: PRCP, TMAX, TMIN on t and t-1 (quality
flag empty), station latitude/longitude/elevation/state (static metadata), month. Station subsample (fixed
rule): crc32(station id) % 8 == 0 so full per-station sequences are kept. Label is observable one day later;
META delay = 1000 (about one day of kept station-days) instead of the 100-event default (documented override).

Window (protocol rule): DEV = event dates 2024-07-01 .. 2025-06-30 (last 12 months of the 2023-07..2025-07
span, since the full network carries far more than 400k station-days per year). CONFIRM = 2025-07-01 .. 2026-06-30.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import zlib
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

BASE = "https://www.ncei.noaa.gov/pub/data/ghcn/daily"
YEARS = (2024, 2025)
WINDOW = ("2024-07-01T00:00:00", "2025-07-01T00:00:00")
META = {
    "name": "ghcn_us_rain",
    "url": f"{BASE}/by_year/{{year}}.csv.gz",
    "license": "NOAA NCEI GHCN-Daily: public domain (US Government work)",
    "publisher": "NOAA National Centers for Environmental Information (GHCN-Daily)",
    "task": "binary: any precipitation recorded at the station on the next day",
    "label": "PRCP(station, t+1) > 0, quality-flag clean",
    "delay": 1000,
    "window": WINDOW,
    "subsample_rule": "station subsample crc32(id)%8==0; then c4_build.N_MAX systematic",
    "features_note": "PRCP/TMAX/TMIN at t and t-1, station lat/lon/elevation/state, month",
}
NUM = ["prcp", "tmax", "tmin", "prcp_l1", "tmax_l1", "lat", "lon", "elev", "month"]
CAT = ["state"]


def _get(url, out: Path):
    if out.exists():
        return
    h = hashlib.sha256()
    n = 0
    tmp = out.with_suffix(out.suffix + ".part")
    with requests.get(url, stream=True, timeout=(30, 600)) as r, open(tmp, "wb") as fh:
        r.raise_for_status()
        for ch in r.iter_content(1 << 20):
            fh.write(ch)
            h.update(ch)
            n += len(ch)
    tmp.rename(out)
    (out.parent / f"{out.name}.receipt.json").write_text(
        json.dumps({"url": url, "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"), "bytes": n, "sha256": h.hexdigest()}, indent=1)
    )


def fetch(raw: Path) -> None:
    _get(f"{BASE}/ghcnd-stations.txt", raw / "ghcnd-stations.txt")
    for y in YEARS:
        _get(f"{BASE}/by_year/{y}.csv.gz", raw / f"{y}.csv.gz")


def load(raw: Path) -> pd.DataFrame:
    keep = lambda s: zlib.crc32(s.encode()) % 8 == 0  # noqa: E731
    fr = []
    for y in YEARS:
        with gzip.open(raw / f"{y}.csv.gz", "rt") as fh:
            for ch in pd.read_csv(
                fh, header=None, names=["id", "date", "el", "v", "m", "q", "s", "t"],
                usecols=[0, 1, 2, 3, 5], dtype={"id": str, "date": str, "el": str, "q": str}, chunksize=3_000_000,
            ):
                ch = ch[ch["id"].str.startswith("US") & ch["el"].isin(["PRCP", "TMAX", "TMIN"]) & ch["q"].isna()]
                ch = ch[ch["id"].map(keep)]
                fr.append(ch[["id", "date", "el", "v"]])
    d = pd.concat(fr, ignore_index=True)
    w = d.pivot_table(index=["id", "date"], columns="el", values="v", aggfunc="first").reset_index()
    w["date"] = pd.to_datetime(w["date"], format="%Y%m%d")
    w = w[w["PRCP"].notna()].sort_values(["id", "date"])
    idx = w.set_index(["id", "date"])

    def shift(col, days):
        k = pd.MultiIndex.from_arrays([w["id"], w["date"] + pd.Timedelta(days=days)])
        return idx[col].reindex(k).to_numpy()

    w["prcp_next"] = shift("PRCP", 1)
    w["prcp_l1"] = shift("PRCP", -1)
    w["tmax_l1"] = shift("TMAX", -1)
    w = w[w["prcp_next"].notna() & (w["date"] >= WINDOW[0]) & (w["date"] < WINDOW[1])]
    st = pd.read_fwf(
        raw / "ghcnd-stations.txt", colspecs=[(0, 11), (12, 20), (21, 30), (31, 37), (38, 40)],
        names=["id", "lat", "lon", "elev", "state"], dtype={"id": str, "state": str},
    )
    w = w.merge(st, on="id", how="left")
    o = pd.DataFrame(
        {
            "ts": w["date"], "y": (w["prcp_next"] > 0).astype(int), "prcp": w["PRCP"], "tmax": w.get("TMAX"), "tmin": w.get("TMIN"),
            "prcp_l1": w["prcp_l1"], "tmax_l1": w["tmax_l1"], "lat": w["lat"], "lon": w["lon"], "elev": w["elev"],
            "month": w["date"].dt.month, "state": w["state"],
        }
    )
    return o.sort_values(["ts"], kind="stable").reset_index(drop=True)
