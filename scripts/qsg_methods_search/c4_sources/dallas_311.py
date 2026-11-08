"""City of Dallas 311 Service Requests (dallasopendata.com, Socrata d7e7-envw): closed within 3 days.

Label rationale (fixed before downloading, from documentation/domain knowledge): the dataset's
ert_estimated_response_time field spans hours to several business days by request type (parking,
code concern, loose-animal and similar fast types vs. longer service-department work orders), so
a 3-day (72 h) closure threshold is expected to split the stream with a base rate in the middle of
[0.2, 0.8]. Still-open or closed-later = 0. The window ends >1 year before the fetch so statuses
have settled. status/closed_date/outcome/update_date/due_date are used only for the label (closed
date) and never as features. Features are those set at intake: request type, the department that
owns the type, estimated response time (a function of type), priority, intake channel, council
district, request hour/dow/month.
"""

from __future__ import annotations

import pandas as pd

from c4_sources._dl_nyc import download

URL = "https://www.dallasopendata.com/resource/d7e7-envw.csv"
COLS = (
    "created_date,closed_date,service_request_type,department,"
    "ert_estimated_response_time,priority,method_received_description,city_council_district"
)
WINDOW = ("2024-07-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 3
META = {
    "name": "dallas_311",
    "url": URL,
    "license": "Dallas Open Data (Socrata), City of Dallas; open public data, no login",
    "publisher": "City of Dallas (311 / dallasopendata.com)",
    "task": "binary: 311 service request closed within 3 days of creation",
    "label": f"closed_date present and closed_date - created_date <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "request type, department, estimated response time, priority, intake "
    "channel, council district, created hour/dow/month: all set at intake",
}
NUM = ["hour", "dow", "month"]
CAT = [
    "service_request_type",
    "department",
    "ert",
    "priority",
    "method",
    "council_district",
]
FILE = "dallas311_2024-07_2025-06.csv"


def fetch(raw):
    where = f"created_date >= '{WINDOW[0]}' AND created_date < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$order": "created_date", "$limit": 1_500_000}
    download(URL, params, raw / FILE)


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["created_date"], errors="coerce")
    closed = pd.to_datetime(d["closed_date"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "service_request_type": d["service_request_type"],
            "department": d["department"],
            "ert": d["ert_estimated_response_time"],
            "priority": d["priority"],
            "method": d["method_received_description"],
            "council_district": d["city_council_district"],
        }
    )
    return out.dropna(subset=["ts"])
