"""calgary_311 (scale-25 DEV recipe). Label: closed within 7 days of creation; window fixed by the protocol rule
(DEV = last 12 months of [2023-07-01, 2025-07-01) because the metadata count exceeds 800k).
Label threshold (7 days) is the protocol default for 311-style streams, fixed before any build.
service name, request source, responsible agency (routed by service type at intake: caveat), location type, community code and creation hour/dow/month; status_description and updated_date excluded
"""

from sources._socrata_common import make_module

CFG = {
    "name": "calgary_311",
    "domain": "data.calgary.ca",
    "rid": "iahh-g8bj",
    "open_col": "requested_date",
    "close_col": "closed_date",
    "thresh_days": 7,
    "window": ("2024-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "The City of Calgary (311 Service Requests)",
    "license": "City of Calgary Open Data Licence (Open Government Licence - Calgary)",
    "page": "https://data.calgary.ca/d/iahh-g8bj",
    "task": "binary: 311 request closed within 7 days of creation",
    "label_text": "closed_date present and closed_date - requested_date <= 7 days (still open = 0)",
    "features_note": "service name, request source, responsible agency (routed by service type at intake: caveat), location type, community code and creation hour/dow/month; status_description and updated_date excluded",
    "cat": {"service_name": "service_name", "source": "source", "agency": "agency_responsible", "location_type": "location_type", "comm_code": "comm_code"},
}
globals().update(make_module(CFG))
