"""NYC Fire Incident Dispatch Data (NYC Open Data, FDNY): first unit on scene within 5 minutes of the alarm.

Label y = 1 if incident_response_seconds_qy <= 300 (5 minutes, fixed before any build) among valid response
times. Known at alarm intake: incident classification (and group), alarm source, borough, zip, community
district, police precinct, hour/dow/month. Excluded: alarm level, units assigned, all assignment/activation/
on-scene/close timestamps and the travel/dispatch time quantities (outcome-time).
Window (protocol): last 12 months of [2023-07-01, 2025-07-01); the 24-month count (1.38M) exceeds 800k.
"""

import pandas as pd

from sources._socrata_common import make_module


def _label(d, ts):
    s = pd.to_numeric(d["incident_response_seconds_qy"], errors="coerce")
    return (s <= 300).astype(float).where(s.notna())


CFG = {
    "name": "nyc_fire_response",
    "domain": "data.cityofnewyork.us",
    "rid": "8m42-w767",
    "open_col": "incident_datetime",
    "close_col": None,
    "label_fn": _label,
    "label_cols": ["incident_response_seconds_qy"],
    "where_extra": "valid_incident_rspns_time_indc='Y'",
    "window": ("2024-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "New York City Fire Department / NYC Open Data (Fire Incident Dispatch Data)",
    "license": "NYC Open Data terms of use (public data)",
    "page": "https://data.cityofnewyork.us/d/8m42-w767",
    "task": "binary: first fire unit on scene within 5 minutes of the incident",
    "label_text": "incident_response_seconds_qy <= 300 among valid response times",
    "features_note": "incident classification and group, alarm source, borough, zip, community district, police precinct, hour/dow/month (alarm-intake fields)",
    "cat": {
        "classification": "incident_classification", "group": "incident_classification_group",
        "alarm_source": "alarm_source_description_tx", "borough": "incident_borough", "zipcode": "zipcode",
        "community_district": "communitydistrict", "precinct": "policeprecinct",
    },
}
globals().update(make_module(CFG))
