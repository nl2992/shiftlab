"""Metadata-only workspace snapshot; never read raw/licensed data contents."""

import datetime
import json
import os
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/retrospective_audit_2026_11_01/WORKSPACE_SNAPSHOT.json"


def run(cwd, args):
    p = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {"command": args, "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def main():
    listing = run(ROOT, ["git", "-c", "core.quotePath=false", "worktree", "list", "--porcelain"])
    records = []
    for block in listing["stdout"].strip().split("\n\n"):
        lines = block.splitlines()
        if not lines or not lines[0].startswith("worktree "):
            continue
        path = lines[0][9:]
        records.append(
            {
                "path": path,
                "worktree_record": lines,
                "status": run(path, ["git", "status", "--porcelain=v1", "--untracked-files=all"]),
                "ignored_metadata": run(
                    path, ["git", "status", "--porcelain=v1", "--ignored", "--untracked-files=no"]
                ),
                "head": run(path, ["git", "rev-parse", "HEAD"]),
            }
        )
    report = {
        "time_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "worktrees": records,
        "gpu": run(
            ROOT,
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json",
            ],
        ),
        "memory": run(
            ROOT,
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | ConvertTo-Json",
            ],
        ),
        "scope": "Git status metadata only; ignored directories listed, contents not exhaustively catalogued; no raw data read",
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"worktrees": len(records), "output": str(OUT)}))


if __name__ == "__main__":
    main()
