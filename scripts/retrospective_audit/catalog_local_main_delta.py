"""Catalog tracked local-main path versions since the initial source census."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "shift-research-starter"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/01a_LOCAL_MAIN_DELTA_CATALOG.csv"
BASE = "e61a3b0adfff54e2e1793759ce669ff5b1d241dd"
HEAD = "d099821479f28eec2659e250296db877541cdd89"


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=SOURCE, text=True, encoding="utf-8", errors="replace"
    ).strip()


def run() -> list[dict[str, str]]:
    if git("merge-base", BASE, HEAD) != BASE:
        raise AssertionError("local main source range drift")
    commits = git("rev-list", "--reverse", f"{BASE}..{HEAD}").splitlines()
    if len(commits) != 8:
        raise AssertionError("local main delta commit count")
    rows = []
    for commit in commits:
        date = git("show", "-s", "--format=%aI", commit)
        paths = git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()
        blobs = {}
        for item in git("ls-tree", "-r", "--full-tree", commit).splitlines():
            metadata, path = item.split("\t", 1)
            parts = metadata.split()
            if parts[1] == "blob":
                blobs[path] = parts[2]
        for path in paths:
            rows.append(
                {
                    "path": path,
                    "git_blob": blobs.get(path, ""),
                    "status": "FOUND_LOCAL_MAIN" if path in blobs else "DELETED_LOCAL_MAIN",
                    "commit": commit,
                    "author_date": date,
                }
            )
    with DEST.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["path", "git_blob", "status", "commit", "author_date"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    versions = run()
    print(len(versions), len({row["path"] for row in versions}))
