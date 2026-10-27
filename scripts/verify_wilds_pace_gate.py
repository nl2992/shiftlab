"""Verify the aggregate artifacts and execution-source receipt for WILDS PACE."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(output: Path) -> list[str]:
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    for name, expected in manifest["artifacts"].items():
        actual = sha256(output / name)
        if actual != expected:
            failures.append(f"artifact hash mismatch: {name}")

    snapshots = output / "execution_sources"
    source_checks = {
        "evaluate_wilds_pace_gate.py": manifest["protocol"]["runner_sha256"],
        "evaluate_wilds_candidate_selection.py": manifest["protocol"]["candidate_selector_sha256"],
        "wilds_pace_gate_protocol_v1.md": manifest["protocol"]["sha256"],
    }
    for name, expected in source_checks.items():
        if sha256(snapshots / name) != expected:
            failures.append(f"execution-source hash mismatch: {name}")
    audit = manifest.get("post_run_audit", {})
    verifier_hash = audit.get("execution_source_snapshots", {}).get("posthoc_verifier_sha256")
    if verifier_hash and sha256(snapshots / "verify_wilds_pace_gate.py") != verifier_hash:
        failures.append("execution-source hash mismatch: verify_wilds_pace_gate.py")

    decisions = manifest["decisions"]
    pace = decisions["pace"]
    if pace["crossing_at_evaluated_instance"] is not None or pace["promoted"]:
        failures.append("PACE record is inconsistent with the reported no-crossing outcome")
    expected_log_e = pace["candidate_wins"] * math.log(1 + pace["lambda"]) + pace[
        "incumbent_wins"
    ] * math.log(1 - pace["lambda"])
    if not math.isclose(pace["log_e_at_stop"], expected_log_e, abs_tol=1e-12):
        failures.append("PACE terminal log-wealth does not match discordant-pair counts")
    if pace["log_e_at_stop"] >= pace["log_threshold"]:
        failures.append("PACE terminal wealth crosses the promotion threshold")

    fixed_n = decisions["fixed_n_mcnemar"]
    if fixed_n["promoted"] != (fixed_n["p_value_one_sided"] <= fixed_n["alpha"]):
        failures.append("fixed-N promotion flag does not match the recorded p-value")
    if fixed_n["candidate_wins"] + fixed_n["incumbent_wins"] != fixed_n["discordant_pairs"]:
        failures.append("fixed-N discordant-pair counts do not add up")
    if pace["candidate_wins"] + pace["incumbent_wins"] != pace["discordant_pairs"]:
        failures.append("PACE discordant-pair counts do not add up")
    if decisions["scout_certification_article_overlap"] != 0:
        failures.append("scout and certification article samples overlap")
    if (
        decisions["scout_articles"] + decisions["certification_articles"]
        != manifest["dataset"]["validation_article_count"]
    ):
        failures.append("validation article allocation does not match manifest count")

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/shiftguard_unified/real_data_development/wilds_pace_gate_v1"),
    )
    args = parser.parse_args()
    failures = verify(args.output)
    if failures:
        raise SystemExit("verification failed: " + "; ".join(failures))
    print("verification=passed; artifacts=4; execution_sources=3; aggregate_checks=passed")


if __name__ == "__main__":
    main()
