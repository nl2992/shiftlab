"""Shared script helpers: ledger append, output dirs."""

import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "paper3" / "joint"
LEDGER = (
    ROOT / "papers" / "paper3_cost_aware_adaptation" / "2026_programme" / "ledger" / "joint.jsonl"
)


def git_sha():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def ledger(stage, config, results=None, wall=None, note=""):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "git_sha": git_sha(),
        "git_dirty": True,
        "workstream": "A_joint",
        "stage": stage,
        "config": config,
        "results": results,
        "wall_clock_s": wall,
        "note": note,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=float) + "\n")


def log(msg):
    print(msg, flush=True)
