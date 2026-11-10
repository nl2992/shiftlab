"""Manifest of the 12 new-source DEV builds (protocol 07a section 3), seed base 2026111000 (not the confirm base)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NEW = ["edmonton_311", "winnipeg_311", "mc311_montgomery", "calgary_311", "nyc_ems_response",
       "nyc_fire_response", "montgomery_police_dispatch", "divvy_chicago", "capitalbikeshare_dc",
       "epa_aqi_county", "ghcn_us_rain", "eia930_pooled"]  # fmt: skip
ds = []
for n in NEW:
    r = json.loads((ROOT / f"docs/paper1_scale25/dev_builds/{n}.json").read_text(encoding="utf-8"))
    assert r["eligible"], n
    ds.append({"name": n, "episodes": r["episodes"], "sealed_path": r["sealed"]["path"],
               "array_content_sha256": r["sealed"]["array_content_sha256"],
               "eligibility": {"eligible": True}})  # fmt: skip
out = ROOT / "outputs/paper1_scale25/c1/dev_manifest.json"
out.write_text(json.dumps({"seed_base": 2026111000, "datasets": ds}, indent=1))
print([(d["name"], d["episodes"]) for d in ds])
