"""Freeze registry: sha256 of frontier / finalists / selector, checked before confirmation seeds are drawn."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FREEZE = ROOT / "outputs/hgxh2c/FREEZE.json"
KEYS = ("frontier", "finalists", "selector")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_freeze(fp=None):
    fp = Path(fp or FREEZE)
    return json.loads(fp.read_text("utf-8")) if fp.exists() else {}


def freeze(key, path, fp=None):
    assert key in KEYS, key
    fp = Path(fp or FREEZE)
    d = read_freeze(fp)
    d[key] = {"path": str(path), "sha256": sha256_file(path), "utc": datetime.now(UTC).isoformat()}
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(d, indent=2), "utf-8")
    return d[key]


def require_frozen(keys, fp=None):
    d = read_freeze(fp)
    for k in keys:
        if k not in d:
            raise RuntimeError(f"FREEZE missing: {k}")
        p = Path(d[k]["path"])
        p = p if p.is_absolute() else ROOT / p
        if not p.exists() or sha256_file(p) != d[k]["sha256"]:
            raise RuntimeError(f"FREEZE hash mismatch or file missing: {k} ({p})")
    return d


def confirm_seeds_allowed(fp=None):
    """Stage 4 guard: confirmation seeds may be drawn only after frontier and finalists are frozen."""
    require_frozen(["frontier", "finalists"], fp)
    return True
