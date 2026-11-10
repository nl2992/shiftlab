"""mc311_montgomery (scale-25 DEV recipe). Label: closed within 7 days of creation; window fixed by the protocol rule
(DEV = last 12 months of [2023-07-01, 2025-07-01) because the metadata count exceeds 800k).
Label threshold (7 days) is the protocol default for 311-style streams, fixed before any build.
SR type/area/sub-area, department, zip, council district, city and creation hour/dow/month; SLA fields, status, days-open and last-update excluded (outcome-dependent or unstated timing)
"""

from sources._socrata_common import make_module

CFG = {
    "name": "mc311_montgomery",
    "domain": "data.montgomerycountymd.gov",
    "rid": "xtyh-brr2",
    "open_col": "created",
    "close_col": "closed",
    "thresh_days": 7,
    "window": ("2024-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "Montgomery County MD (MC311 Service Requests)",
    "license": "Montgomery County MD open data (data.montgomerycountymd.gov), public use",
    "page": "https://data.montgomerycountymd.gov/d/xtyh-brr2",
    "task": "binary: 311 request closed within 7 days of creation",
    "label_text": "closed present and closed - created <= 7 days (still open = 0)",
    "features_note": "SR type/area/sub-area, department, zip, council district, city and creation hour/dow/month; SLA fields, status, days-open and last-update excluded (outcome-dependent or unstated timing)",
    "cat": {"sr_type": "sr_type", "sr_area": "sr_area", "sr_sub_area": "sr_sub_area", "department": "department", "zipcode": "x_zipcode", "council_dist": "x_councildist", "city": "x_city"},
}
globals().update(make_module(CFG))
