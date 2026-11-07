"""Scheduled-task entry: relaunch pipeline.py detached unless DONE exists or a live pipeline holds the lock."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline as P

TASK = "ShiftLab-HGxH2c-watchdog"
NOWIN = 0x08000000
FLAGS = (
    0x00000008 | 0x00000200 | NOWIN
)  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW


def wlog(m):
    P.log(f"[watchdog] {m}")


def main():
    if P.DONE.exists():
        wlog("DONE exists; unregistering task")
        subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK, "/F"],
            creationflags=NOWIN,
            capture_output=True,
            check=False,
        )
        return
    if P.lock_held():
        return
    wlog("launching pipeline")
    f = open(P.LOG, "a", encoding="utf-8")  # noqa: SIM115 - handle must outlive this scope for the detached pipeline
    cmd = [P.py(), str(P.ROOT / "scripts/hgxh2c/pipeline.py")]
    kw = {"cwd": P.ROOT, "stdout": f, "stderr": f, "stdin": subprocess.DEVNULL, "close_fds": True}
    try:  # escape the Task Scheduler job object so the pipeline outlives this process
        subprocess.Popen(cmd, creationflags=FLAGS | 0x01000000, **kw)
    except OSError:
        subprocess.Popen(cmd, creationflags=FLAGS, **kw)


if __name__ == "__main__":
    main()
