"""Run the registered EIA real-data validity protocol (docs/eia_real_data_validity_protocol.md).

Refuses to start unless the freeze record exists and every recorded hash matches the file on disk.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROTOCOL_REL = "docs/eia_real_data_validity_protocol.md"
FREEZE_REL = "docs/eia_real_data_validity_freeze.json"
STREAMS_REL = "outputs/eia_paired_reserve/streams.parquet"
OUT_REL = "outputs/eia_real_data_validity"
FREEZE_KEYS = ("protocol_sha256", "code_sha256", "streams_sha256", "freeze_utc")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def check_freeze(root: Path, freeze_path: Path | None = None) -> dict:
    """Return the freeze record after verifying protocol, code and stream hashes under ``root``."""
    freeze_path = Path(freeze_path) if freeze_path is not None else root / FREEZE_REL
    if not freeze_path.is_file():
        raise FileNotFoundError(f"freeze record missing: {freeze_path}")
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    missing = [key for key in FREEZE_KEYS if key not in freeze]
    if missing:
        raise ValueError(f"freeze record lacks keys {missing}")
    expected = {PROTOCOL_REL: freeze["protocol_sha256"], STREAMS_REL: freeze["streams_sha256"]}
    expected.update(freeze["code_sha256"])
    for rel, want in expected.items():
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(f"frozen file missing: {rel}")
        if digest(path) != want:
            raise ValueError(f"hash mismatch for {rel}: file changed since freeze")
    return freeze


def check_output_dir(out: Path) -> None:
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out}")


def run_analyses(streams: list, replicates: dict | None = None) -> dict:
    """Run analyses (a)-(c) on in-memory streams; ``replicates`` overrides counts (tests only)."""
    from shiftlab.dive.eia_validity_analysis import (
        collect_paths,
        injected_analysis,
        null_analysis,
        unmodified_analysis,
    )

    reps = {"null": 1000, "rerun": 4000, "unmodified": 200, "injected": 200}
    reps.update(replicates or {})
    paths = collect_paths(streams)
    null_df, decision = null_analysis(paths, reps["null"], reps["rerun"])
    return {
        "null_cells": null_df,
        "unmodified": unmodified_analysis(paths, reps["unmodified"]),
        "injected": injected_analysis(paths, reps["injected"]),
        "decision": decision,
    }


def main() -> None:
    from shiftlab.dive.eia_paired_reserve import read_streams

    start = time.perf_counter()
    freeze = check_freeze(ROOT)
    out = ROOT / OUT_REL
    check_output_dir(out)
    head_start = git("rev-parse", "HEAD")
    dirty_start = git("status", "--porcelain").splitlines()
    started = datetime.now(UTC).isoformat()
    streams = read_streams(ROOT / "outputs/eia_paired_reserve")
    result = run_analyses(streams)
    out.mkdir(parents=True, exist_ok=True)
    for name in ("null_cells", "unmodified", "injected"):
        result[name].to_csv(out / f"{name}.csv", index=False)
    (out / "decision.json").write_text(
        json.dumps(result["decision"], indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "freeze_record": freeze,
        "started_at_utc": started,
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "git_head": head_start,
        "git_head_at_end": git("rev-parse", "HEAD"),
        "dirty_paths": dirty_start,
        "dirty_paths_at_end": git("status", "--porcelain").splitlines(),
        "command": subprocess.list2cmdline(sys.argv),
        "runtime_seconds": time.perf_counter() - start,
        "versions": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pandas": pd.__version__,
        },
        "outputs_sha256": {p.name: digest(p) for p in sorted(out.iterdir()) if p.is_file()},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["decision"], indent=2))


if __name__ == "__main__":
    main()
