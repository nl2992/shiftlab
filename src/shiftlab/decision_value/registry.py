"""Append-only JSONL run registry."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[2]
REGISTRY = ROOT / "outputs" / "decision_value" / "manifests" / "run_registry.jsonl"


def source_hashes() -> dict:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PKG.glob("*.py"))}


def git_state() -> dict:
    def run(*a):
        return subprocess.run(
            ["git", *a], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()

    return {"commit": run("rev-parse", "HEAD"), "dirty": bool(run("status", "--porcelain"))}


def versions() -> dict:
    import numpy
    import pandas
    import scipy

    return {
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
    }


def append_run(
    run_id: str,
    config: dict,
    seeds: dict,
    n_episodes: int,
    runtime_s: float,
    outputs: list,
    confirmation: bool = False,
    registry: Path | None = None,
) -> dict:
    entry = {
        "run_id": run_id,
        "utc_time": datetime.now(UTC).isoformat(),
        "git": git_state(),
        "source_sha256": source_hashes(),
        "versions": versions(),
        "config": config,
        "seeds": seeds,
        "n_episodes": n_episodes,
        "hardware": {"platform": platform.platform(), "cpu_count": os.cpu_count()},
        "runtime_s": round(runtime_s, 2),
        "outputs": [str(o) for o in outputs],
        "stage": "confirmation" if confirmation else "development",
    }
    path = Path(registry or REGISTRY)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf8") as f:  # append-only
        f.write(json.dumps(entry, sort_keys=True, default=str) + "\n")
    return entry
