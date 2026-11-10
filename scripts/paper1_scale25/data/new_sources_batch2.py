"""Second batch of built-source metadata (merged into new_sources.BUILT at import time of build_ledger)."""

BUILT2 = {
    "montgomery_police_dispatch": dict(
        publisher="Montgomery County MD Police", url="https://data.montgomerycountymd.gov/d/98cc-bc7d", license="Montgomery County MD open data (public domain per catalog)",
        domain="public-safety", task_family="dispatch-response-time", parent="montgomery_police_dispatch", org="Montgomery County MD",
        socrata=("data.montgomerycountymd.gov", "98cc-bc7d"), label="calltime_arrive <= 600 s among incidents with an arrival time",
        features="priority, initial call type, district, sector, PRA, zip, city, hour/dow/month",
        leak="close_type, disposition, crash/crime report flags and all time quantities excluded", delay_rule="100 events (default)", cadence="4 times daily",
        notes="DEV is the full 24-month span (count under 800k); same county as mc311_montgomery and montgomery_traffic (different department)"),
    "usac_erate_invoices": dict(
        publisher="Universal Service Administrative Company (E-Rate)", url="https://datahub.usac.org/d/jpiu-tj8h", license="USAC open data portal (public)",
        domain="finance-economics", task_family="invoice-processing-time", parent="usac_erate_invoices", org="USAC (FCC E-Rate)",
        socrata=("datahub.usac.org", "jpiu-tj8h"), label="inv_line_completion_date - inv_received_date <= 30 days",
        features="invoice type, submission method, SPIN, applicant type/state, service type/category, funding year, bill frequency, requested amounts, discount rate",
        leak="lines listed only once authorized (right-truncation near the window end); decision codes and approved amount excluded",
        delay_rule="100 events (default; true processing lag is weeks)", cadence="daily", notes="Federal programme data, not municipal; DEV is the 24-month span"),
    "nyc_forestry_work_orders": dict(
        publisher="NYC Parks (Forestry)", url="https://data.cityofnewyork.us/d/bdjm-n7q4", license="NYC Open Data terms of use",
        domain="public-works", task_family="work-order-closure", parent="nyc_forestry_work_orders", org="City of New York (Parks)",
        socrata=("data.cityofnewyork.us", "bdjm-n7q4"), label="closed within 30 days of creation (open or cancelled = 0)",
        features="work-order type/priority/category, borough, community board, zip, council district, sidewalk-damage and wire-conflict flags, hour/dow/month",
        leak="status/cancel/finish/crew/sanitation/contract/entity fields excluded", delay_rule="100 events (default)", cadence="daily",
        notes="Different agency (Parks) from the FDNY recipes"),
}
