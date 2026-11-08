"""City of Sacramento 311 service requests (Salesforce311 view, services5.arcgis.com org
54falWtcpty3V47Z, City of Sacramento open data): closed within 7 days of creation.

Label rationale (fixed before downloading, from documentation/domain knowledge): Sacramento 311
mixes solid-waste, illegal-dumping, parks and street-maintenance requests handled by different
departments; routine pickups and quick field fixes close within days while engineering/repair
work orders stay open for weeks, so a 7-day threshold is expected to give a base rate inside
[0.3, 0.7]. Still-open or closed-later = 0. DateClosed carries a 1899 default sentinel for open
tickets; a closure is valid only if DateClosed >= DateCreated (otherwise treated as not closed).
DateClosed/DateUpdated/PublicStatus are used only for the label (status not used at all).
Features are set at intake: category levels 1-2 and category name, council district, incident
source, neighborhood, zip, and creation hour/dow/month (America/Los_Angeles). Window is calendar
2024, fetched ~22 months later, rows streamed to disk in 2000-row pages (never held in memory).
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime

import pandas as pd
import requests

BASE = "https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/SalesForce311_View/FeatureServer/0/query"
FIELDS = [
    "CategoryLevel1",
    "CategoryLevel2",
    "CategoryName",
    "CouncilDistrictNumber",
    "SourceLevel1",
    "Neighborhood",
    "ZIP",
    "DateCreated",
    "DateClosed",
]
WINDOW = ("2024-01-01 00:00:00", "2025-01-01 00:00:00")
WHERE = f"DateCreated >= timestamp '{WINDOW[0]}' AND DateCreated < timestamp '{WINDOW[1]}'"
THRESH_DAYS = 7
META = {
    "name": "sacramento_311",
    "url": BASE,
    "license": "City of Sacramento open data (City of Sacramento ArcGIS Hub), open public data",
    "publisher": "City of Sacramento (311 Customer Contact Center)",
    "task": "binary: Sacramento 311 request closed within 7 days of creation",
    "label": f"DateClosed valid (>= DateCreated) and DateClosed - DateCreated <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "category levels/name, council district, incident source, neighborhood, zip, "
    "created hour/dow/month: all recorded at intake",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "CategoryLevel1",
    "CategoryLevel2",
    "CategoryName",
    "CouncilDistrictNumber",
    "SourceLevel1",
    "Neighborhood",
    "ZIP",
]
FILE = "sacramento311_2024.csv"


def fetch(raw):
    out = raw / FILE
    if out.exists():
        return
    raw.mkdir(parents=True, exist_ok=True)
    cnt = requests.get(
        BASE, params={"where": WHERE, "returnCountOnly": "true", "f": "json"}, timeout=120
    ).json()["count"]
    tmp = out.with_suffix(".csv.part")
    n = 0
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(FIELDS)
        for off in range(0, cnt, 2000):
            params = {
                "where": WHERE,
                "outFields": ",".join(FIELDS),
                "returnGeometry": "false",
                "orderByFields": "OBJECTID",
                "resultOffset": off,
                "resultRecordCount": 2000,
                "f": "json",
            }
            for attempt in range(8):
                try:
                    r = requests.get(BASE, params=params, timeout=(10, 90))
                    r.raise_for_status()
                    feats = r.json()["features"]
                    break
                except Exception:
                    if attempt == 7:
                        raise
            for x in feats:
                a = x["attributes"]
                w.writerow([a.get(k) for k in FIELDS])
            n += len(feats)
    tmp.replace(out)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": BASE,
                "where": WHERE,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": out.stat().st_size,
                "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "rows": n,
                "expected_count": cnt,
            },
            indent=1,
        )
    )


def _dt(s):
    return (
        pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True)
        .dt.tz_convert("America/Los_Angeles")
        .dt.tz_localize(None)
    )


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = _dt(d["DateCreated"])
    closed = _dt(d["DateClosed"])
    delta = closed - ts
    valid = delta >= pd.Timedelta(0)  # excludes the 1899 sentinel and NaT
    y = (valid & (delta <= pd.Timedelta(days=THRESH_DAYS))).astype(int)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            **{c: d[c] for c in CAT},
        }
    )
    out = out.dropna(subset=["ts"])
    out = out[(out.ts >= WINDOW[0]) & (out.ts < WINDOW[1])]
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
