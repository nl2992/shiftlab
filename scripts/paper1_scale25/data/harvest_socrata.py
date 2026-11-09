"""WS-A discovery: harvest Socrata catalog metadata (names, columns, licence, update times).

Metadata only; no label statistics are computed. Output: outputs/paper1_scale25/data/socrata_catalog.json
"""
import json, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper1_scale25/data"
OUT.mkdir(parents=True, exist_ok=True)
QUERIES = ["311 service requests", "service requests closed date", "code enforcement cases", "building permits",
           "inspections", "crime incidents", "traffic crashes", "parking citations", "police calls for service",
           "fire incidents", "animal shelter intake outcome", "complaints", "work orders", "potholes",
           "customer service requests", "311 cases", "citizen requests", "restaurant inspections",
           "ems incidents", "permit applications"]
res = {}
for q in QUERIES:
    for off in range(0, 400, 100):
        try:
            r = requests.get("https://api.us.socrata.com/api/catalog/v1",
                             params={"q": q, "only": "datasets", "limit": 100, "offset": off}, timeout=90)
            r.raise_for_status()
        except Exception as e:
            print("fail", q, off, e, file=sys.stderr); break
        rs = r.json().get("results", [])
        if not rs: break
        for x in rs:
            rid = x["resource"]
            key = (x["metadata"]["domain"], rid["id"])
            res["%s|%s" % key] = {
                "domain": key[0], "id": rid["id"], "name": rid["name"], "updatedAt": rid.get("data_updated_at"),
                "createdAt": rid.get("createdAt"), "columns": rid.get("columns_field_name", []),
                "ctypes": rid.get("columns_datatype", []),
                "license": (x["metadata"].get("license") or ""), "attribution": rid.get("attribution"),
                "views": rid.get("page_views", {}).get("page_views_total", 0), "query": q,
                "link": x.get("permalink")}
        time.sleep(0.3)
(OUT / "socrata_catalog.json").write_text(json.dumps(list(res.values()), indent=0))
print(len(res))
