"""Run dev builds for several recipe ids sequentially (resumable: skips ids with a build record unless --force).

Failures are logged to outputs/paper1_scale25/data/build_failures.jsonl and never retried with changed
definitions. Usage: python run_builds.py id1 id2 ... [--force]
"""

import json
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dev_build  # noqa: E402

ROOT = dev_build.ROOT
FAIL = ROOT / "outputs/paper1_scale25/data/build_failures.jsonl"

if __name__ == "__main__":
    ids = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    for i in ids:
        if (dev_build.DEV_REC / f"{i}.json").exists() and not force:
            print("skip", i, flush=True)
            continue
        print("BUILD", i, datetime.now(UTC).isoformat(timespec="seconds"), flush=True)
        try:
            r = dev_build.build(i, True)
            print(i, "eligible", r["eligible"], "episodes", r["episodes"], "val", r["validation"], flush=True)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            with open(FAIL, "a") as f:
                f.write(json.dumps({"id": i, "time": datetime.now(UTC).isoformat(timespec="seconds"), "error": repr(e)[:400]}) + "\n")
            print(i, "FAILED", repr(e)[:200], flush=True)
