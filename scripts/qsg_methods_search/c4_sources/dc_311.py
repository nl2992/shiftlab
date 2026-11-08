"""Washington DC 311 City Service Requests 2024 (opendata.dc.gov, DCGIS ServiceRequests layer 16):
resolved within 5 days of being added.

Label rationale (fixed before downloading, from documentation/domain knowledge): DC 311 mixes
same-day parking/trash enforcement tickets with service orders that carry multi-day to multi-week
due dates (bulk pickup, potholes, tree and sidewalk work), so a 5-day threshold is expected to give
a base rate in the middle of [0.2, 0.8]. Unresolved or resolved later = 0. The calendar-2024 layer
is fetched ~2 years later so resolutions are settled. RESOLUTIONDATE is used only for the label;
SERVICEDUEDATE, SERVICEORDERDATE, STATUS_CODE, SERVICEORDERSTATUS, inspection fields and DETAILS
are never features. Features are those set at intake: service code and its description/type,
organization acronym (assigned from the service code), ward, zip code, priority, request
hour/dow/month (America/New_York local).
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import pandas as pd
import requests

BASE = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/16/query"
FIELDS = (
    "SERVICECODE,SERVICECODEDESCRIPTION,SERVICETYPECODEDESCRIPTION,ORGANIZATIONACRONYM,"
    "WARD,ZIPCODE,PRIORITY,ADDDATE,RESOLUTIONDATE"
)
WINDOW = ("2024-01-01T00:00:00", "2025-01-01T00:00:00")
THRESH_DAYS = 5
META = {
    "name": "dc_311",
    "url": BASE,
    "license": "DC Open Data (opendata.dc.gov), Government of the District of Columbia, CC0 / open public data",
    "publisher": "Government of the District of Columbia (DC 311 / DCGIS)",
    "task": "binary: 311 service request resolved within 5 days of being added",
    "label": f"RESOLUTIONDATE present and RESOLUTIONDATE - ADDDATE <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "service code/description/type, organization acronym, ward, zip, priority, "
    "added hour/dow/month: all recorded at intake",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "service_code",
    "service_desc",
    "service_type",
    "org",
    "ward",
    "zip",
    "priority",
]
FILE = "dc311_2024.csv"


def fetch(raw):
    out = raw / FILE
    if out.exists():
        return
    from concurrent.futures import ThreadPoolExecutor

    cnt = requests.get(
        BASE, params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, timeout=120
    ).json()["count"]
    cache = raw / "pages"
    cache.mkdir(exist_ok=True)

    def page(off):
        f = cache / f"{off:08d}.json"
        if f.exists():
            return json.loads(f.read_text())
        params = {
            "where": "1=1",
            "outFields": FIELDS,
            "returnGeometry": "false",
            "orderByFields": "OBJECTID",
            "resultOffset": off,
            "resultRecordCount": 1000,
            "f": "json",
        }
        for attempt in range(8):
            try:
                r = requests.get(BASE, params=params, timeout=(10, 40))
                r.raise_for_status()
                p = [x["attributes"] for x in r.json()["features"]]
                f.write_text(json.dumps(p))
                return p
            except Exception:
                if attempt == 7:
                    raise

    with ThreadPoolExecutor(3) as ex:
        pages = list(ex.map(page, range(0, cnt, 1000)))
    rows = [a for p in pages for a in p]
    h = hashlib.sha256()
    tmp = out.with_suffix(".csv.part")
    pd.DataFrame(rows).to_csv(tmp, index=False)
    tmp.replace(out)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": BASE,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": out.stat().st_size,
                "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "rows": len(rows),
                "pages_sha256": h.hexdigest(),
            },
            indent=1,
        )
    )


def _dt(s):
    return (
        pd.to_datetime(pd.to_numeric(s, errors="coerce"), unit="ms", utc=True)
        .dt.tz_convert("America/New_York")
        .dt.tz_localize(None)
    )


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = _dt(d["ADDDATE"])
    closed = _dt(d["RESOLUTIONDATE"])
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "service_code": d["SERVICECODE"],
            "service_desc": d["SERVICECODEDESCRIPTION"],
            "service_type": d["SERVICETYPECODEDESCRIPTION"],
            "org": d["ORGANIZATIONACRONYM"],
            "ward": d["WARD"],
            "zip": d["ZIPCODE"],
            "priority": d["PRIORITY"],
        }
    )
    out = out.dropna(subset=["ts"])
    out = out[(out.ts >= WINDOW[0]) & (out.ts < WINDOW[1])]
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
