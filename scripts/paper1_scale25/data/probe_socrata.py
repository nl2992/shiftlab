"""WS-A discovery: metadata-only probe of Socrata candidates (row counts per window and date range).

For each catalog entry with a created-like and a closed-like date column, count rows in the
fixed DEV [2023-07-01,2025-07-01) and CONFIRM [2025-07-01,2026-07-01) periods. Counts only; no
label statistic is requested. Output: outputs/paper1_scale25/data/socrata_probe.json (resumable).
"""
import json, re, sys, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper1_scale25/data"
cat = json.load(open(OUT / "socrata_catalog.json"))
pf = OUT / "socrata_probe.json"
done = json.load(open(pf)) if pf.exists() else {}
op = re.compile(r"(creat|open|request|submit|report|receiv|issue|filed|intake|incident|arriv|date_time|datetime|start|dispatch)", re.I)
cl = re.compile(r"(clos|resol|complet|finish|outcome|dispos|final|end|expire)", re.I)
DEV = ("2023-07-01T00:00:00", "2025-07-01T00:00:00")
CON = ("2025-07-01T00:00:00", "2026-07-01T00:00:00")
todo = []
for d in cat:
    if not d["updatedAt"] or d["updatedAt"] < "2026-07-01": continue
    ts = [a for a, t in zip(d["columns"], d["ctypes"]) if t in ("Calendar date", "Date") and not a.startswith(":")]
    o = [a for a in ts if op.search(a)]; k = [a for a in ts if cl.search(a) and a not in o[:1]]
    if o and k: todo.append((d, o[0], k[0]))
print(len(todo), "to probe", file=sys.stderr)
def q(dom, rid, sel, where=None):
    p = {"$select": sel}
    if where: p["$where"] = where
    r = requests.get(f"https://{dom}/resource/{rid}.json", params=p, timeout=60)
    r.raise_for_status(); return r.json()
n = 0
for d, o, k in todo:
    key = f"{d['domain']}|{d['id']}"
    if key in done: continue
    rec = {"name": d["name"], "domain": d["domain"], "id": d["id"], "open_col": o, "close_col": k, "views": d["views"],
           "license": d["license"], "updatedAt": d["updatedAt"]}
    try:
        mm = q(d["domain"], d["id"], f"min({o}) as mn, max({o}) as mx")[0]
        rec["min_ts"], rec["max_ts"] = mm.get("mn"), mm.get("mx")
        rec["n_dev"] = int(q(d["domain"], d["id"], "count(*) as n", f"{o}>='{DEV[0]}' AND {o}<'{DEV[1]}'")[0]["n"])
        rec["n_conf"] = int(q(d["domain"], d["id"], "count(*) as n", f"{o}>='{CON[0]}' AND {o}<'{CON[1]}'")[0]["n"])
    except Exception as e:
        rec["error"] = str(e)[:160]
    done[key] = rec; n += 1
    if n % 20 == 0:
        pf.write_text(json.dumps(done, indent=0)); print(n, file=sys.stderr)
    time.sleep(0.2)
pf.write_text(json.dumps(done, indent=0))
print("done", len(done))
