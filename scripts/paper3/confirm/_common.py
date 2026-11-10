"""Shared helpers for the confirmation runs (registration 04_EXPERIMENT_PROTOCOL.md @2190f95f)."""

import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs" / "paper3" / "confirm"
LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/confirm.jsonl"
REG_SHA = "2190f95f"


def git_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def ledger(hyp, kind, config, results=None, wall=None, note=""):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "git_sha": git_sha(),
        "registration": REG_SHA,
        "hypothesis": hyp,
        "kind": kind,
        "config": config,
        "results": results,
        "wall_clock_s": wall,
        "note": note,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=float) + "\n")
