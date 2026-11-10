"""NYC Parks Forestry Work Orders (NYC Open Data): work order closed within 30 days of creation.

Label y = 1 if closeddate - createddate <= 30 days (never closed or cancelled = 0; 30 days is the protocol default
for work-order streams, fixed before any build). Known at creation: work-order type, priority, category,
borough, community board, zip, city council district, sidewalk-damage and wire-conflict flags. Excluded:
status, cancel fields, finish date, crew, sanitation fields, contract and entity assignments (assigned during
handling), and updated date. Window (protocol): 24 months [2023-07-01, 2025-07-01) (count 306k <= 800k).
"""

from sources._socrata_common import make_module

CFG = {
    "name": "nyc_forestry_work_orders",
    "domain": "data.cityofnewyork.us",
    "rid": "bdjm-n7q4",
    "open_col": "createddate",
    "close_col": "closeddate",
    "thresh_days": 30,
    "window": ("2023-07-01T00:00:00", "2025-07-01T00:00:00"),
    "publisher": "NYC Parks and Recreation (Forestry) / NYC Open Data",
    "license": "NYC Open Data terms of use (public data)",
    "page": "https://data.cityofnewyork.us/d/bdjm-n7q4",
    "task": "binary: forestry work order closed within 30 days of creation",
    "label_text": "closeddate - createddate <= 30 days (open or cancelled = 0)",
    "features_note": "work-order type/priority/category, borough, community board, zip, council district, sidewalk-damage and wire-conflict flags, hour/dow/month",
    "cat": {
        "wotype": "wotype",
        "priority": "wopriority",
        "category": "wocategory",
        "borough": "boroughcode",
        "community_board": "communityboard",
        "zipcode": "zipcode",
        "council": "citycouncil",
        "sidewalk_damage": "sidewalkdamage",
        "wire_conflict": "wowireconflict",
    },
}
globals().update(make_module(CFG))
