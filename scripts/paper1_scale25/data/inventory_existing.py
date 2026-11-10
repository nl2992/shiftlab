"""WS-A: inventory of the 44 existing C4 recipes -> outputs/paper1_scale25/data/existing_inventory.json.

Reads recipes (META), build records, registrations and sealed arrays (hash verification only; no
statistic of the sealed arrays is produced here), and confirm_avail.json.
"""

import hashlib
import importlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
MAIN = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter")
FRESHWT = Path("C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-paper1-eqsdp-2026-11-08")
sys.path.insert(0, str(ROOT / "scripts/qsg_methods_search"))
OUT = ROOT / "outputs/paper1_scale25/data"


def ahash(*arrs):
    h = hashlib.sha256()
    for a in arrs:
        h.update(np.ascontiguousarray(a).tobytes())
    return h.hexdigest()


reg = {}
for f, batch in [
    ("c4_registration.json", "batch1"),
    ("c4_registration_batch2.json", "batch2"),
    ("c4_registration_batchF.json", "batchF"),
]:
    for d in json.load(open(ROOT / "docs/qsg_methods_search" / f))["datasets"]:
        reg[d["name"]] = {**d, "batch": batch}
fresh = {
    d["name"]: d for d in json.load(open(ROOT / "docs/paper1_eqsdp/fresh_registration.json"))["datasets"]
}

U = "-"
# domain, task family, parent_source_id, org, audit note (from c4_build_audit.md and the recipes)
INFO = {
    "la_crime": ("public-safety", "crime-case-status", "lapd_crime_2020_2024", "City of Los Angeles / LAPD",
                 "pass; label has a maturity trend (status != IC at freeze). Dataset 2nrs-mtv8 holds no rows after 2024-12 (count 0 for 2025-26)"),
    "sf_311": ("municipal-311", "311-closure-speed", "sfgov_311", "City and County of San Francisco", "pass"),
    "nyc_collisions": ("public-safety", "crash-injury", "nyc_collisions", "City of New York", "pass"),
    "boston_311": ("municipal-311", "311-closure-speed", "boston_311", "City of Boston", "pass"),
    "kc_311": ("municipal-311", "311-closure-speed", "kcmo_311", "Kansas City MO", "pass; department_work_group is the documented default per request type"),
    "montgomery_traffic": ("public-safety", "traffic-stop-citation", "montgomerycountymd_traffic", "Montgomery County MD", "pass with caveat (stop-condition flags); window already ends 2026-07"),
    "dallas_311": ("municipal-311", "311-closure-speed", "dallas_311", "City of Dallas", "pass"),
    "dc_311": ("municipal-311", "311-closure-speed", "dc_311", "District of Columbia", "pass with caveat (org/priority treated as intake-time)"),
    "philly_311": ("municipal-311", "311-closure-speed", "philly_311", "City of Philadelphia", "pass with caveat (agency_responsible routed at intake)"),
    "austin_311": ("municipal-311", "311-closure-speed", "austin_311", "City of Austin", "pass"),
    "cincinnati_311": ("municipal-311", "311-closure-speed", "cincinnati_311", "City of Cincinnati", "pass"),
    "nola_311": ("municipal-311", "311-closure-speed", "nola_311", "City of New Orleans", "pass"),
    "oakland_311": ("municipal-311", "311-closure-speed", "oakland_311", "City of Oakland", "pass; fresh window ineligible (27 episodes)"),
    "sandiego_311": ("municipal-311", "311-closure-speed", "sandiego_getitdone", "City of San Diego", "pass (Referred counts as resolved)"),
    "sacramento_311": ("municipal-311", "311-closure-speed", "sacramento_311", "City of Sacramento", "pass"),
    "baltimore_311": ("municipal-311", "311-closure-speed", "baltimore_311", "City of Baltimore", "pass"),
    "miamidade_311": ("municipal-311", "311-closure-speed", "miamidade_311", "Miami-Dade County", "pass with caveat (case_owner routed at intake; empty issue_description)"),
    "minneapolis_311": ("municipal-311", "311-closure-speed", "minneapolis_311", "City of Minneapolis", "pass with caveat (TITLE treated as intake-time)"),
    "louisville_311": ("municipal-311", "311-closure-speed", "louisville_311", "Louisville Metro", "pass"),
    "chicago_311": ("municipal-311", "311-closure-speed", "chicago_311", "City of Chicago", "pass"),
    "denver_311": ("municipal-311", "311-closure-speed", "denver_311", "City and County of Denver", "pass with caveat (agency/division routed at intake)"),
    "pittsburgh_311": ("municipal-311", "311-closure-speed", "pittsburgh_311", "City of Pittsburgh (WPRDC)", "pass with caveat (closure propagates from parent to grouped child tickets)"),
    "bts_ontime": ("transport", "flight-delay", "bts_ontime", "US DOT BTS", "pass (schedule-time features only)"),
    "sf_building_permits": ("permits-enforcement", "permit-outcome", "sf_dbi_permits", "City and County of San Francisco", "pass (filing-time fields only); same city as sf_311, different department"),
    "chicago_traffic_crashes": ("public-safety", "crash-damage", "chicago_crashes", "City of Chicago", "pass (scene-condition fields only)"),
    "dallas_animal_shelter": ("health-animal", "shelter-outcome", "dallas_animal_shelter", "City of Dallas", "pass with caveat (re-impounds present); same city as dallas_311, different department"),
    "austin_animal": ("health-animal", "shelter-outcome", "austin_animal_center", "City of Austin", "EXCLUDED by pre-opening audit: sex_upon_outcome recorded at resolution (rule 3)"),
    "chicago_crimes": ("public-safety", "crime-arrest", "chicago_crimes", "City of Chicago", U),
    "eia_ba": ("energy", "demand-forecast-error", "eia_930", "US EIA", U),
    "nyc_tlc_taxi": ("transport", "taxi-tip", "nyc_tlc", "NYC TLC", U),
    "uk_police": ("public-safety", "street-crime-outcome", "uk_police", "UK police.uk", U),
    "seattle_spd": ("public-safety", "police-report", "seattle_spd", "City of Seattle", U),
    "nyc_311": ("municipal-311", "311-closure-speed", "nyc_311", "City of New York", U),
    "nyc_restaurant_inspections": ("health-inspection", "inspection-grade", "nyc_restaurant", "NYC DOHMH", U),
    "chicago_taxi": ("transport", "taxi-tip", "chicago_taxi", "City of Chicago", "fetch hit the 1M-row limit; true window end earlier than declared"),
    "citibike": ("transport", "bike-ebike", "nyc_citibike", "Citi Bike / Lyft", U),
    "buffalo_311": ("municipal-311", "311-closure-speed", "buffalo_311", "City of Buffalo", U),
    "detroit_311": ("municipal-311", "311-closure-speed", "detroit_311", "City of Detroit", U),
    "cambridge_311": ("municipal-311", "311-closure-speed", "cambridge_311", "City of Cambridge MA", U),
    "gainesville_311": ("municipal-311", "311-closure-speed", "gainesville_311", "City of Gainesville", U),
    "chicago_food_inspections": ("health-inspection", "inspection-result", "chicago_food", "City of Chicago", U),
    "seattle_building_permits": ("permits-enforcement", "permit-outcome", "seattle_permits", "City of Seattle", U),
    "cfpb_complaints": ("finance-economics", "complaint-timely-response", "cfpb_complaints", "CFPB", U),
    "sonoma_animal_shelter": ("health-animal", "shelter-outcome", "sonoma_shelter", "County of Sonoma", U),
}
avail = json.load(open(OUT / "confirm_avail.json"))
rows = []
for name, (dom, fam, parent, org, audit) in INFO.items():
    m = importlib.import_module("c4_sources." + name)
    b = json.load(open(ROOT / f"docs/qsg_methods_search/c4_builds/{name}.json"))
    r = {
        "dataset_id": name, "domain": dom, "task_family": fam, "parent_source_id": parent, "org": org, "audit": audit,
        "meta": {k: m.META.get(k) for k in ("url", "license", "publisher", "task", "label", "delay", "window", "features_note")},
        "num": b["num"], "cat": b["cat"], "n_after_filter": b["n_after_filter"], "episodes": b["episodes"],
        "eligible_build": b["eligible"], "gates": b["gates"], "validation": b["validation"],
        "ts_bounds": b["ts_bounds"], "subsample": b["subsample"],
    }
    if name in reg:
        d = reg[name]
        sp = MAIN / "data/c4_sealed" / f"{name}.npz"
        z = np.load(sp)
        h = ahash(z["l0"], z["l1"], z["starts"])
        r.update(registered=True, batch=d["batch"], registered_hash=d["array_content_sha256"], recomputed_hash=h,
                 hash_ok=(h == d["array_content_sha256"]), sealed_path=str(sp).replace("\\", "/"),
                 registered_episodes=d["episodes"])
    else:
        r.update(registered=False)
    if name in fresh:
        d = fresh[name]
        sp = FRESHWT / "data/c4_sealed" / f"{name}__fresh.npz"
        r.update(fresh_window=d["window"], fresh_episodes=d["episodes"], fresh_eligible=d["eligibility"]["eligible"],
                 fresh_validation=d["eligibility"]["validation"], fresh_registered_hash=d.get("array_content_sha256"),
                 fresh_sealed_path=str(sp).replace("\\", "/"))
        if sp.exists() and d.get("array_content_sha256"):
            z = np.load(sp)
            h = ahash(z["l0"], z["l1"], z["starts"])
            r.update(fresh_recomputed_hash=h, fresh_hash_ok=(h == d["array_content_sha256"]))
        else:
            r.update(fresh_hash_ok=None)
    r["confirm"] = avail.get(name)
    rows.append(r)
(OUT / "existing_inventory.json").write_text(json.dumps(rows, indent=1, default=str))
print(len(rows), "registered:", sum(r["registered"] for r in rows), "hash_ok:", sum(bool(r.get("hash_ok")) for r in rows),
      "fresh:", sum("fresh_window" in r for r in rows), "fresh_hash_ok:", sum(bool(r.get("fresh_hash_ok")) for r in rows))
for r in rows:
    if r.get("registered") and not r["hash_ok"]:
        print("HASH MISMATCH", r["dataset_id"])
    if "fresh_window" in r and not r.get("fresh_hash_ok"):
        print("FRESH HASH", r["dataset_id"], r.get("fresh_hash_ok"))
