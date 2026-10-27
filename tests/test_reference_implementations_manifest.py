"""Tests for the reference implementation provenance manifest."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from verify_reference_implementations import _sha256, verify

ROOT = Path(__file__).resolve().parents[1]


def test_reference_manifest_hashes_match_current_sources_and_artifacts():
    assert verify(ROOT) == []


def test_reference_manifest_detects_modified_frozen_file(tmp_path: Path):
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("changed", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "references": {"example": {"source": {"path": "frozen.txt", "sha256": "0" * 64}}},
            }
        ),
        encoding="utf-8",
    )

    errors = verify(tmp_path, Path("manifest.json"))

    assert len(errors) == 1
    assert "SHA-256 mismatch for frozen.txt" in errors[0]


def test_reference_manifest_hash_is_independent_of_text_line_endings(tmp_path: Path):
    frozen = tmp_path / "frozen.py"
    expected = b"first line\nsecond line\n"
    frozen.write_bytes(b"first line\r\nsecond line\r\n")

    assert _sha256(frozen) == hashlib.sha256(expected).hexdigest()


def test_reference_manifest_rejects_conflicting_hashes_for_same_file(tmp_path: Path):
    frozen = tmp_path / "frozen.txt"
    frozen.write_text("stable", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "references": {
                    "first": {"path": "frozen.txt", "sha256": "0" * 64},
                    "second": {"path": "frozen.txt", "sha256": "1" * 64},
                },
            }
        ),
        encoding="utf-8",
    )

    errors = verify(tmp_path, Path("manifest.json"))

    assert any("conflicting expected SHA-256 values" in error for error in errors)
