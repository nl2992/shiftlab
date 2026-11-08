"""Oakland OAK 311 service requests (data.oaklandca.gov, quth-gb8e): closed within 7 days of init.

Label rationale (fixed before downloading, from documentation/domain knowledge): the Oakland Call
Center logs both informational calls/questions (closed at once) and field requests (illegal dumping,
potholes, streetlights, abandoned vehicles) that are worked through department queues over days to
weeks, so a 7-day threshold is expected to give a base rate inside [0.3, 0.7]. Still-open or
closed-later requests = 0. Window ends >1 year before fetch so status is settled.
status/datetimeclosed are used only for the label. Features are set at intake: request description
(type), request category (department queue), intake source, council district, police beat, zip,
request hour/dow/month.
"""

from __future__ import annotations

import pandas as pd

from ._dl_nyc import download

URL = "https://data.oaklandca.gov/resource/quth-gb8e.csv"
COLS = "datetimeinit,datetimeclosed,source,description,reqcategory,councildistrict,beat,zipcode"
WINDOW = ("2023-07-01T00:00:00", "2025-07-01T00:00:00")
THRESH_DAYS = 7
META = {
    "name": "oakland_311",
    "url": URL,
    "license": "City of Oakland open data (data.oaklandca.gov), public domain / open government data",
    "publisher": "City of Oakland (OAK 311 Call Center)",
    "task": "binary: OAK 311 request closed within 7 days of initiation",
    "label": f"datetimeclosed present and datetimeclosed - datetimeinit <= {THRESH_DAYS} days",
    "delay": 100,
    "window": WINDOW,
    "subsample_rule": "c4_build.N_MAX systematic",
    "features_note": "description, category, intake source, council district, beat, zip, "
    "init hour/dow/month: all recorded at intake",
}
NUM = ["hour", "dow", "month"]
CAT = ["description", "reqcategory", "source", "councildistrict", "beat", "zipcode"]
FILE = "oakland311_2023-07_2025-06.csv"


def fetch(raw):
    where = f"datetimeinit >= '{WINDOW[0]}' AND datetimeinit < '{WINDOW[1]}'"
    params = {"$select": COLS, "$where": where, "$order": "datetimeinit", "$limit": 1_000_000}
    download(URL, params, raw / FILE)


def load(raw):
    d = pd.read_csv(raw / FILE, dtype=str)
    ts = pd.to_datetime(d["datetimeinit"], errors="coerce")
    closed = pd.to_datetime(d["datetimeclosed"], errors="coerce")
    y = ((closed - ts) <= pd.Timedelta(days=THRESH_DAYS)).astype(int)
    out = pd.DataFrame(
        {
            "ts": ts,
            "y": y,
            "hour": ts.dt.hour,
            "dow": ts.dt.dayofweek,
            "month": ts.dt.month,
            "description": d["description"],
            "reqcategory": d["reqcategory"],
            "source": d["source"],
            "councildistrict": d["councildistrict"],
            "beat": d["beat"],
            "zipcode": d["zipcode"],
        }
    )
    out = out.dropna(subset=["ts"])
    return out.sort_values("ts", kind="stable").reset_index(drop=True)
