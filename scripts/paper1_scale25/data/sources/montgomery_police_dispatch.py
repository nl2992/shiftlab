"""Montgomery County MD Police Dispatched Incidents (county open data): first unit arrives within 10 minutes of call pickup.

Label y = 1 if calltime_arrive (seconds from call pickup to first unit on scene, documented in the column
description) <= 600; incidents with no arrival time are excluded. 10 minutes is the response horizon used for
the NYC EMS recipe, fixed before any build. Known at pickup: priority (0-4), initial call type, police district,
sector, PRA, zip, city, hour/dow/month. Excluded: close_type, disposition, cr_number, crash_reports and every
calltime_*/dispatch_*/arrive_* quantity. Window (protocol): 24 months [2023-07-01, 2025-07-01) (count 410k <= 800k).
"""

import pandas as pd

from sources._socrata_common import make_module


def _label(d, ts):
    s = pd.to_numeric(d["calltime_arrive"], errors="coerce")
    return (s <= 600).astype(float).where(s.notna())


CFG = {
    "name": "montgomery_police_dispatch",
    "domain": "data.montgomerycountymd.gov",
    "rid": "98cc-bc7d",
    "open_col": "start_time",
    "close_col": None,
    "label_fn": _label,
    "label_cols": ["calltime_arrive"],
    "window": ("2023-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "Montgomery County MD Police (Police Dispatched Incidents)",
    "license": "Montgomery County MD open data (public domain per catalog)",
    "page": "https://data.montgomerycountymd.gov/d/98cc-bc7d",
    "task": "binary: first police unit on scene within 10 minutes of call pickup",
    "label_text": "calltime_arrive <= 600 s among incidents with an arrival time",
    "features_note": "priority, initial call type, police district, sector, PRA, zip, city, hour/dow/month (call-pickup fields)",
    "cat": {"priority": "priority", "initial_type": "initial_type", "district": "police_district_number", "sector": "sector", "pra": "pra", "zip": "zip", "city": "city"},
}
globals().update(make_module(CFG))
