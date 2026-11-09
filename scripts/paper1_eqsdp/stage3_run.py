"""Stage 3 runner: the frozen candidate, the frozen new reference, arm R and the original reference
on ODD episodes, once.

  python stage3_run.py
Refuses to start unless the freeze file docs/paper1_eqsdp/stage2_frozen_config.json is tracked,
unmodified, and its introducing commit is already contained in origin/<current branch>. The episode
index is kept in the seed derivation exactly as in the even-episode runs (ep, seed, seed_base).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage2_eval as ev
import trace_run as tr

ROOT = tr.ROOT
FREEZE = ROOT / "docs/paper1_eqsdp/stage2_frozen_config.json"
OUT = ROOT / "outputs/paper1_eqsdp/stage3"


def git(*a):
    return subprocess.run(
        ["git", *a], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def guard() -> str:
    rel = FREEZE.relative_to(ROOT).as_posix()
    assert rel in git("ls-files").splitlines(), "freeze file not tracked"
    assert git("status", "--porcelain", "--", rel) == "", "freeze file modified since commit"
    commit = git("log", "--diff-filter=A", "--format=%H", "--", rel).splitlines()[-1]
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    git("fetch", "origin", branch)
    git("merge-base", "--is-ancestor", commit, f"origin/{branch}")  # raises if not pushed
    return commit


def main():
    commit = guard()
    fz = json.loads(FREEZE.read_text())
    cand_name, ref_name = "s3_candidate", fz["new_reference"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "start.json").write_text(
        json.dumps({"freeze_commit": commit, "started": time.strftime("%Y-%m-%d %H:%M:%S %z"),
                    "epoch": time.time(), "candidate_cfg": fz["candidate_cfg"],
                    "new_reference": ref_name})
    )  # fmt: skip
    names = [cand_name, ref_name, tr.ARM_R, "wald_l0.97_g0.2"]
    ev.run_named(names, "odd", OUT / "run", workers=16, dyn={cand_name: fz["candidate_cfg"]})


if __name__ == "__main__":
    main()
