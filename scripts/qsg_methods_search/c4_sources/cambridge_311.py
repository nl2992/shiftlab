"""Cambridge MA Commonwealth Connect (SeeClickFix) Service Requests (data.cambridgema.gov 2z9k-mv9g):
closed within 7 days of creation.

Label rationale (fixed before downloading, from documentation/domain knowledge): Cambridge routes
Commonwealth Connect reports (potholes, trash, graffiti, parking, bike-lane, sidewalk etc.) to DPW,
Traffic/Parking and Inspectional Services; simple field issues are closed in days, others take
weeks. A 7-day threshold is expected to give a base rate inside [0.3, 0.7]. Tickets with no closure
timestamp (open/acknowledged/archived) = 0. The window ends 22 months before the fetch.
ticket_closed_date_time is used only for the label; ticket_status, ticket_last_updated_date_time,
acknowledged_at, issue_description (free text), image and html_url are never features. Features:
issue type, issue category, ~1 km location grid cell (rounded lat/lng, as reported at intake),
created hour/dow/month (timestamps are local America/New_York as published).
"""

from __future__ import annotations

import pandas as pd

try:
    from ._dl_nyc import download
except ImportError:
    from c4_sources._dl_nyc import download

URL = "https://data.cambridgema.gov/resource/2z9k-mv9g.csv"
COLS = "ticket_created_date_time,ticket_closed_date_time,issue_type,issue_category,lat,lng"
WINDOW = ("2023-01-01T00:00:00", "2025-01-01T00:00:00")
THRESH_DAYS = 7
META = {
    "name": "cambridge_311",
    "url": URL,
    "license": "Open data (data.cambridgema.gov), City of Cambridge MA",
    "publisher": "City of Cambridge MA (Commonwealth Connect Service Requests)",
    "task": "binary: Cambridge 311 ticket closed within 7 days of creation",
    "label": f"ticket_closed_date_time present and closed - created <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "issue type, issue category, 0.01-degree location cell, hour/dow/month: intake-time",
}
NUM = ["hour", "dow", "month"]
CAT = ["issue_type", "issue_category", "cell"]
FILE = "cambridge311_2023_2024.csv"


def fetch(raw):
    where = (
        f"ticket_created_date_time >= '{WINDOW[0]}' AND ticket_created_date_time < '{WINDOW[1]}'"
    )
    download(
        URL,
        {
            "$select": COLS,
            "$where": where,
            "$order": "ticket_created_date_time",
            "$limit": 1_500_000,
        },
        raw / FILE,
    )


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["ticket_created_date_time"], errors="coerce")
    closed = pd.to_datetime(d["ticket_closed_date_time"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)  # NaT -> 0
    lat = pd.to_numeric(d["lat"], errors="coerce").round(2)
    lng = pd.to_numeric(d["lng"], errors="coerce").round(2)
    cell = lat.astype(str) + "," + lng.astype(str)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "issue_type": d["issue_type"],
            "issue_category": d["issue_category"],
            "cell": cell,
        }
    )
    out = out.dropna(subset=["ts"])
    out = out[(out.ts >= WINDOW[0]) & (out.ts < WINDOW[1])]
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
