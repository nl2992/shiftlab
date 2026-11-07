#!/usr/bin/env python3
"""Audit Sprint 2 candidate registry coverage and cited evidence files.

This checks structural lineage, shared registry/ledger claims, and cited evidence-file existence.
It does not re-compute metrics, validate a theorem, or provide an independent scientific review.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FAMILIES = {"H": "h", "R": "r", "T": "t", "P": "p"}
TRACKS = ("track_E", "track_R", "track_V")
REQUIRED_CANDIDATE_FIELDS = (
    "implementation",
    "run_config",
    "seed_manifest",
    "results_artifact",
    *TRACKS,
    "ablation",
    "disposition",
    "next_action",
)


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def family_entries(letter: str) -> list[dict[str, Any]]:
    ledger = load_json(ROOT / f"docs/sprint2/family_{FAMILIES[letter]}/ledger.json")
    if isinstance(ledger, list):
        return ledger
    entries = ledger.get("candidates", [])
    if not isinstance(entries, list):
        raise ValueError(f"{letter} ledger candidates is not a list")  # noqa: TRY004
    return entries


def audit() -> dict[str, Any]:
    registry = load_json(ROOT / "docs/sprint2/candidates.json")
    expected = {f"{family}{i}" for family in FAMILIES for i in range(1, 7)}
    failures: list[str] = []
    if set(registry) != expected:
        failures.append(
            f"candidate ids differ: missing={sorted(expected - set(registry))}, extra={sorted(set(registry) - expected)}"
        )
    missing_tracks: list[str] = []
    blank_status: list[str] = []
    missing_artifacts: list[dict[str, str]] = []
    missing_ledger_fields: list[dict[str, str]] = []
    missing_manifests: list[dict[str, str]] = []
    missing_provenance_records: list[dict[str, str]] = []
    declared_provenance_gaps: list[dict[str, str]] = []
    for cid in sorted(expected & set(registry)):
        candidate = registry[cid]
        if not str(candidate.get("status", "")).strip():
            blank_status.append(cid)
        for track in TRACKS:
            if not str(candidate.get(track, "")).strip():
                missing_tracks.append(f"{cid}.{track}")
        artifacts = candidate.get("results_artifact", [])
        if isinstance(artifacts, str):
            artifacts = [part.strip() for part in artifacts.split(";")]
        for artifact in artifacts:
            artifact = str(artifact).strip().strip("`")
            if not artifact or any(char in artifact for char in "*{}"):
                continue
            if (
                artifact.startswith(("outputs/", "docs/", "scripts/", "tests/"))
                and not (ROOT / artifact).exists()
            ):
                missing_artifacts.append({"candidate": cid, "path": artifact})

    ledger_ids: dict[str, list[str]] = {}
    registry_cells_without_family_source: list[str] = []
    registry_ledger_mismatches: list[dict[str, str]] = []
    for family in FAMILIES:
        entries = family_entries(family)
        ids = [str(entry.get("id")) for entry in entries]
        ledger_ids[family] = ids
        expected_family = {f"{family}{i}" for i in range(1, 7)}
        if set(ids) != expected_family:
            failures.append(
                f"{family} ledger ids differ: missing={sorted(expected_family - set(ids))}, extra={sorted(set(ids) - expected_family)}"
            )
        for entry in entries:
            cid = str(entry.get("id"))
            if cid not in registry:
                continue
            for field in REQUIRED_CANDIDATE_FIELDS:
                if field not in entry:
                    missing_ledger_fields.append({"candidate": cid, "field": field})
                    continue
                value = entry[field]
                # next_action may be null when the disposition is final for this
                # sprint; all other required fields must contain useful content.
                if field == "next_action" and value is None:
                    continue
                if value is None or value == "" or value == [] or value == {}:
                    missing_ledger_fields.append({"candidate": cid, "field": field})
            seed_manifest = entry.get("seed_manifest")
            if not isinstance(seed_manifest, dict):
                missing_ledger_fields.append(
                    {"candidate": cid, "field": "seed_manifest (must be structured)"}
                )
                manifest_paths = []
            else:
                manifest_paths = seed_manifest.get("manifests", [])
                provenance_record = seed_manifest.get("provenance_record")
                if provenance_record:
                    p = str(provenance_record).strip().strip("`")
                    if not (ROOT / p).exists():
                        missing_provenance_records.append({"candidate": cid, "path": p})
                elif not manifest_paths:
                    missing_ledger_fields.append(
                        {"candidate": cid, "field": "seed_manifest.manifests or provenance_record"}
                    )
                provenance_status = seed_manifest.get("provenance_status")
                if provenance_status not in {"complete", "partial"}:
                    missing_ledger_fields.append(
                        {
                            "candidate": cid,
                            "field": "seed_manifest.provenance_status (complete|partial)",
                        }
                    )
                if provenance_status == "partial":
                    if not provenance_record:
                        missing_ledger_fields.append(
                            {
                                "candidate": cid,
                                "field": "partial seed provenance requires provenance_record",
                            }
                        )
                    declared_provenance_gaps.append(
                        {"candidate": cid, "note": str(seed_manifest.get("note", ""))}
                    )
            for manifest in manifest_paths:
                path = str(manifest).strip().strip("`")
                if path and not (ROOT / path).exists():
                    missing_manifests.append({"candidate": cid, "path": path})
            # Every field shared by the family ledger and candidate registry is
            # a mirrored claim. Keep the user-facing matrix synchronized with
            # the more detailed family evidence record.
            for field in entry:
                # Registry run_config may summarize additional completion runs
                # that the original family ledger predates; it is not a mirror.
                if field == "run_config":
                    continue
                if field in registry[cid] and entry[field] != registry[cid][field]:
                    registry_ledger_mismatches.append(
                        {
                            "candidate": cid,
                            "field": field,
                            "ledger": repr(entry[field])[:300],
                            "registry": repr(registry[cid][field])[:300],
                        }
                    )
                    if field in TRACKS:
                        registry_cells_without_family_source.append(f"{cid}.{field}")

    if missing_tracks:
        failures.append(f"blank Track cells: {missing_tracks}")
    if blank_status:
        failures.append(f"blank statuses: {blank_status}")
    if missing_artifacts:
        failures.append(f"missing artifact paths: {missing_artifacts}")
    if missing_ledger_fields:
        failures.append(f"missing required ledger fields: {missing_ledger_fields}")
    if missing_manifests:
        failures.append(f"missing seed manifest paths: {missing_manifests}")
    if missing_provenance_records:
        failures.append(f"missing provenance sidecar paths: {missing_provenance_records}")
    if registry_cells_without_family_source:
        failures.append(
            f"family/registry Track-cell mismatches: {registry_cells_without_family_source}"
        )
    if registry_ledger_mismatches:
        failures.append(f"family/registry shared-field mismatches: {registry_ledger_mismatches}")

    return {
        "structural_audit": "PASS" if not failures else "FAIL",
        "registry_candidate_count": len(registry),
        "expected_candidate_count": len(expected),
        "family_ledger_ids": ledger_ids,
        "blank_track_cells": missing_tracks,
        "blank_statuses": blank_status,
        "missing_artifacts": missing_artifacts,
        "missing_ledger_fields": missing_ledger_fields,
        "missing_seed_manifests": missing_manifests,
        "missing_provenance_records": missing_provenance_records,
        "declared_provenance_gaps": declared_provenance_gaps,
        "provenance_audit": "PARTIAL"
        if declared_provenance_gaps
        else ("PASS" if not missing_manifests else "FAIL"),
        "track_cell_mismatches": registry_cells_without_family_source,
        "registry_ledger_mismatches": registry_ledger_mismatches,
        "limitations": [
            "Checks candidate schema, referenced-manifest existence, shared-field equality, artifact path existence, and registry coverage; does not recompute metrics or verify that each manifest semantically covers its candidate.",
            "A populated Track cell does not mean the track is applicable or complete; read its explicit n/a/partial qualification.",
            "No independent review, selection adjustment, theorem proof, or data-validity claim is established by this audit.",
        ],
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.out:
        out = args.out if args.out.is_absolute() else ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered)
    print(rendered, end="")
    return 0 if result["structural_audit"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
