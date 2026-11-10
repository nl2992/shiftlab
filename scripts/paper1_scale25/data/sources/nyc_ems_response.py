"""NYC EMS Incident Dispatch Data (NYC Open Data, FDNY): first unit on scene within 10 minutes of the call.

Event = EMS incident with a valid incident response time. Label y = 1 if incident_response_seconds_qy <= 600
(10 minutes; the response-time horizon commonly reported for FDNY EMS, fixed before any build). Incidents with
valid_incident_rspns_time_indc != 'Y' or no response time are excluded by the SoQL filter / dropna (no
arrival to time). Known at call intake: initial call type, initial severity level, borough, zip, community
district, police precinct, dispatch area, special-event flag, hour/dow/month. Excluded: final_* fields,
disposition, hold indicator, any dispatch/travel/on-scene timestamps (all outcome-time).
Window (protocol): last 12 months of [2023-07-01, 2025-07-01) because the 24-month count exceeds 800k.
"""

import pandas as pd

from sources._socrata_common import make_module


def _label(d, ts):
    s = pd.to_numeric(d["incident_response_seconds_qy"], errors="coerce")
    return (s <= 600).astype(float).where(s.notna())


CFG = {
    "name": "nyc_ems_response",
    "domain": "data.cityofnewyork.us",
    "rid": "76xm-jjuj",
    "open_col": "incident_datetime",
    "close_col": None,
    "label_fn": _label,
    "label_cols": ["incident_response_seconds_qy"],
    "where_extra": "valid_incident_rspns_time_indc='Y'",
    "window": ("2024-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "New York City Fire Department / NYC Open Data (EMS Incident Dispatch Data)",
    "license": "NYC Open Data terms of use (public data)",
    "page": "https://data.cityofnewyork.us/d/76xm-jjuj",
    "task": "binary: EMS first unit on scene within 10 minutes of the incident",
    "label_text": "incident_response_seconds_qy <= 600 among valid response times",
    "features_note": "initial call type and severity, borough, zip, community district, police precinct, dispatch area, special-event flag, hour/dow/month (call-intake fields)",
    "cat": {
        "call_type": "initial_call_type", "severity": "initial_severity_level_code", "borough": "borough",
        "zipcode": "zipcode", "community_district": "communitydistrict", "precinct": "policeprecinct",
        "dispatch_area": "incident_dispatch_area", "special_event": "special_event_indicator",
    },
}
globals().update(make_module(CFG))
