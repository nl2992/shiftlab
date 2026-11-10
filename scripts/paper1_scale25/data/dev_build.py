"""WS-A wrapper around scripts/qsg_methods_search/c4_build.py for scale-25 DEV windows.

Backward-compatible: c4_build.py and c4_sources/* are untouched. New recipes live in
scripts/paper1_scale25/data/sources/<id>.py and keep the c4_sources interface (META, fetch, load,
NUM, CAT, WINDOW). Outputs: data/scale25_dev/<id>.npz (sealed test losses), build record
docs/paper1_scale25/dev_builds/<id>.json, raw data data/raw/scale25/<id>/.

Usage: python dev_build.py <id> [--fetch]
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/qsg_methods_search"))
sys.path.insert(0, str(ROOT / "scripts/paper1_scale25/data"))
import c4_build  # noqa: E402

DEV_NPZ = ROOT / "data/scale25_dev"
DEV_REC = ROOT / "docs/paper1_scale25/dev_builds"
DEV_RAW = ROOT / "data/raw/scale25"


def build(name: str, fetch: bool) -> dict:
    mod = importlib.import_module(f"sources.{name}")
    sys.modules[f"c4_sources.{name}"] = mod  # c4_build resolves recipes by this key
    c4_build.RAW, c4_build.SEALED, c4_build.RECORDS = DEV_RAW, DEV_NPZ, DEV_REC
    rec = c4_build.build(name, fetch)
    p = DEV_REC / f"{name}.json"
    r = json.loads(p.read_text())
    if "sealed" in r:
        r["sealed"]["path"] = f"data/scale25_dev/{name}.npz"
    r["builder"] = "scripts/paper1_scale25/data/dev_build.py (wraps c4_build.build; unchanged gates)"
    p.write_text(json.dumps(r, indent=1, default=str) + "\n")
    return r


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--fetch", action="store_true")
    a = ap.parse_args()
    r = build(a.name, a.fetch)
    print(json.dumps({k: r[k] for k in ("name", "n", "validation", "gates", "eligible", "episodes")}, indent=1))
