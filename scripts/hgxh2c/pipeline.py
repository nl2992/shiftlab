"""Unattended HG x H2c orchestrator. Idempotent: stages with a marker are skipped.

Usage: pipeline.py [--only STAGE] [--status]
Markers: outputs/hgxh2c/markers/<stage>.done | .failed ; lock: outputs/hgxh2c/pipeline.lock ; end: DONE.
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/hgxh2c"
MARK, LOG, LOCK, DONE = (
    OUT / "markers",
    OUT / "logs/pipeline.log",
    OUT / "pipeline.lock",
    OUT / "DONE",
)
H = 3600
# stage -> (script, timeout seconds or None)
STAGES = {
    "stage1": ("scripts/hgxh2c/stage1/run_native_repro.py", 12 * H),
    "stage2": ("scripts/hgxh2c/stage2_benchmark.py", 24 * H),
    "stage3": ("scripts/hgxh2c/stage3_search.py", None),
    "stage4": ("scripts/hgxh2c/stage4_confirm.py", 24 * H),
    "stage1_full": (
        "scripts/hgxh2c/stage1/run_native_repro.py",
        None,
        "--full",
    ),  # paper-budget reruns; never blocks report
    "report": ("scripts/hgxh2c/make_report.py", 1 * H),
}
UPSTREAM = {"stage3": "stage2", "stage4": "stage3"}
RETRIES, BACKOFF = 3, (60, 300, 900)


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')} {msg}\n")


def py():
    v = ROOT / ".venv/Scripts/python.exe"
    return str(v if v.exists() else sys.executable)


def lock_held():
    try:
        pid = int(LOCK.read_text().strip())
        p = psutil.Process(pid)
        return p.is_running() and "pipeline.py" in " ".join(p.cmdline()) and pid != os.getpid()
    except (OSError, ValueError, psutil.Error):
        return False


def state(stage):
    if (MARK / f"{stage}.done").exists():
        return "DONE"
    if (MARK / f"{stage}.failed").exists():
        return "FAILED"
    return "MISSING_SCRIPT" if not (ROOT / STAGES[stage][0]).exists() else "PENDING"


def status():
    for s in STAGES:
        print(f"{s:7s} {state(s)}")
    print("lock:", "held by live pipeline" if lock_held() else "free")
    print("DONE:", DONE.exists())


def run_stage(stage):
    script, timeout, *extra = STAGES[stage]
    if not (ROOT / script).exists():
        log(f"{stage} MISSING_SCRIPT {script}")
        return "MISSING_SCRIPT"
    if stage == "stage4":
        sys.path.insert(0, str(ROOT / "src"))
        from shiftlab.hgxh2c.freeze import require_frozen

        try:
            require_frozen(["frontier", "finalists"])
        except RuntimeError as e:
            log(f"{stage} FAILED not frozen: {e}")
            return "FAILED"
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    for attempt in range(RETRIES):
        log(f"{stage} start attempt {attempt + 1}/{RETRIES}")
        with open(LOG, "a", encoding="utf-8") as f:
            try:
                rc = subprocess.run(
                    [py(), str(ROOT / script), *extra],
                    cwd=ROOT,
                    check=False,
                    env=env,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                ).returncode
            except subprocess.TimeoutExpired:
                rc = "timeout"
        log(f"{stage} exit {rc}")
        if rc == 0:
            return "DONE"
        if attempt < RETRIES - 1:
            time.sleep(BACKOFF[attempt])
    log(f"{stage} FAILED after {RETRIES} attempts")
    return "FAILED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=list(STAGES))
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.status:
        return status()
    if lock_held():
        return print("pipeline already running")
    OUT.mkdir(parents=True, exist_ok=True)
    MARK.mkdir(exist_ok=True)
    LOCK.write_text(str(os.getpid()))
    try:
        todo = [a.only] if a.only else list(STAGES)
        res = {}
        for s in todo:
            if a.only:
                (MARK / f"{s}.failed").unlink(missing_ok=True)
            elif s != "report" and state(s) in ("DONE", "FAILED"):
                res[s] = state(s)
                continue
            if UPSTREAM.get(s) and (res.get(UPSTREAM[s]) or state(UPSTREAM[s])) == "FAILED":
                log(f"{s} SKIPPED_UPSTREAM_FAILED")
                res[s] = "FAILED"
                continue
            if s == "report":  # report always regenerates from whatever exists
                run_stage(s)
                continue
            res[s] = run_stage(s)
            if res[s] in ("DONE", "FAILED"):
                (MARK / f"{s}.{res[s].lower()}").write_text(datetime.now().isoformat())
        if not a.only and all(res.get(s) in ("DONE", "FAILED") for s in STAGES if s != "report"):
            DONE.write_text(datetime.now().isoformat())
            log("ALL STAGES TERMINAL; DONE written")
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
