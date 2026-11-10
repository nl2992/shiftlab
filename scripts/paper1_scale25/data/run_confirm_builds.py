"""Run the C1 confirmation builds in protocol order, one subprocess each (resumable; no definition changes on retry)."""

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import confirm_build as cb

if __name__ == "__main__":
    only = sys.argv[1:]
    for name, a, b in cb.ORDER:
        if only and name not in only:
            continue
        done = (cb.OUT_REC / f"{name}.json").exists()
        if done:
            print("skip", name, flush=True)
            continue
        for attempt in range(3):
            print(time.strftime("%H:%M:%S"), "BUILD", name, a, b, "attempt", attempt, flush=True)
            r = subprocess.run(
                [sys.executable, str(HERE / "confirm_build.py"), name, "--fetch"], check=False
            )
            if r.returncode == 0:
                break
            (cb.OUT_REC / f"{name}.FAILED.json").rename(cb.OUT_REC / f"{name}.FAILED{attempt}.json")
        print(time.strftime("%H:%M:%S"), "done", name, "rc", r.returncode, flush=True)
