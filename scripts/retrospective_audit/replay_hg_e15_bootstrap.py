"""Replay the archived HG confirmation analyzer on a temporary copy of e15 seeds."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BRANCH = ROOT.parent / "branch-research-shiftlab-mandate-gap-closure-2026-10-30"
SOURCE = BRANCH / "outputs/gap_closure/e15_confirm"
ANALYZER = BRANCH / "scripts/gap/analyze_confirmation.py"
SPEC = BRANCH / "configs/gap_closure/frozen_confirmation_v1.json"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/HG_E15_BOOTSTRAP_REPLAY.json"
SOURCE_HASHES = {
    "scripts/gap/analyze_confirmation.py": "5d28895d65bce011f2113ed5b36a8d042434c74a4d12221b587831a3d16d83b4",
    "configs/gap_closure/frozen_confirmation_v1.json": "53c44ac1480179a78ec63f6dcab2c89e2025b4137561a6d5f36f281d61b9f9fa",
    "outputs/gap_closure/e15_confirm/perseed.parquet": "9741a566f427cadd4c7a44826460e78c6df803e731f7fa44b252265d6f9f0eaa",
}


def run() -> dict[str, object]:
    for name, expected_hash in SOURCE_HASHES.items():
        if hashlib.sha256((BRANCH / name).read_bytes()).hexdigest() != expected_hash:
            raise AssertionError(f"e15 replay input hash mismatch: {name}")
    with tempfile.TemporaryDirectory(prefix="shiftlab_hg_e15_") as temp:
        work = Path(temp)
        output = work / "outputs/gap_closure/e15_confirm"
        output.mkdir(parents=True)
        (work / "docs/sota_gap_closure").mkdir(parents=True)
        shutil.copyfile(SOURCE / "perseed.parquet", output / "perseed.parquet")
        # The archived analyzer imports a simulator module whose Unix-only
        # resource dependency is unused in this analysis-only replay.
        (work / "resource.py").write_text("RUSAGE_SELF = 0\n", encoding="utf-8")
        env = dict(os.environ)
        env["CONFIRM_CFG"] = str(SPEC)
        env["PYTHONPATH"] = os.pathsep.join((str(work), str(BRANCH / "src")))
        result = subprocess.run(
            [sys.executable, "-B", str(ANALYZER)],
            cwd=work,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise RuntimeError(result.stderr[-3000:])
        actual = pd.read_csv(output / "comparisons.csv")
    expected = pd.read_csv(SOURCE / "comparisons.csv")
    if list(actual.columns) != list(expected.columns) or len(actual) != 30:
        raise AssertionError("e15 comparison schema or row mismatch")
    string_cols = ["A", "B", "metric"]
    if not actual[string_cols].equals(expected[string_cols]):
        raise AssertionError("e15 comparison row identity mismatch")
    numeric = [col for col in actual if col not in string_cols]
    errors = {}
    for col in numeric:
        left = actual[col].to_numpy(dtype=float)
        right = expected[col].to_numpy(dtype=float)
        if not np.allclose(left, right, rtol=0, atol=1e-12, equal_nan=True):
            raise AssertionError(f"e15 replay mismatch: {col}")
        errors[col] = float(np.nanmax(np.abs(left - right)))
    return {
        "scope": "Archived-source analyzer replay on stored e15 seeds; no fresh simulator or independent statistical method",
        "verified_source_hashes": SOURCE_HASHES,
        "comparison_rows": len(actual),
        "max_absolute_error_by_column": errors,
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["comparison_rows"], result["max_absolute_error_by_column"])
