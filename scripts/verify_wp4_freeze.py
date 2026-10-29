"""Portable verifier for the WP4 EIA real-data validity freeze record.

The freeze record (docs/eia_real_data_validity_freeze.json) lists SHA-256
hashes of the protocol and code files frozen for WP4. Files are text, but a
checkout may store them with LF or CRLF line endings depending on Git settings
(see .gitattributes: ``* text=auto eol=lf``). A file therefore counts as
matching if ANY of these byte encodings hashes to the frozen value:

  raw         the working-tree bytes exactly as stored
  lf          CRLF -> LF normalised bytes (the Git index form)
  crlf        LF -> CRLF of the normalised bytes (the Windows text form)

The matched variant is reported so that line-ending differences are visible,
not hidden. A file that matches no variant has changed since freeze.

Usage:
    uv run --no-sync python scripts/verify_wp4_freeze.py
Exit status is 0 when every listed file matches, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FREEZE_RECORD = REPO_ROOT / "docs" / "eia_real_data_validity_freeze.json"


@dataclass(frozen=True)
class FileCheck:
    path: str
    frozen: str
    raw: str | None
    lf: str | None
    crlf: str | None
    matched: str | None  # "raw" | "lf" | "crlf" | None

    @property
    def ok(self) -> bool:
        return self.matched is not None


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def line_ending_variants(data: bytes) -> dict[str, bytes]:
    """Return the raw, LF-normalised and CRLF-normalised byte forms of ``data``."""
    lf = data.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return {"raw": data, "lf": lf, "crlf": crlf}


def load_listed_files(record_path: Path = FREEZE_RECORD) -> dict[str, str]:
    """Map each frozen repo-relative path to its frozen SHA-256 hex digest."""
    record = json.loads(record_path.read_text(encoding="utf-8"))
    listed: dict[str, str] = {}
    listed.update(record.get("code_sha256", {}))
    if "protocol_sha256" in record:
        listed["docs/eia_real_data_validity_protocol.md"] = record["protocol_sha256"]
    return listed


def check_file(rel_path: str, frozen: str, repo_root: Path = REPO_ROOT) -> FileCheck:
    full = repo_root / rel_path
    if not full.is_file():
        return FileCheck(rel_path, frozen, None, None, None, None)
    variants = line_ending_variants(full.read_bytes())
    digests = {name: sha256_hex(data) for name, data in variants.items()}
    matched = next((name for name in ("raw", "lf", "crlf") if digests[name] == frozen), None)
    return FileCheck(rel_path, frozen, digests["raw"], digests["lf"], digests["crlf"], matched)


def verify(record_path: Path = FREEZE_RECORD, repo_root: Path = REPO_ROOT) -> list[FileCheck]:
    return [check_file(p, h, repo_root) for p, h in load_listed_files(record_path).items()]


def format_table(results: list[FileCheck]) -> str:
    def short(h: str | None) -> str:
        return h[:16] if h else "MISSING"

    header = f"{'file':<58} {'raw':<18} {'lf':<18} {'crlf':<18} {'frozen':<18} result"
    lines = [header, "-" * len(header)]
    for r in results:
        if r.matched is None and r.raw is None:
            status = "MISSING FILE"
        elif r.matched is None:
            status = "MISMATCH (changed since freeze)"
        else:
            status = f"OK ({r.matched} variant)"
        lines.append(
            f"{r.path:<58} {short(r.raw):<18} {short(r.lf):<18} {short(r.crlf):<18} "
            f"{short(r.frozen):<18} {status}"
        )
    return "\n".join(lines)


def main() -> int:
    results = verify()
    print(format_table(results))
    failures = [r for r in results if not r.ok]
    print()
    print(f"{len(results) - len(failures)}/{len(results)} listed files match the freeze record.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
