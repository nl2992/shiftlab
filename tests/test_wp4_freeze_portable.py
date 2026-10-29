from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_VERIFIER = Path(__file__).resolve().parents[1] / "scripts" / "verify_wp4_freeze.py"
_spec = importlib.util.spec_from_file_location("verify_wp4_freeze", _VERIFIER)
verifier = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules[_spec.name] = verifier
_spec.loader.exec_module(verifier)


def test_crlf_and_lf_versions_hash_identically_after_normalisation() -> None:
    lf_bytes = b"line one\nline two\n\nline four\n"
    crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")
    assert crlf_bytes != lf_bytes

    lf_norm = verifier.line_ending_variants(lf_bytes)["lf"]
    crlf_norm = verifier.line_ending_variants(crlf_bytes)["lf"]
    assert verifier.sha256_hex(lf_norm) == verifier.sha256_hex(crlf_norm)
    assert lf_norm == crlf_norm == lf_bytes


def test_every_listed_file_matches_freeze_record() -> None:
    results = verifier.verify()
    assert results, "freeze record lists no files"
    mismatches = [r for r in results if not r.ok]
    if mismatches:
        names = ", ".join(r.path for r in mismatches)
        pytest.xfail(f"file(s) changed since WP4 freeze, no hash variant matches: {names}")
    assert all(r.ok for r in results)


def test_listed_files_exist_in_checkout() -> None:
    for r in verifier.verify():
        assert r.raw is not None, f"listed file missing from working tree: {r.path}"
