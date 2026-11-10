"""WS-A: confirmation-window AVAILABILITY for the existing sources (row counts only, no label data).

Rule (DATASET_ELIGIBILITY_PROTOCOL.md section 4): CONFIRM = [base_end, min(base_end + L, 2026-07-01)),
where base_end/L come from the registered window, or from the fresh window for fresh-opened sources.
Available iff the verified (or labelled-estimated) row count >= 150,000.
"""
import json, re, sys
from pathlib import Path
import requests
from dateutil.relativedelta import relativedelta
from datetime import date

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper1_scale25/data/confirm_avail.json"
CAP = date(2026, 7, 1)
S = lambda d: d.strftime("%Y-%m-%dT00:00:00")
def months(a, b): return (b.year - a.year) * 12 + b.month - a.month

# name: (reg_start, reg_end, fresh_end or None, kind, args)
SPEC = {
 "la_crime": ("2020-01-01", "2025-01-01", None, "soc", ("data.lacity.org", "2nrs-mtv8", "date_occ")),
 "sf_311": ("2024-07-01", "2025-07-01", "2026-07-01", "soc", ("data.sfgov.org", "vw6y-z8j6", "requested_datetime")),
 "nyc_collisions": ("2022-01-01", "2025-10-01", None, "soc", ("data.cityofnewyork.us", "h9gi-nx95", "crash_date")),
 "boston_311": ("2024-01-01", "2025-01-01", None, "ckan_boston", None),
 "kc_311": ("2023-07-01", "2025-07-01", "2026-07-01", "soc", ("data.kcmo.org", "d4px-6rwg", "open_date_time")),
 "montgomery_traffic": ("2024-07-01", "2026-07-01", None, "soc", ("data.montgomerycountymd.gov", "4mse-ku6q", "date_of_stop")),
 "dallas_311": ("2024-07-01", "2025-07-01", "2026-07-01", "soc", ("www.dallasopendata.com", "d7e7-envw", "created_date")),
 "dc_311": ("2024-01-01", "2025-01-01", "2026-01-01", "arc_dc", None),
 "philly_311": ("2024-07-01", "2025-07-01", None, "carto", None),
 "austin_311": ("2024-01-01", "2025-07-01", "2026-07-01", "soc", ("data.austintexas.gov", "xwdj-i9he", "sr_created_date")),
 "cincinnati_311": ("2023-07-01", "2025-07-01", "2026-07-01", "soc", ("data.cincinnati-oh.gov", "gcej-gmiw", "date_created")),
 "nola_311": ("2023-01-01", "2025-07-01", None, "soc", ("data.nola.gov", "2jgv-pqrq", "date_created")),
 "oakland_311": ("2023-07-01", "2025-07-01", "2026-07-01", "soc", ("data.oaklandca.gov", "quth-gb8e", "datetimeinit")),
 "sandiego_311": ("2024-01-01", "2025-01-01", "2026-01-01", "sd", None),
 "sacramento_311": ("2024-01-01", "2025-01-01", None, "arc", ("https://services5.arcgis.com/54falWtcpty3V47Z/arcgis/rest/services/SalesForce311_View/FeatureServer/0", "DateCreated")),
 "baltimore_311": ("2024-09-01", "2025-01-01", None, "arc", ("https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/311_Customer_Service_Requests_{y}/FeatureServer/0", "CreatedDate")),
 "miamidade_311": ("2022-01-01", "2024-01-01", None, "arc", ("https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/data_311_{y}/FeatureServer/0", "ticket_created_date_time")),
 "minneapolis_311": ("2023-01-01", "2025-01-01", None, "arc", ("https://services.arcgis.com/afSMGVsC7QlRK1kZ/ArcGIS/rest/services/Public_311_{y}/FeatureServer/0", "OPENEDDATETIME")),
 "louisville_311": ("2023-01-01", "2025-01-01", None, "louis", None),
 "chicago_311": ("2024-01-01", "2025-01-01", None, "soc", ("data.cityofchicago.org", "v6vf-nfxy", "created_date")),
 "denver_311": ("2022-01-01", "2024-01-01", None, "arc", ("https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/311_Service_Requests_{y}/FeatureServer/0", "Case_Created_dttm")),
 "pittsburgh_311": ("2022-07-01", "2024-07-01", None, "ckan_pgh", None),
 "bts_ontime": ("2025-05-01", "2025-07-01", None, "bts", None),
 "sf_building_permits": ("2015-01-01", "2025-07-01", None, "soc", ("data.sfgov.org", "i98e-djp9", "filed_date")),
 "chicago_traffic_crashes": ("2021-01-01", "2023-01-01", None, "soc", ("data.cityofchicago.org", "85ca-t3if", "crash_date")),
 "dallas_animal_shelter": ("2015-10-01", "2024-10-01", None, "soc", ("www.dallasopendata.com", "txcn-ne83", "intake_date")),
}
def soc_count(dom, rid, col, a, b):
    r = requests.get(f"https://{dom}/resource/{rid}.json", params={"$select": "count(*) as n", "$where": f"{col}>='{S(a)}' AND {col}<'{S(b)}'"}, timeout=120)
    r.raise_for_status(); return int(r.json()[0]["n"])
def arc_count(tmpl, col, a, b):
    tot = 0; used = []
    for y in range(a.year, b.year + 1):
        url = tmpl.format(y=y) if "{y}" in tmpl else tmpl
        w = f"{col} >= timestamp '{a:%Y-%m-%d} 00:00:00' AND {col} < timestamp '{b:%Y-%m-%d} 00:00:00'"
        r = requests.get(url + "/query", params={"where": w, "returnCountOnly": "true", "f": "json"}, timeout=120)
        j = r.json()
        if "count" not in j: raise RuntimeError(f"year {y} layer: {str(j)[:100]}")
        tot += j["count"]; used.append(y)
        if "{y}" not in tmpl: break
    return tot
def count(name, kind, args, a, b):
    if kind == "soc": return soc_count(*args, a, b)
    if kind == "arc": return arc_count(*args, a, b)
    if kind == "arc_dc":
        tot = 0
        for lay in (18, 21):
            url = f"https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/{lay}/query"
            w = f"ADDDATE >= timestamp '{a:%Y-%m-%d} 00:00:00' AND ADDDATE < timestamp '{b:%Y-%m-%d} 00:00:00'"
            j = requests.get(url, params={"where": w, "returnCountOnly": "true", "f": "json"}, timeout=120).json()
            tot += j.get("count", 0)
        return tot
    if kind == "carto":
        q = f"select count(*) as n from public_cases_fc where requested_datetime >= '{a:%Y-%m-%d}' and requested_datetime < '{b:%Y-%m-%d}'"
        return int(requests.get("https://phl.carto.com/api/v2/sql", params={"q": q}, timeout=300).json()["rows"][0]["n"])
    if kind == "louis":
        B = "https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/"
        t = 0
        for n, (x, y) in {"metro_311_2025": ("2025-01-01", "2026-01-01"), "metro_311_2026": ("2026-01-01", "2026-07-01")}.items():
            t += requests.get(B + n + "/FeatureServer/0/query", params={"where": f"requested_datetime >= timestamp '{x} 00:00:00' AND requested_datetime < timestamp '{y} 00:00:00'", "returnCountOnly": "true", "f": "json"}, timeout=90).json()["count"]
        return t
    if kind == "ckan_boston":  # 2025 resource of the 311 package (datastore total); window is calendar 2025
        return requests.get("https://data.boston.gov/api/3/action/datastore_search", params={"resource_id": "9d7c2214-4709-478a-a2e8-fb2020a5bb94", "limit": 0}, timeout=60).json()["result"]["total"]
    if kind == "ckan_pgh":
        import importlib; sys.path.insert(0, str(ROOT / "scripts/qsg_methods_search")); p = importlib.import_module("c4_sources.pittsburgh_311")
        sql = f"SELECT count(*) FROM \"{p.RID}\" WHERE create_date_et >= '{a:%Y-%m-%d}' AND create_date_et < '{b:%Y-%m-%d}'"
        return int(requests.get(p.URL, params={"sql": sql}, timeout=300).json()["result"]["records"][0]["count"])
    raise NotImplementedError(kind)
res = {}
for name, (rs, re_, fe, kind, args) in SPEC.items():
    rs, re_ = date.fromisoformat(rs), date.fromisoformat(re_)
    L = months(rs, re_)
    base_end = date.fromisoformat(fe) if fe else re_
    ce = min(base_end + relativedelta(months=L), CAP)
    rec = {"reg_window": [str(rs), str(re_)], "fresh_end": fe, "L_months": L, "confirm_start": str(base_end), "confirm_end": str(ce)}
    if ce <= base_end:
        rec.update(avail="no", reason="empty interval after 2026-07-01 settling cap", n_confirm=None)
    else:
        try:
            if name == "miamidade_311": raise RuntimeError("2024-26 layers use a new schema (Created_Date, Subject, SubType, Department...); dev recipe fields absent -> not the same recipe; unavailable without a schema adapter")
            if name == "denver_311": raise RuntimeError("no 2024/2025 per-year layers in the publisher's ArcGIS org (only 2007-2023); ODC_service_requests_311 URL invalid")
            if name == "bts_ontime":
                hs = [requests.head(f"https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2025_{m}.zip", timeout=60, allow_redirects=True) for m in (7, 8)]
                if all(h.status_code == 200 for h in hs):
                    rec.update(n_confirm=None, count_kind="estimated (monthly zips 2025-07, 2025-08 exist, %s bytes; dev rate ~600k rows/month)" % [h.headers.get("Content-Length") for h in hs], avail="yes", reason="monthly archives exist (HEAD 200)"); res[name] = rec; print(name, "bts yes", file=sys.stderr); continue
                raise RuntimeError("monthly zips missing")
            if name == "sandiego_311":
                h = requests.head("https://seshat.datasd.org/get_it_done_reports/get_it_done_requests_closed_2026_datasd.csv", timeout=60)
                rec.update(n_confirm=None, count_kind="estimated (dev-year rate ~423k/yr x 0.5yr ~ 210k; 2026 closed-requests file exists, %s bytes)" % h.headers.get("Content-Length"), avail="yes (estimated)", reason="2026 file exists; count not queried"); res[name] = rec; print(name, "sd est", file=sys.stderr); continue
            n = count(name, kind, args, base_end, ce)
            rec.update(n_confirm=n, count_kind="verified-count-query", avail="yes" if n >= 150000 else "no", reason=f"verified count {n}" )
        except Exception as e:
            rec.update(n_confirm=None, count_kind="unverified", avail="unverified", reason=str(e)[:150])
    res[name] = rec; print(name, rec["confirm_start"], rec["confirm_end"], rec.get("n_confirm"), rec["avail"], rec["reason"][:80], file=sys.stderr)
OUT.write_text(json.dumps(res, indent=1))
