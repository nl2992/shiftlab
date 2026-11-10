"""Stall watchdog for c1_run.py: relaunch (resumable) if out/progress.txt has not changed for --stall seconds.

python c1_watch.py --stall 900 --retries 8 -- <args passed to c1_run.py>
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stall", type=int, default=900)
    ap.add_argument("--retries", type=int, default=8)
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    rest = [x for x in a.rest if x != "--"]
    out = Path(rest[rest.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)
    prog = out / "progress.txt"
    wlog = out / "watch.log"

    def log(m):
        with open(wlog, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {m}\n")

    for attempt in range(a.retries + 1):
        if (out / "DONE").exists():
            log("DONE")
            return
        log(f"launch attempt {attempt}")
        p = subprocess.Popen([sys.executable, str(HERE / "c1_run.py"), *rest])
        last = time.time()
        seen = prog.stat().st_mtime if prog.exists() else 0
        while p.poll() is None:
            time.sleep(30)
            m = prog.stat().st_mtime if prog.exists() else 0
            if m != seen:
                seen, last = m, time.time()
            elif time.time() - last > a.stall:
                log("stall: killing process tree")
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], check=False)
                break
        if p.returncode == 0 and (out / "DONE").exists():
            log("finished ok")
            return
        log(f"exit code {p.returncode}")
    log("giving up")


if __name__ == "__main__":
    main()
