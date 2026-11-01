"""Read-only tracked source inventory; verdict hits are candidates, never audited claims."""

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/retrospective_audit_2026_11_01"
DECISION = re.compile(
    r"\b(pass|kill|no[- ]go|stop|mixed|inconclusive|conditional go|novel|invalid|uncertified|not worth|superseded)\b",
    re.IGNORECASE,
)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    refs = (
        git(
            "for-each-ref", "--format=%(refname) %(objectname)", "refs/heads", "refs/remotes/origin"
        )
        .decode()
        .splitlines()
    )
    trees = {}
    coverage = []
    for line in refs:
        ref, commit = line.split()
        entries = git("ls-tree", "-r", "-z", commit).split(b"\0")
        count = 0
        for entry in entries:
            if not entry:
                continue
            meta, raw_path = entry.split(b"\t", 1)
            _mode, kind, oid = meta.decode().split()
            path = raw_path.decode("utf-8")
            if kind != "blob" or path.split("/")[0] not in {
                "docs",
                "papers",
                "configs",
                "scripts",
                "src",
                "tests",
                "outputs",
            }:
                continue
            count += 1
            trees.setdefault((path, oid), []).append((ref, commit))
        coverage.append({"ref": ref, "commit": commit, "files": count})
    with (OUT / "01_SOURCE_CATALOG.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "git_blob", "status", "refs_and_commits"])
        for (path, oid), locations in sorted(trees.items()):
            writer.writerow(
                [
                    path,
                    oid,
                    "FOUND_MAIN"
                    if any(r == "refs/remotes/origin/main" for r, c in locations)
                    else "FOUND_BRANCH",
                    json.dumps(locations),
                ]
            )
    with (OUT / "DECISION_CANDIDATES.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "git_blob", "line", "verbatim", "audit_status"])
        for (path, oid), locations in sorted(trees.items()):
            if Path(path).suffix.lower() not in {".md", ".txt", ".yaml", ".yml", ".py", ".json"}:
                continue
            data = git("cat-file", "blob", oid)
            if len(data) > 2_000_000:
                continue
            for number, text in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
                if DECISION.search(text):
                    writer.writerow([path, oid, number, text, "NOT_YET_AUDITED"])
    (OUT / "BRANCH_COVERAGE.json").write_text(json.dumps(coverage, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "refs": len(refs),
                "unique_path_blob_versions": len(trees),
                "candidate_sha256": hashlib.sha256(
                    (OUT / "DECISION_CANDIDATES.csv").read_bytes()
                ).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
