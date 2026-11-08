"""Pittsburgh 311 (WPRDC "311 Data", resource 29462525-...): closed within 7 days of creation.

Label rationale (fixed before building, from documentation/domain knowledge): the City of
Pittsburgh 311 stream mixes quickly-resolved items (missed collection, potholes, graffiti, street
lights, information requests) with longer code-enforcement, forestry and capital-project work, so a
7-day threshold is expected to give a base rate inside [0.3, 0.7]. Still-open requests (no
closed_date_et) are 0; closed_date_et - create_date_et <= 7 days is 1. The feed stopped updating on
2025-02-04 (new 311 system), and the window is 2022-07-01 to 2024-07-01 by creation time (>28
months before the fetch), so labels are mature. Per the codebook, closures are recorded on parent
tickets and propagate to grouped child tickets; this is used as published.
status_name/status_code, parent_closed, closed_date_*, last_action_*, num_requests and group_id
(both assigned by later grouping), street/cross-street addresses, coordinates and geo_accuracy are
never features. Features are request type, department routed by type, request origin (intake
channel), neighbourhood, council district, ward, police zone and created hour/dow/month.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import requests

RID = "29462525-62a6-45bf-9b5e-ad2e1c06348d"
URL = "https://data.wprdc.org/api/3/action/datastore_search_sql"
COLS = "create_date_et,closed_date_et,dept,request_type_name,origin,neighborhood,council_district,ward,police_zone"
WINDOW = ("2022-07-01T00:00:00", "2024-07-01T00:00:00")
THRESH_DAYS = 7
PAGE = 30000
META = {
    "name": "pittsburgh_311",
    "url": URL + f"?resource_id={RID}",
    "license": "Creative Commons Attribution (WPRDC / City of Pittsburgh)",
    "publisher": "City of Pittsburgh via the Western Pennsylvania Regional Data Center (311 Data)",
    "task": "binary: Pittsburgh 311 request closed within 7 days of creation",
    "label": f"closed_date_et present and closed_date_et - create_date_et <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "request type, dept, origin, neighbourhood, council district, ward, police zone, created hour/dow/month",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "dept",
    "request_type_name",
    "origin",
    "neighborhood",
    "council_district",
    "ward",
    "police_zone",
]
FILE = "pittsburgh311_2022-07_2024-06.csv"


def fetch(raw: Path) -> None:
    out = raw / FILE
    if out.exists():
        return
    frames, off = [], 0
    while True:
        sql = (
            f"SELECT _id,{COLS} FROM \"{RID}\" WHERE create_date_et >= '{WINDOW[0]}' "
            f"AND create_date_et < '{WINDOW[1]}' ORDER BY _id LIMIT {PAGE} OFFSET {off}"
        )
        for attempt in range(6):
            try:
                r = requests.get(URL, params={"sql": sql}, timeout=(15, 300))
                r.raise_for_status()
                recs = r.json()["result"]["records"]
                break
            except Exception:
                if attempt == 5:
                    raise
        if not recs:
            break
        frames.append(pd.DataFrame(recs).drop(columns=["_full_text"], errors="ignore"))
        off += PAGE
        if len(recs) < PAGE:
            break
    df = pd.concat(frames, ignore_index=True)
    tmp = out.with_suffix(".csv.part")
    df.to_csv(tmp, index=False)
    tmp.replace(out)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": URL,
                "resource_id": RID,
                "window": WINDOW,
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": out.stat().st_size,
                "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "rows": len(df),
            },
            indent=1,
        )
    )


def load(raw: Path) -> pd.DataFrame:
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["create_date_et"], errors="coerce")
    closed = pd.to_datetime(d["closed_date_et"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    out = pd.DataFrame(
        {"ts": ts, "y": y, "hour": ts.dt.hour, "dow": ts.dt.dayofweek, "month": ts.dt.month}
    )
    for c in CAT:
        out[c] = d[c]
    return out.dropna(subset=["ts"]).sort_values("ts", kind="stable").reset_index(drop=True)
