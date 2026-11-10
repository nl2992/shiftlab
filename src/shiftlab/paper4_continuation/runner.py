"""Light-weight process runner for the A3/A4 harness (no scipy/shiftlab imports).

Kept separate from ``ablation`` so the parent process stays small: on macOS a child's
``ru_maxrss`` can inherit the parent's pre-exec footprint.
"""

from __future__ import annotations

import hashlib
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_child(command: list[str], cap_seconds: float) -> dict:
    """Run ``command`` in a fresh process; per-child peak RSS via ``os.wait4``.

    ``wait4`` returns the rusage of exactly that pid, so ``ru_maxrss`` is this child's own
    high-water mark (bytes on macOS, kilobytes on Linux), not the max over all past children
    as with ``getrusage(RUSAGE_CHILDREN)``.  The child is ``python`` itself (no wrapper
    process), spawned from a small campaign process.
    """
    started = time.perf_counter()
    stdout_path = Path(os.environ.get("TMPDIR", "/tmp")) / f"abl_{os.getpid()}_{time.time_ns()}.out"
    timed_out = False
    with open(stdout_path, "wb") as sink:
        process = subprocess.Popen(command, stdout=sink, stderr=subprocess.PIPE)
        status = rusage = None
        while True:
            pid, status, rusage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                break
            if time.perf_counter() - started > cap_seconds:
                timed_out = True
                os.kill(process.pid, signal.SIGKILL)
                _pid, status, rusage = os.wait4(process.pid, 0)
                break
            time.sleep(0.05)
    wall = time.perf_counter() - started
    process.returncode = os.waitstatus_to_exitcode(status)
    stderr = process.stderr.read().decode(errors="replace") if process.stderr else ""
    raw = rusage.ru_maxrss
    peak_bytes = raw if sys.platform == "darwin" else raw * 1024
    text = stdout_path.read_text()
    stdout_path.unlink(missing_ok=True)
    lines = [line for line in text.splitlines() if line.strip()]
    return {
        "returncode": process.returncode,
        "timed_out": timed_out,
        "wall_seconds_parent": wall,
        "peak_rss_bytes": peak_bytes,
        "peak_rss_mib": peak_bytes / 2**20,
        "child_user_seconds": rusage.ru_utime,
        "child_system_seconds": rusage.ru_stime,
        "stdout_last_line": lines[-1] if lines else "",
        "stderr_tail": stderr[-2000:],
    }
