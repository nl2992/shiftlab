"""winnipeg_311 (scale-25 DEV recipe). Label: closed within 7 days of creation; window fixed by the protocol rule
(DEV = last 12 months of [2023-07-01, 2025-07-01) because the metadata count exceeds 800k).
Label threshold (7 days) is the protocol default for 311-style streams, fixed before any build.
request reason/subject/type, channel type, ward, neighbourhood and open hour/dow/month; case_status and closed_date only in the label
"""

from sources._socrata_common import make_module

CFG = {
    "name": "winnipeg_311",
    "domain": "data.winnipeg.ca",
    "rid": "u7f6-5326",
    "open_col": "open_date",
    "close_col": "closed_date",
    "thresh_days": 7,
    "window": ("2024-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "City of Winnipeg (311 Requests)",
    "license": "Open Government Licence - Winnipeg (Canada OGL compatible)",
    "page": "https://data.winnipeg.ca/d/u7f6-5326",
    "task": "binary: 311 request closed within 7 days of creation",
    "label_text": "closed_date present and closed_date - open_date <= 7 days (still open = 0)",
    "features_note": "request reason/subject/type, channel type, ward, neighbourhood and open hour/dow/month; case_status and closed_date only in the label",
    "cat": {"reason": "reason", "subject": "subject", "type": "type", "channel": "channel_type", "ward": "ward", "neighbourhood": "neighbourhood"},
}
globals().update(make_module(CFG))
