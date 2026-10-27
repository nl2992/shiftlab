"""Verify the hash-pinned ShiftGuard reference implementation snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

MANIFEST = Path("papers/shiftguard_unified/reference_implementations_v1.json")


def _entries(value: Any) -> Iterator[dict[str, str]]:
    """Yield every {path, sha256} entry recursively from a JSON value."""
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield value
        for child in value.values():
            yield from _entries(child)
    elif isinstance(value, list):
        for child in value:
            yield from _entries(child)


def verify(root: Path, manifest_path: Path = MANIFEST) -> list[str]:
    """Return validation errors; an empty list means every frozen hash matches."""
    manifest_file = root / manifest_path
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read manifest {manifest_path}: {exc}"]

    if manifest.get("schema_version") != 1:
        return ["unsupported or missing schema_version"]
    references = manifest.get("references")
    if not isinstance(references, dict) or not references:
        return ["manifest has no reference implementations"]

    errors: list[str] = []
    expected_by_path: dict[str, str] = {}
    for entry in _entries(references):
        relative = entry["path"]
        expected = entry["sha256"].lower()
        if len(expected) != 64 or any(char not in "0123456789abcdef" for char in expected):
            errors.append(f"invalid SHA-256 value for {relative}")
            continue
        previous = expected_by_path.setdefault(relative, expected)
        if previous != expected:
            errors.append(f"conflicting expected SHA-256 values for {relative}")

    for relative, expected in expected_by_path.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing frozen file: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"SHA-256 mismatch for {relative}: expected {expected}, got {actual}")
    if not expected_by_path:
        errors.append("manifest contains no frozen file hashes")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = verify(args.root.resolve())
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: all hash-pinned reference files match ({MANIFEST.as_posix()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
