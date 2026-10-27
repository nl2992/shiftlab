"""Hash Git-reported worktree changes into a reproducible snapshot manifest."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
OUTPUT = REPOSITORY / "papers" / "shiftguard_unified" / "worktree_snapshot_2026-10-26.json"


def run_git(*arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPOSITORY,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


def main() -> None:
    head = run_git("rev-parse", "HEAD").decode().strip()
    branch = run_git("branch", "--show-current").decode().strip()
    records = [
        record
        for record in run_git("status", "--porcelain=v1", "-z", "--untracked-files=all").split(
            b"\0"
        )
        if record
    ]
    output_relative = OUTPUT.relative_to(REPOSITORY).as_posix()
    file_entries: list[dict[str, str | int]] = []

    for record in records:
        status = record[:2].decode("ascii")
        relative_path = record[3:].decode("utf-8", errors="surrogateescape")
        path = REPOSITORY / relative_path
        if path.resolve() == OUTPUT.resolve():
            continue
        if "R" in status or "C" in status:
            raise ValueError("Rename/copy entries need explicit source-path handling")

        entry: dict[str, str | int] = {
            "path": Path(relative_path).as_posix(),
            "index_status": status[0],
            "worktree_status": status[1],
        }
        if path.is_symlink():
            target = str(path.readlink())
            entry.update(
                {
                    "state": "symlink",
                    "target": target,
                    "sha256": hashlib.sha256(target.encode()).hexdigest(),
                }
            )
        elif path.is_file():
            payload = path.read_bytes()
            entry.update(
                {
                    "state": "present",
                    "size_bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        elif path.is_dir():
            nested_head: str | None = None
            nested_changes: list[dict[str, str | int]] = []
            try:
                nested_head = run_git("-C", str(path), "rev-parse", "HEAD").decode().strip()
                nested_records = [
                    item
                    for item in run_git(
                        "-C",
                        str(path),
                        "status",
                        "--porcelain=v1",
                        "-z",
                        "--untracked-files=all",
                    ).split(b"\0")
                    if item
                ]
            except subprocess.CalledProcessError:
                nested_records = []

            for nested_record in nested_records:
                nested_status = nested_record[:2].decode("ascii")
                nested_relative = nested_record[3:].decode("utf-8", errors="surrogateescape")
                nested_path = path / nested_relative
                if "R" in nested_status or "C" in nested_status:
                    raise ValueError(
                        f"Rename/copy entry in nested repository {relative_path}: {nested_relative}"
                    )
                change: dict[str, str | int] = {
                    "path": Path(nested_relative).as_posix(),
                    "status": nested_status,
                }
                if nested_path.is_symlink():
                    target = str(nested_path.readlink())
                    change.update(
                        {
                            "state": "symlink",
                            "target": target,
                            "sha256": hashlib.sha256(target.encode()).hexdigest(),
                        }
                    )
                elif nested_path.is_file():
                    payload = nested_path.read_bytes()
                    change.update(
                        {
                            "state": "present",
                            "size_bytes": len(payload),
                            "sha256": hashlib.sha256(payload).hexdigest(),
                        }
                    )
                else:
                    change["state"] = "missing_or_non_file"
                nested_changes.append(change)

            entry.update(
                {
                    "state": "nested_git_repository" if nested_head else "directory",
                    "nested_repository_head": nested_head or "",
                    "nested_repository_changes": sorted(
                        nested_changes, key=lambda item: str(item["path"])
                    ),
                }
            )
        else:
            entry["state"] = "missing_or_non_file"
        file_entries.append(entry)

    lock_path = REPOSITORY / "uv.lock"
    manifest = {
        "snapshot_schema": "shiftlab-worktree-snapshot-v1",
        "captured_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "repository_head": head,
        "branch": branch,
        "expanded_changed_path_count_excluding_snapshot": len(file_entries),
        "files": sorted(file_entries, key=lambda item: str(item["path"])),
        "snapshot_file_excluded_from_own_hash_list": output_relative,
        "dependency_lock": {
            "path": "uv.lock",
            "sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        },
        "scope_note": (
            "Hashes cover changed, staged, unstaged, and untracked non-ignored "
            "files reported by git status --porcelain=v1 -z --untracked-files=all. "
            "Nested Git repositories record their HEAD and dirty-file hashes. "
            "This is a working-tree snapshot, not a commit or clean release."
        ),
    }
    OUTPUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Snapshotted {len(file_entries)} changed paths at HEAD {head[:12]}.")


if __name__ == "__main__":
    main()
