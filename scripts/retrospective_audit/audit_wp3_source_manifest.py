"""Check the archived WP3 source manifest against its recorded Git tree."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT.parent / "shift-research-starter" / "outputs" / "data_efficient_prescreen_20"
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "WP3_SOURCE_PROVENANCE.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", f"{revision}:{path}"], cwd=ROOT)


def run() -> dict[str, object]:
    manifest = json.loads((ARCHIVE / "manifest.json").read_text(encoding="utf-8"))
    launch = json.loads((ARCHIVE / "launch.json").read_text(encoding="utf-8"))
    analysis = json.loads((ARCHIVE / "analysis" / "manifest.json").read_text(encoding="utf-8"))
    head = manifest["git_head"]
    records = []
    for raw_name, expected in manifest["source_sha256"].items():
        name = raw_name.replace("\\", "/")
        committed = git_blob(head, name)
        current = (ROOT.parent / "shift-research-starter" / name).read_bytes()
        commit_match = digest(committed) == expected
        current_match = digest(current) == expected
        crlf_only = current_match and current.replace(b"\r\n", b"\n") == committed
        if not commit_match and not crlf_only:
            raise AssertionError(f"Unexplained source mismatch: {name}")
        records.append(
            {
                "path": name,
                "recorded_sha256": expected,
                "git_blob_exact": commit_match,
                "archived_bytes_are_crlf_git_blob": crlf_only and not commit_match,
                "current_file_exact": current_match,
            }
        )

    output_mismatches = [
        name
        for name, expected in manifest["outputs_sha256"].items()
        if digest((ARCHIVE / name).read_bytes()) != expected
    ]
    if output_mismatches:
        raise AssertionError(f"Output hash mismatches: {output_mismatches}")
    script = git_blob("0ec8f6a", "scripts/analyze_data_efficient_prescreen.py")
    analysis_hash_match = digest(script) == analysis["analysis_source_sha256"]
    if not analysis_hash_match:
        raise AssertionError("Archived analysis hash differs from first tracked script")
    return {
        "run_head": head,
        "run_started_at_utc": launch["started_at_utc"],
        "run_recorded_at_utc": manifest["recorded_at_utc"],
        "source_count": len(records),
        "git_blob_exact_count": sum(r["git_blob_exact"] for r in records),
        "crlf_only_count": sum(r["archived_bytes_are_crlf_git_blob"] for r in records),
        "current_file_exact_count": sum(r["current_file_exact"] for r in records),
        "current_file_mismatches": [r["path"] for r in records if not r["current_file_exact"]],
        "crlf_only_paths": [r["path"] for r in records if r["archived_bytes_are_crlf_git_blob"]],
        "run_output_hash_count": len(manifest["outputs_sha256"]),
        "run_output_hash_mismatches": output_mismatches,
        "analysis_script_untracked_at_launch": (
            "?? scripts/analyze_data_efficient_prescreen.py" in launch["dirty_paths"]
        ),
        "analysis_hash_matches_first_tracked_blob": analysis_hash_match,
        "scope": "Archived physical-source bytes versus run Git tree; no event-level replay",
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        result["source_count"],
        "source hashes:",
        result["git_blob_exact_count"],
        "exact Git blobs,",
        result["crlf_only_count"],
        "CRLF-only;",
        result["run_output_hash_count"],
        "output hashes checked",
    )
