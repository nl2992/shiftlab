"""City of San Diego "Get It Done" reports (data.sandiego.gov, seshat.datasd.org): closed within 14 days.

Label rationale (fixed before downloading, from documentation/domain knowledge): Get It Done
requests (graffiti, illegal dumping, potholes, sidewalk and streetlight repair, parks issues,
abandoned vehicles) are routed to different City staff groups; policing/graffiti requests are
closed in days while infrastructure work orders take weeks to months, so a 14-day threshold is
expected to give a base rate inside [0.3, 0.7]. Open, referred-later or closed-later = 0
(label = status in {Closed, Referred} and case_age_days <= 14; case_age_days is documented as the
whole-day span between request and closure). Published files are split by CLOSURE year plus an open
file, so the calendar-2024 request window is assembled from closed_2024, closed_2025, closed_2026
and open files (all four are fetched; the last request of the window is >22 months before fetch).
Raw downloads are streamed and trimmed (selected columns, window rows) to keep raw small; the
receipt records the sha256 of each full original file. status, date_closed, case_age_days,
referred, parent id, SAP number, asset codes and public_description are NEVER features. Features
are set at intake: staff group (case_record_type), service name and detail, council district,
community plan code, zip, case origin, request hour/dow/month.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from datetime import UTC, datetime

import pandas as pd
import requests

BASE = "https://seshat.datasd.org/get_it_done_reports/get_it_done_requests_{}_datasd.csv"
PARTS = ["closed_2024", "closed_2025", "closed_2026", "open"]
WINDOW = ("2024-01-01 00:00:00", "2025-01-01 00:00:00")
THRESH_DAYS = 14
USE = [
    "date_requested",
    "case_age_days",
    "status",
    "case_record_type",
    "service_name",
    "service_name_detail",
    "council_district",
    "comm_plan_code",
    "zipcode",
    "case_origin",
]
META = {
    "name": "sandiego_311",
    "url": BASE.format("{closed_2024,closed_2025,closed_2026,open}"),
    "license": "City of San Diego open data (data.sandiego.gov), Creative Commons CC0 / public domain",
    "publisher": "City of San Diego (Get It Done)",
    "task": "binary: Get It Done request closed within 14 days of being requested",
    "label": f"status in (Closed, Referred) and case_age_days <= {THRESH_DAYS}",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "staff group, service name/detail, council district, community plan, zip, "
    "case origin, request hour/dow/month: all recorded at intake",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "case_record_type",
    "service_name",
    "service_name_detail",
    "council_district",
    "comm_plan_code",
    "zipcode",
    "case_origin",
]
FILE = "sandiego_getitdone_req2024.csv"


def fetch(raw):
    out = raw / FILE
    if out.exists():
        return
    raw.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".csv.part")
    tmp.unlink(missing_ok=True)
    receipts = []
    first = True
    for part in PARTS:
        url = BASE.format(part)
        h = hashlib.sha256()
        n = 0
        with tempfile.TemporaryDirectory(dir=raw) as td:
            f = f"{td}/full.csv"
            with requests.get(url, timeout=1200, stream=True) as r:
                r.raise_for_status()
                with open(f, "wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
                        h.update(chunk)
                        n += len(chunk)
            kept = 0
            for ch in pd.read_csv(f, usecols=USE, dtype=str, chunksize=100_000):
                m = (ch["date_requested"] >= WINDOW[0]) & (ch["date_requested"] < WINDOW[1])
                ch = ch[m]
                kept += len(ch)
                ch.to_csv(tmp, mode="w" if first else "a", header=first, index=False)
                first = False
        receipts.append({"url": url, "bytes": n, "sha256": h.hexdigest(), "rows_kept": kept})
    tmp.replace(out)
    (raw / f"{FILE}.receipt.json").write_text(
        json.dumps(
            {
                "url": META["url"],
                "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                "bytes": out.stat().st_size,
                "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                "originals": receipts,
            },
            indent=1,
        )
    )


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["date_requested"], errors="coerce")
    age = pd.to_numeric(d["case_age_days"], errors="coerce")
    done = d["status"].isin(["Closed", "Referred"])
    y = (done & (age <= THRESH_DAYS)).astype(int)
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
