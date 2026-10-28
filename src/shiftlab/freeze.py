"""Executable freeze records for Stage 1 confirmatory runs.

A freeze record lists a protocol file and every code and configuration file a run depends on, each
with its SHA-256 over LF-normalised bytes, so the record is portable across Windows and POSIX
checkouts. A confirmatory runner calls :func:`require_freeze` before touching registered seeds: it
refuses to run when any listed file differs from the record or when the working tree has
uncommitted changes to a listed file.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def file_sha256(path: Path) -> str:
    """SHA-256 of a file with CRLF normalised to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write_freeze(
    record_path: Path,
    *,
    experiment: str,
    protocol: str,
    files: list[str],
    seed_blocks: list[str],
    note: str = "",
    repo_root: Path = REPO_ROOT,
) -> dict:
    """Hash the protocol and dependent files and write the freeze record."""
    listed = [protocol, *files]
    missing = [f for f in listed if not (repo_root / f).is_file()]
    if missing:
        raise FileNotFoundError(f"cannot freeze missing files: {missing}")
    record = {
        "experiment": experiment,
        "frozen_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": _git(["rev-parse", "HEAD"], repo_root),
        "hash_rule": "sha256 over CRLF->LF normalised bytes",
        "protocol": protocol,
        "seed_blocks": seed_blocks,
        "sha256": {f: file_sha256(repo_root / f) for f in listed},
        "note": note,
    }
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
    return record


def check_freeze(record_path: Path, repo_root: Path = REPO_ROOT) -> list[str]:
    """Return every reason the current checkout does not match the freeze record."""
    record = json.loads(record_path.read_text(encoding="utf-8"))
    problems = []
    for rel, frozen in record["sha256"].items():
        path = repo_root / rel
        if not path.is_file():
            problems.append(f"missing: {rel}")
        elif file_sha256(path) != frozen:
            problems.append(f"changed since freeze: {rel}")
    dirty = _git(["status", "--porcelain", "--", *record["sha256"]], repo_root)
    if dirty:
        problems.append(f"uncommitted changes to frozen files:\n{dirty}")
    return problems


def require_freeze(record_path: Path, repo_root: Path = REPO_ROOT) -> dict:
    """Raise unless the checkout matches the freeze record; return the record."""
    problems = check_freeze(record_path, repo_root)
    if problems:
        raise RuntimeError("freeze check failed:\n" + "\n".join(problems))
    return json.loads(record_path.read_text(encoding="utf-8"))


def _git(args: list[str], repo_root: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, text=True, check=True
    ).stdout.strip()
