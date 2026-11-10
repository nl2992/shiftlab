"""Protocol C1 step 2: confirmation-window builds (docs/paper1_scale25/07a_PROTOCOL_C1_V1_22.md).

Same recipe, label, features, delay and C4 gates as the dev builds; only the window (and the
publisher's per-vintage file/layer constants that the window implies) change. The builder never
computes or prints test-window statistics (c4_build.build records only validation gates).

Outputs: data/scale25_confirm/<id>.npz (gitignored), docs/paper1_scale25/confirm_builds/<id>.json,
raw data data/raw/scale25_confirm/<id>/ (gitignored).

Usage: python confirm_build.py <id> [--fetch]
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/qsg_methods_search"))
sys.path.insert(0, str(ROOT / "scripts/paper1_scale25/data"))
import c4_build

OUT_NPZ = ROOT / "data/scale25_confirm"
OUT_REC = ROOT / "docs/paper1_scale25/confirm_builds"
OUT_RAW = ROOT / "data/raw/scale25_confirm"
NEW_WIN = ("2025-07-01", "2026-07-01")
ORDER = [
    ("boston_311", "2025-01-01", "2026-01-01"),
    ("philly_311", "2025-07-01", "2026-07-01"),
    ("sacramento_311", "2025-01-01", "2026-01-01"),
    ("baltimore_311", "2025-01-01", "2025-05-01"),
    ("louisville_311", "2025-01-01", "2026-07-01"),
    ("chicago_311", "2025-01-01", "2026-01-01"),
    ("chicago_traffic_crashes", "2023-01-01", "2025-01-01"),
    ("bts_ontime", "2025-07-01", "2025-09-01"),
    ("dc_311", "2026-01-01", "2026-07-01"),
    ("sandiego_311", "2026-01-01", "2026-07-01"),
    *[(n, *NEW_WIN) for n in (
        "edmonton_311", "winnipeg_311", "mc311_montgomery", "calgary_311", "nyc_ems_response",
        "nyc_fire_response", "montgomery_police_dispatch", "divvy_chicago", "capitalbikeshare_dc",
        "epa_aqi_county", "ghcn_us_rain", "eia930_pooled")],
]  # fmt: skip
NEW = {o[0] for o in ORDER[10:]}
BOSTON_2025 = (
    "https://data.boston.gov/dataset/8048697b-ad64-4bfc-b090-ee00169f2323/resource/"
    "9d7c2214-4709-478a-a2e8-fb2020a5bb94/download/lagan_311_open_data_2025_rvsd3.csv"
)
DC_2026 = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/ServiceRequests/FeatureServer/21/query"
LOU = "https://services1.arcgis.com/79kfd2K6fskCAkyg/arcgis/rest/services/"
BALT_2025 = (
    "https://services1.arcgis.com/UWYHeuuJISiGmgXx/ArcGIS/rest/services/"
    "311_Customer_Service_Requests_2025/FeatureServer/0"
)


def fmt_like(old: str, new: str) -> str:
    sep = "T" if "T" in old else " "
    return f"{new}{sep}00:00:00"


def months(a: str, b: str):
    y, m = int(a[:4]), int(a[5:7])
    ye, me = int(b[:4]), int(b[5:7])
    while (y, m) < (ye, me):
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def load_module(name: str, a: str, b: str):
    """Import the recipe module and re-point it at the confirmation window."""
    if name in NEW:
        if name in ("divvy_chicago", "capitalbikeshare_dc"):
            common = importlib.import_module("sources._bikeshare_common")
            common.MONTHS = [f"{y}{m:02d}" for y, m in months(a, b)]
            common.WINDOW = (f"{a}T00:00:00", f"{b}T00:00:00")
        mod = importlib.import_module(f"sources.{name}")
        if name in ("divvy_chicago", "capitalbikeshare_dc"):
            mod = importlib.reload(mod)  # re-run make_module with the patched common constants
        elif hasattr(mod, "CFG"):  # Socrata factory recipes
            from sources._socrata_common import make_module

            vars(mod).update(make_module({**mod.CFG, "window": (f"{a}T00:00:00", f"{b}T00:00:00")}))
        else:  # epa, ghcn, eia930: module-level WINDOW / YEARS
            mod.WINDOW = (f"{a}T00:00:00", f"{b}T00:00:00")
            mod.META = {**mod.META, "window": mod.WINDOW}
            if name == "epa_aqi_county":
                mod.YEARS = (2025, 2026)
            if name == "ghcn_us_rain":
                mod.YEARS = (2025, 2026)
        sys.modules[f"c4_sources.{name}"] = mod
        return mod
    mod = importlib.import_module(f"c4_sources.{name}")
    mod.WINDOW = (fmt_like(mod.WINDOW[0], a), fmt_like(mod.WINDOW[1], b))
    mod.META = {**mod.META, "window": mod.WINDOW}
    if name == "boston_311":
        mod.URL, mod.FILE = BOSTON_2025, "boston311_2025.csv"
        mod.META["url"] = mod.URL
    elif name == "sacramento_311":
        mod.WHERE = f"DateCreated >= timestamp '{mod.WINDOW[0]}' AND DateCreated < timestamp '{mod.WINDOW[1]}'"
    elif name == "baltimore_311":
        mod.LAYER = BALT_2025
        mod.META["url"] = mod.LAYER
        mod.FILE = "baltimore311_2025.csv"

        def fetch(raw, _m=mod):
            import datetime as dt

            lo = (dt.date.fromisoformat(a) - dt.timedelta(days=1)).isoformat()
            hi = (dt.date.fromisoformat(b) + dt.timedelta(days=1)).isoformat()
            where = f"CreatedDate >= TIMESTAMP '{lo} 00:00:00' AND CreatedDate < TIMESTAMP '{hi} 00:00:00'"
            from c4_sources._dl_arcgis import fetch_arcgis

            fetch_arcgis(_m.LAYER, _m.FIELDS, where, "ESRI_OID", raw, _m.FILE, 2000)

        mod.fetch = fetch
    elif name == "louisville_311":
        mod.LAYERS = {
            "2025": LOU + "metro_311_2025/FeatureServer/0",
            "2026": LOU + "metro_311_2026/FeatureServer/0",
        }
        mod.META["url"] = ";".join(mod.LAYERS.values())
    elif name == "bts_ontime":
        mod.MONTHS = list(months(a, b))
    elif name == "dc_311":
        mod.BASE, mod.FILE = DC_2026, "dc311_2026h1.csv"
        mod.META["url"] = mod.BASE
    return mod


def build(name: str, a: str, b: str, fetch: bool) -> dict:
    mod = load_module(name, a, b)
    sys.modules[f"c4_sources.{name}"] = mod
    c4_build.RAW, c4_build.SEALED, c4_build.RECORDS = OUT_RAW, OUT_NPZ, OUT_REC
    c4_build.build(name, fetch)
    p = OUT_REC / f"{name}.json"
    r = json.loads(p.read_text())
    if "sealed" in r:
        r["sealed"]["path"] = f"data/scale25_confirm/{name}.npz"
    r["builder"] = (
        "scripts/paper1_scale25/data/confirm_build.py (wraps c4_build.build; unchanged gates)"
    )
    r["confirm_window"] = [a, b]
    p.write_text(json.dumps(r, indent=1, default=str) + "\n")
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--fetch", action="store_true")
    x = ap.parse_args()
    a, b = next((o[1], o[2]) for o in ORDER if o[0] == x.name)
    try:
        r = build(x.name, a, b, x.fetch)
        print(
            json.dumps(
                {k: r[k] for k in ("name", "n", "validation", "gates", "eligible", "episodes")},
                indent=1,
            )
        )
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        OUT_REC.mkdir(parents=True, exist_ok=True)
        (OUT_REC / f"{x.name}.FAILED.json").write_text(
            json.dumps({"name": x.name, "window": [a, b], "error": repr(e)[:500]}, indent=1) + "\n"
        )
        print(x.name, "FAILED", repr(e)[:300])
        sys.exit(1)
