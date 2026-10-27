"""Append a verified seed-overlap correction to the frozen Q2 dev artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_dev_v1"
CORRECTION = ROOT / "papers/shiftguard_unified/target_scout_fixed_split_seed_overlap_correction.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest["configuration"]
    dev_start = int(config["seed_offset"])
    dev_end = int(config["seed_end_inclusive"])
    prior_start, prior_end = 20_265_000, 20_265_999
    if max(dev_start, prior_start) > min(dev_end, prior_end):
        raise RuntimeError("registered seed ranges no longer overlap")
    overlap = [max(dev_start, prior_start), min(dev_end, prior_end)]
    note = {
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "status": "provenance_correction_recorded",
        "development_seed_range": [dev_start, dev_end],
        "overlapping_markov_null_seed_range": [prior_start, prior_end],
        "overlap_inclusive": overlap,
        "overlap_count": overlap[1] - overlap[0] + 1,
        "markov_null_protocol": "docs/scout_context_policy_markov_null_protocol.md",
        "markov_null_manifest": "outputs/scout_context_policy_markov_null_1000/reports/manifest.json",
        "dgp_configurations_differ": True,
        "within_run_matched_contrasts_affected": False,
        "independent_across_experiments": False,
        "correction_document": CORRECTION.relative_to(ROOT).as_posix(),
        "correction_sha256": digest(CORRECTION),
        "annotation_script_sha256": digest(Path(__file__).resolve()),
    }
    report_path = OUTPUT / "results.md"
    report = report_path.read_text(encoding="utf-8")
    if "Seed provenance correction (2026-10-26)" not in report:
        raise RuntimeError("expected correction is absent from results.md")
    manifest["provenance_correction"] = note
    manifest["artifacts"]["results.md"] = digest(report_path)
    verification_path = OUTPUT / "verification.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    verification["provenance_correction"] = note
    verification_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    manifest["verification"] = verification
    manifest["artifacts"]["verification.json"] = digest(verification_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(note, indent=2))


if __name__ == "__main__":
    main()
