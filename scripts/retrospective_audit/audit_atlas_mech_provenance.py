"""Locate the archived Atlas Amendment 4 source bytes in visible Git/local history."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "shift-research-starter" / "outputs" / "failure_atlas_v1_mechcheck"
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "ATLAS_MECHCHECK_PROVENANCE.json"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL)


def run(source: Path = SOURCE) -> dict[str, object]:
    result_path = source / "results.json"
    archive = json.loads(result_path.read_text(encoding="utf-8"))
    roots = [
        Path(line.removeprefix("worktree "))
        for line in git("worktree", "list", "--porcelain").decode("utf-8").splitlines()
        if line.startswith("worktree ")
    ]
    fsck_lines = (
        git("fsck", "--full", "--no-reflogs", "--unreachable", "--no-progress")
        .decode("ascii")
        .splitlines()
    )
    unreachable_blobs = [
        line.split()[2] for line in fsck_lines if line.startswith("unreachable blob ")
    ]
    target_hashes = set(archive["git"]["src_sha256"].values())
    unreachable_hash_matches: dict[str, list[str]] = {digest: [] for digest in target_hashes}
    for object_id in unreachable_blobs:
        digest = hashlib.sha256(git("cat-file", "blob", object_id)).hexdigest()
        if digest in unreachable_hash_matches:
            unreachable_hash_matches[digest].append(object_id)
    records = []
    for name, target in archive["git"]["src_sha256"].items():
        relative = f"scripts/{name}" if name.startswith("run_") else f"src/shiftlab/dive/{name}"
        commits = git("log", "--all", "--format=%H", "--", relative).decode("ascii").splitlines()
        seen: set[str] = set()
        matches = []
        for commit in commits:
            try:
                payload = git("show", f"{commit}:{relative}")
            except subprocess.CalledProcessError:
                continue
            digest = hashlib.sha256(payload).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            if digest == target:
                matches.append(commit)
        local_matches = []
        for root in roots:
            candidate = root / relative
            if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest() == target:
                local_matches.append(str(root))
        records.append(
            {
                "path": relative,
                "recorded_sha256": target,
                "distinct_visible_committed_versions_checked": len(seen),
                "matching_visible_commits": matches,
                "matching_worktrees": local_matches,
                "matching_unreachable_blobs": unreachable_hash_matches[target],
                "recovered": bool(matches or local_matches or unreachable_hash_matches[target]),
            }
        )
    return {
        "archived_result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "archive_git_head": archive["git"]["head"],
        "archive_dirty": archive["git"]["dirty"],
        "visible_worktrees_checked": len(roots),
        "unreachable_blobs_checked": len(unreachable_blobs),
        "files": records,
        "unrecovered_paths": [row["path"] for row in records if not row["recovered"]],
        "scope": "Reachable commits from current --all refs, present worktree files, and locally unreachable blobs from git fsck. Does not search unfetched PR commits or inaccessible machines. Hash recovery alone does not replay per-seed outcomes.",
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(
        f"{len(result['files'])} recorded source hashes; {len(result['unrecovered_paths'])} unrecovered"
    )
