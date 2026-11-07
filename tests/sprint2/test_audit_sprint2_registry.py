import json
from pathlib import Path

from scripts.sota_sprint import audit_sprint2_registry as registry_audit


def _write_fixture(root: Path, *, missing_manifest: bool = False) -> None:
    (root / "docs/sprint2").mkdir(parents=True)
    (root / "docs/sprint2/provenance.json").write_text("{}\n")
    registry = {}
    for family, suffix in (("H", "h"), ("R", "r"), ("T", "t"), ("P", "p")):
        entries = []
        for i in range(1, 7):
            cid = f"{family}{i}"
            seed_manifest = {
                "manifests": [],
                "provenance_record": "docs/sprint2/provenance.json",
                "provenance_status": "partial",
                "note": "fixture declared gap",
            }
            if missing_manifest and cid == "H1":
                seed_manifest = {
                    "manifests": ["outputs/missing/manifest.json"],
                    "seed_bases": ["1"],
                    "provenance_status": "complete",
                    "note": "fixture",
                }
            entry = {
                "id": cid,
                "status": "screened",
                "implementation": "fixture.py",
                "run_config": ["fixture command"],
                "seed_manifest": seed_manifest,
                "results_artifact": ["fixture artifact"],
                "track_E": "fixture E",
                "track_R": "n/a",
                "track_V": "fixture V",
                "ablation": "fixture ablation",
                "disposition": "fixture disposition",
                "next_action": None,
            }
            entries.append(entry)
            registry[cid] = {
                key: entry[key]
                for key in ("status", "results_artifact", "track_E", "track_R", "track_V")
            }
        (root / f"docs/sprint2/family_{suffix}").mkdir(parents=True)
        (root / f"docs/sprint2/family_{suffix}/ledger.json").write_text(
            json.dumps({"candidates": entries})
        )
    (root / "docs/sprint2/candidates.json").write_text(json.dumps(registry))


def test_audit_accepts_complete_schema_and_reports_declared_provenance_gaps(tmp_path, monkeypatch):
    _write_fixture(tmp_path)
    monkeypatch.setattr(registry_audit, "ROOT", tmp_path)

    result = registry_audit.audit()

    assert result["structural_audit"] == "PASS"
    assert result["provenance_audit"] == "PARTIAL"
    assert len(result["declared_provenance_gaps"]) == 24
    assert result["missing_ledger_fields"] == []
    assert result["missing_provenance_records"] == []


def test_audit_fails_for_a_missing_manifest_reference(tmp_path, monkeypatch):
    _write_fixture(tmp_path, missing_manifest=True)
    monkeypatch.setattr(registry_audit, "ROOT", tmp_path)

    result = registry_audit.audit()

    assert result["structural_audit"] == "FAIL"
    assert result["missing_seed_manifests"] == [
        {"candidate": "H1", "path": "outputs/missing/manifest.json"}
    ]
