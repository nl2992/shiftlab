"""Philadelphia 311 service requests (OpenDataPhilly, phl.carto.com table public_cases_fc):
closed within 5 days of the request.

Label rationale (fixed before downloading, from documentation/domain knowledge): Philly311 mixes
information requests and quick-service tickets (closed within hours/days) with longer field work
(abandoned vehicles, illegal dumping, street/lighting and inspection requests with multi-day to
multi-week targets), so a 5-day threshold is expected to give a base rate in the middle of
[0.2, 0.8]. Open or closed-later = 0. The window ends >1 year before the fetch so statuses are
settled. closed_datetime is used only for the label; status, status_notes, updated_datetime,
expected_datetime, service_notice, subject and media are never features. Features are those set at
the request: service_name, service_code, agency_responsible (assigned from the service type),
zip code, request hour/dow/month (America/New_York local). The table has no channel field.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import pandas as pd
import requests

URL = "https://phl.carto.com/api/v2/sql"
WINDOW = ("2024-07-01", "2025-07-01")
THRESH_DAYS = 5
META = {
    "name": "philly_311",
    "url": URL + " (table public_cases_fc)",
    "license": "OpenDataPhilly / City of Philadelphia open data (Creative Commons Attribution)",
    "publisher": "City of Philadelphia (Philly311, via OpenDataPhilly / phl.carto.com)",
    "task": "binary: 311 request closed within 5 days of being requested",
    "label": f"closed_datetime present and closed_datetime - requested_datetime <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "service name/code, responsible agency, zip code, request hour/dow/month",
}
NUM = ["hour", "dow", "month"]
CAT = ["service_name", "service_code", "agency", "zipcode"]
FILE = "philly311_2024-07_2025-06.csv"


def _months():
    t = pd.Timestamp(WINDOW[0])
    end = pd.Timestamp(WINDOW[1])
    while t < end:
        n = t + pd.offsets.MonthBegin(1)
        yield t.strftime("%Y-%m-%d"), n.strftime("%Y-%m-%d")
        t = n


def fetch(raw):
    out = raw / FILE
    if out.exists():
        return
    tmp = out.with_suffix(".csv.part")
    n, first = 0, True
    with open(tmp, "wb") as f:
        for a, b in _months():
            q = (
                "select service_name,service_code,agency_responsible,zipcode,requested_datetime,"
                f"closed_datetime from public_cases_fc where requested_datetime >= '{a}' "
                f"and requested_datetime < '{b}' order by requested_datetime"
            )
            for attempt in range(4):
                try:
                    r = requests.get(URL, params={"q": q, "format": "csv"}, timeout=600)
                    r.raise_for_status()
                    break
                except Exception:
                    if attempt == 3:
                        raise
            body = r.content
            if not first:
                body = body.split(b"\n", 1)[1]  # drop repeated header
            first = False
            f.write(body)
            n += len(body)
    tmp.replace(out)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": URL + " (monthly SQL chunks, table public_cases_fc)",
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": out.stat().st_size,
                "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
            },
            indent=1,
        )
    )


def _local(s):
    return pd.to_datetime(s, errors="coerce", utc=True).dt.tz_convert("America/New_York")


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = _local(d["requested_datetime"])
    closed = _local(d["closed_datetime"])
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)
    ts = ts.dt.tz_localize(None)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "service_name": d["service_name"],
            "service_code": d["service_code"],
            "agency": d["agency_responsible"],
            "zipcode": d["zipcode"],
        }
    )
    return out.dropna(subset=["ts"]).sort_values("ts", kind="stable").reset_index(drop=True)
