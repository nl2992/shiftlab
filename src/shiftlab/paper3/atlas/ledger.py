"""Append-only run ledger (ledger/atlas.jsonl)."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/atlas.jsonl"


def git_sha() -> str:
    try:
        s = subprocess.run(  # noqa: PLW1510
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
        d = subprocess.run(  # noqa: PLW1510
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
        ).stdout.strip()
        return s + ("+dirty" if d else "")
    except Exception:  # noqa: BLE001
        return "unknown"


def append(kind: str, config: dict, seeds, status: str, metrics_path: str, note: str = ""):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "git_sha": git_sha(),
        "kind": kind,
        "config_hash": hashlib.sha256(
            json.dumps(config, sort_keys=True, default=str).encode()
        ).hexdigest()[:12],
        "config": config,
        "seeds": seeds,
        "status": status,
        "metrics_path": metrics_path,
        "note": note,
    }
    with open(LEDGER, "a", encoding="utf8") as f:
        f.write(json.dumps(rec, default=str) + "\n")
