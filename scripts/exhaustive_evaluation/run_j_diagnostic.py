"""Enforce the existing Candidate J diagnostic cap without editing its source."""

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/exhaustive_evaluation"


def main():
    paths = [
        "scripts/research_risk_approx/benchmark_candidate_j_controller_risk.py",
        "src/shiftlab/dive/risk_preserving_approx/controller_risk_verifier.py",
        "docs/risk_preserving_approx/CANDIDATE_J_RISK_DP_PROTOCOL_V1.md",
    ]
    record = {
        "started_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "timeout_seconds": 120,
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
    }
    target = OUT / "candidate_j_execution.json"
    if target.exists():
        raise FileExistsError("Registered one-shot diagnostic already has an execution record")
    record["status"] = "running"
    target.write_text(json.dumps(record, indent=2), encoding="utf-8")
    env = dict(
        os.environ, PYTHONPATH=str(ROOT / "src"), OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1"
    )
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / paths[0])],
            check=False,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        record.update(
            status="completed" if result.returncode == 0 else "failed", returncode=result.returncode
        )
        (OUT / "candidate_j_stdout.txt").write_text(result.stdout, encoding="utf-8")
        (OUT / "candidate_j_stderr.txt").write_text(result.stderr, encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        record.update(
            status="timeout",
            note="120-second total child-process cap; no risk equality or efficiency gate inferred from timeout",
        )
        (OUT / "candidate_j_stdout.txt").write_bytes(exc.stdout or b"")
        (OUT / "candidate_j_stderr.txt").write_bytes(exc.stderr or b"")
    record["finished_utc"] = datetime.now(UTC).isoformat()
    target.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()
