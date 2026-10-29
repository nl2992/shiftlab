"""Read-only integrity check for the preserved ShiftGuard research platform anchors."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "docs/switching_platform_manifest_v1.json"
RUN = ROOT / "outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1"
VERIFICATION = RUN / "analysis_v3/verification.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify() -> dict[str, object]:
    manifest = json.loads(PLATFORM.read_text(encoding="utf-8"))
    recorded = json.loads(VERIFICATION.read_text(encoding="utf-8"))
    checked: dict[Path, str] = {}
    errors: list[str] = []

    def check(relative: str, expected: str) -> None:
        path = ROOT / Path(relative.replace("\\", "/"))
        if not path.is_file():
            errors.append(f"missing: {relative}")
            return
        actual = checked[path] if path in checked else checked.setdefault(path, sha256(path))
        if actual.lower() != expected.lower():
            errors.append(f"sha256 mismatch: {relative}")

    for entry in manifest["entries"]:
        check(entry["path"], entry["sha256"])

    if recorded.get("status") != "passed":
        errors.append("saved independent analysis status is not passed")
    if recorded.get("metric_rows") != 7200 or recorded.get("profile_method_cells") != 72:
        errors.append("saved confirmation row/cell counts do not match the frozen design")
    if (
        recorded.get("learner_event_rows") != 23_040_000
        or recorded.get("evaluator_event_rows") != 23_040_000
    ):
        errors.append("saved event-log row counts do not match the frozen design")
    if recorded.get("max_label_use") != 640 or recorded.get("primary_contrasts") != 22:
        errors.append("saved cap/primary-contrast checks do not match the frozen design")

    for relative, expected in recorded.get("source_sha256_verified", {}).items():
        check(relative, expected)
    for group in ("artifact_sha256", "analysis_outputs_sha256"):
        for relative, expected in recorded.get(group, {}).items():
            check(relative, expected)

    if errors:
        raise RuntimeError("platform verification failed:\n- " + "\n- ".join(errors))
    return {
        "status": "passed",
        "selected_platform_anchors": len(manifest["entries"]),
        "historical_confirmation_sources_and_artifacts": len(checked) - len(manifest["entries"]),
        "unique_files_hashed": len(checked),
        "historical_analysis_status": recorded["status"],
        "metric_rows": recorded["metric_rows"],
        "profile_method_cells": recorded["profile_method_cells"],
        "learner_event_rows": recorded["learner_event_rows"],
        "evaluator_event_rows": recorded["evaluator_event_rows"],
        "maximum_label_use": recorded["max_label_use"],
        "primary_contrasts": recorded["primary_contrasts"],
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
