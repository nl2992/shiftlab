"""Re-run the frozen EIA 2026 experiment and verify aggregate reproducibility."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/shiftguard_unified/independent_real_data/eia_2026_v1"
ARCHIVE = ROOT / "data/raw/eia/EBA.zip"
READINESS = ROOT / "data/reports/eia_2026_holdout_readiness.json"
PROTOCOL = ROOT / "papers/shiftguard_unified/eia_2026_out_of_time_confirmation_protocol_v1.md"
RUNNER = ROOT / "scripts/run_eia_2026_out_of_time_confirmation.py"
AUDIT_SCRIPT = ROOT / "scripts/audit_eia_2026_holdout_readiness.py"
VERIFICATION = OUTPUT / "reproducibility_verification.json"
METRIC_FILES = ("summary.csv", "monthly_metrics.csv", "paired_block_intervals.csv", "results.md")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compare_summary_frames(expected: pd.DataFrame, actual: pd.DataFrame) -> float:
    """Require exact metric equality while reporting machine-dependent fit-time drift."""
    if "fit_seconds" not in expected.columns or "fit_seconds" not in actual.columns:
        raise ValueError("Summary lacks the recorded fit_seconds runtime field")
    assert_frame_equal(
        expected.drop(columns="fit_seconds"),
        actual.drop(columns="fit_seconds"),
        check_exact=True,
        check_dtype=True,
    )
    left = pd.to_numeric(expected["fit_seconds"], errors="raise").to_numpy(dtype=float)
    right = pd.to_numeric(actual["fit_seconds"], errors="raise").to_numpy(dtype=float)
    if not all(math.isfinite(value) and value > 0 for value in (*left, *right)):
        raise ValueError("Fit-time values must be finite and positive")
    return float(abs(left - right).max(initial=0.0))


def verify(
    replay_dir: Path | None = None, *, overwrite_verification: bool = False
) -> dict[str, Any]:
    if VERIFICATION.exists() and not overwrite_verification:
        raise FileExistsError(f"Refusing to overwrite verification record: {VERIFICATION}")
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    code_hashes = {
        "source_archive_sha256": sha256(ARCHIVE),
        "readiness_report_sha256": sha256(READINESS),
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(RUNNER),
        "readiness_audit_script_sha256": sha256(AUDIT_SCRIPT),
    }
    for key, value in code_hashes.items():
        if manifest.get(key) != value:
            raise ValueError(f"Frozen input hash changed: {key}")
    if manifest.get("raw_rows_or_predictions_persisted") is not False:
        raise ValueError("The source manifest does not confirm aggregate-only outputs")
    for filename in METRIC_FILES:
        expected_hash = manifest["outputs_sha256"].get(filename)
        if expected_hash != sha256(OUTPUT / filename):
            raise ValueError(f"Frozen output checksum failed: {filename}")

    temporary_dir = None
    if replay_dir is None:
        temporary_dir = tempfile.TemporaryDirectory(prefix="shiftguard_eia_2026_replay_")
        replay_dir = Path(temporary_dir.name) / "replay"
    else:
        replay_dir = replay_dir.resolve()
        if not (replay_dir / "manifest.json").is_file():
            raise FileNotFoundError(f"Replay manifest is missing from {replay_dir}")
    if temporary_dir is not None:
        subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--output-dir",
                str(replay_dir),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
    replay = json.loads((replay_dir / "manifest.json").read_text(encoding="utf-8"))
    for key in (
        "source_archive_sha256",
        "readiness_report_sha256",
        "protocol_sha256",
        "runner_sha256",
        "readiness_audit_script_sha256",
        "data_source_code_hash",
        "torch_version",
        "python_version",
        "policies",
        "delay_hours",
        "model_and_policy_constants",
    ):
        if replay.get(key) != manifest.get(key):
            raise ValueError(f"Replayed provenance mismatch: {key}")
    if replay.get("device") != manifest.get("device"):
        raise ValueError("Replay used a different computation device")
    if manifest.get("device") != "cuda":
        raise ValueError("This protocol's verification requires the recorded CUDA path")

    expected_summary = pd.read_csv(OUTPUT / "summary.csv")
    replay_summary = pd.read_csv(replay_dir / "summary.csv")
    max_fit_time_difference = compare_summary_frames(expected_summary, replay_summary)
    for filename in ("monthly_metrics.csv", "paired_block_intervals.csv", "results.md"):
        if sha256(OUTPUT / filename) != sha256(replay_dir / filename):
            raise ValueError(f"Replayed output differs: {filename}")

    summary = pd.read_csv(OUTPUT / "summary.csv")
    intervals = pd.read_csv(OUTPUT / "paired_block_intervals.csv")
    if len(summary) != 24 or len(intervals) != 54:
        raise ValueError("Unexpected EIA result dimensions")
    if set(summary["domain_id"]) != {"CISO", "ERCO"}:
        raise ValueError("Unexpected authority set")
    if set(summary["delay_hours"].astype(int)) != {0, 24, 168}:
        raise ValueError("Unexpected feedback delay set")
    if set(summary["policy"]) != {"frozen", "weekly", "monthly", "error_trigger"}:
        raise ValueError("Unexpected policy set")
    if set(intervals["n_populated_blocks"].astype(int)) != {42}:
        raise ValueError("Expected 42 populated weekly blocks in each paired interval")

    report: dict[str, Any] = {
        "status": "passed_frozen_eia_2026_cuda_reproducibility_audit",
        "verification_scope": "same frozen implementation re-executed in a separate process; exact aggregate metrics, monthly table, paired block intervals, and report reproduced; no tuning",
        "input_sha256": code_hashes,
        "frozen_output_sha256": {filename: sha256(OUTPUT / filename) for filename in METRIC_FILES},
        "reproduced_dimensions": {
            "summary_rows": len(summary),
            "paired_interval_rows": len(intervals),
            "monthly_metric_rows": len(pd.read_csv(OUTPUT / "monthly_metrics.csv")),
            "authorities": sorted(summary["domain_id"].unique().tolist()),
            "delay_hours": sorted(summary["delay_hours"].astype(int).unique().tolist()),
            "policies": sorted(summary["policy"].unique().tolist()),
            "populated_168_hour_blocks": 42,
        },
        "exact_metric_reproduction": True,
        "exact_monthly_interval_and_report_reproduction": True,
        "max_absolute_fit_runtime_difference_seconds": max_fit_time_difference,
        "interpretation": "This establishes deterministic reproducibility of the frozen event-time forecasting/resource comparison, not prospective availability, electricity-system utility, or independent deployment replication.",
    }
    VERIFICATION.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replay-dir",
        type=Path,
        help="Reuse a completed replay directory; otherwise run the frozen CUDA experiment now.",
    )
    parser.add_argument(
        "--overwrite-verification",
        action="store_true",
        help="Replace only the audit JSON after a successful reproduction; experiment outputs are never overwritten.",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            verify(args.replay_dir, overwrite_verification=args.overwrite_verification),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
