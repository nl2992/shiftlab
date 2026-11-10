"""edmonton_311 (scale-25 DEV recipe). Label: closed within 7 days of creation; window fixed by the protocol rule
(DEV = last 12 months of [2023-07-01, 2025-07-01) because the metadata count exceeds 800k).
Label threshold (7 days) is the protocol default for 311-style streams, fixed before any build.
service category/area/description, interaction channel, ward, neighbourhood and creation hour/dow/month; request_status, status_detail, referral_type and closure fields are excluded
"""

from sources._socrata_common import make_module

CFG = {
    "name": "edmonton_311",
    "domain": "data.edmonton.ca",
    "rid": "q7ua-agfg",
    "open_col": "date_created",
    "close_col": "date_closed",
    "thresh_days": 7,
    "window": ("2024-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "City of Edmonton (311 Requests)",
    "license": "City of Edmonton Open Data Terms of Use (Open Government Licence - Edmonton)",
    "page": "https://data.edmonton.ca/d/q7ua-agfg",
    "task": "binary: 311 request closed within 7 days of creation",
    "label_text": "date_closed present and date_closed - date_created <= 7 days (still open = 0)",
    "features_note": "service category/area/description, interaction channel, ward, neighbourhood and creation hour/dow/month; request_status, status_detail, referral_type and closure fields are excluded",
    "cat": {"service_category": "service_category", "service_area": "service_area", "service_description": "service_description", "channel": "interaction_channel", "ward": "ward", "neighbourhood": "neighbourhood"},
}
globals().update(make_module(CFG))
