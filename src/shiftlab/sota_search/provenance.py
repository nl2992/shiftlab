"""Capture a clean committed source closure and installed dependency versions."""

from __future__ import annotations

import hashlib
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def source_provenance(repo: Path) -> tuple[dict, list[Path]]:
    scopes = [
        "src",
        "scripts/sota_search",
        "configs/sota_search",
        "docs/sota_synthetic_search",
        "pyproject.toml",
        "uv.lock",
    ]
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", *scopes],
        cwd=repo,
        encoding="utf-8",
    )
    if dirty.strip():
        raise RuntimeError(
            "commit research source and protocol before launching a registered batch"
        )
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=repo, encoding="utf-8"
    ).strip()
    if branch != "research/shiftlab-sota-synthetic-search-2026-10-29":
        raise RuntimeError("synthetic search must remain in its isolated research branch")
    tracked = subprocess.check_output(
        ["git", "ls-files", "-z", "--", *scopes], cwd=repo, encoding="utf-8"
    ).split("\0")
    files = [repo / path for path in sorted(filter(None, tracked))]
    source_hash = hashlib.sha256()
    for path in files:
        source_hash.update(path.relative_to(repo).as_posix().encode() + b"\0")
        source_hash.update(hashlib.sha256(path.read_bytes()).digest())
    metadata = {
        "code_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, encoding="utf-8"
        ).strip(),
        "source_hash": source_hash.hexdigest(),
        "source_hash_scheme": "sorted_posix_path_NUL_sha256_file_bytes_v2",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {
                name: version(name) for name in ("numpy", "scipy", "psutil", "pandas", "pydantic")
            },
        },
    }
    return metadata, files


def archive_source(destination: Path, repo: Path, files: list[Path]) -> None:
    with ZipFile(destination, "x", compression=ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(repo).as_posix())
