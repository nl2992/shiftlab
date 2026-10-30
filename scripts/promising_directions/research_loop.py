"""Resumable research-loop orchestrator: lock, atomic state, append-only ledger, CLI.

Usage: python scripts/promising_directions/research_loop.py {run --max-cycles N | status | resume}
Cycles run sequentially; max_workers is recorded in config but not yet used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = "configs/promising_directions/research_loop.yaml"
STATE = "docs/promising_directions/RESEARCH_STATE.json"
LEDGER = "docs/promising_directions/RESEARCH_LEDGER.md"
LOCK = "docs/promising_directions/.research_loop.lock"
STALE_LOCK_S = 6 * 3600


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(root: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], check=False, cwd=root, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def ledger_append(root: Path, line: str) -> None:
    with open(root / LEDGER, "a", encoding="utf-8", newline="\n") as f:
        f.write(f"- {now()} {line}\n")


def pid_alive(pid: int) -> bool:
    if sys.platform == "win32":  # os.kill(pid, 0) would terminate the process on Windows
        import ctypes

        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class Lock:
    """Single-writer lock file created with O_EXCL; stale if pid dead or too old."""

    def __init__(self, path: Path, stale_s: float = STALE_LOCK_S):
        self.path, self.stale_s = path, stale_s

    def _stale(self) -> bool:
        try:
            info = json.loads(self.path.read_text())
            return not pid_alive(int(info["pid"])) or time.time() - info["ts"] > self.stale_s
        except (OSError, ValueError, KeyError):
            return True

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if not self._stale():
                    raise RuntimeError(f"lock held: {self.path}") from None
                self.path.unlink(missing_ok=True)
                continue
            with os.fdopen(fd, "w") as f:
                json.dump({"pid": os.getpid(), "ts": time.time()}, f)
            return
        raise RuntimeError(f"could not acquire lock: {self.path}")

    def release(self) -> None:
        self.path.unlink(missing_ok=True)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()


def load_config(root: Path) -> dict:
    return yaml.safe_load((root / CONFIG).read_text(encoding="utf-8"))


def save_state(root: Path, state: dict) -> None:
    state["updated_at"] = now()
    atomic_write(root / STATE, json.dumps(state, indent=2, sort_keys=True) + "\n")


def next_pending(state: dict) -> str | None:
    return next((t for t, v in state["tasks"].items() if v["status"] == "pending"), None)


def ensure_state(root: Path, cfg: dict) -> dict:
    """Load state (creating it if absent) and register new config tasks with protocol hashes."""
    p = root / STATE
    if p.exists():
        state = json.loads(p.read_text(encoding="utf-8"))
    else:
        state = {
            "branch": git(root, "branch", "--show-current"),
            "source_commit": git(root, "rev-parse", "9cb4a1d") or git(root, "rev-parse", "HEAD"),
            "lanes": cfg["lanes"],
            "budget": cfg["limits"],
            "tasks": {},
            "cycle_counter": 0,
            "consecutive_no_insight": 0,
            "consecutive_infra_failures": 0,
            "last_verified_checkpoint": None,
            "next_task": None,
            "stop_reason": None,
        }
    for t in cfg["tasks"]:
        if t["id"] not in state["tasks"]:
            proto = root / t["protocol_path"]
            if not proto.exists():
                raise FileNotFoundError(f"protocol missing for {t['id']}: {proto}")
            state["tasks"][t["id"]] = {
                **t,
                "status": "pending",
                "protocol_sha256": sha256_file(proto),
                "registered_at": now(),
                "cycles": [],
                "artifacts": {},
                "error": None,
            }
    state["next_task"] = next_pending(state)
    save_state(root, state)
    return state


def run_session(root: Path, max_cycles: int | None = None, resume: bool = False) -> dict:
    from run_one_cycle import run_one_cycle

    cfg = load_config(root)
    lim = cfg["limits"]
    with Lock(root / LOCK):
        state = ensure_state(root, cfg)
        if resume:  # explicit operator action: requeue failures and clear the stop reason
            for v in state["tasks"].values():
                if v["status"] == "failed":
                    v["status"] = "pending"
            state.update(stop_reason=None, consecutive_no_insight=0, consecutive_infra_failures=0)
        state["stop_reason"] = None
        n = min(max_cycles or lim["max_cycles_per_session"], lim["max_cycles_per_session"])
        for _ in range(n):
            tid = next_pending(state)
            if tid is None:
                break
            run_one_cycle(root, state, tid, lim)
            if state["consecutive_no_insight"] >= lim["max_consecutive_no_insight"]:
                state["stop_reason"] = "no_insight"
            elif state["consecutive_infra_failures"] >= lim["max_consecutive_infra_failures"]:
                state["stop_reason"] = "infra_failures"
            if state["stop_reason"]:
                break
        if state["stop_reason"] is None and next_pending(state) is None:
            state["stop_reason"] = "queue_empty"
        state["next_task"] = next_pending(state)
        save_state(root, state)
        ledger_append(
            root, f"session end stop_reason={state['stop_reason']} next={state['next_task']}"
        )
    return state


def status_text(root: Path) -> str:
    p = root / STATE
    if not p.exists():
        return "no state yet (run `run` first)"
    s = json.loads(p.read_text(encoding="utf-8"))
    rows = [f"  {k}: {v['status']} cycles={len(v['cycles'])}" for k, v in s["tasks"].items()]
    return "\n".join(
        [
            f"branch={s['branch']} source_commit={s['source_commit'][:7]} cycles={s['cycle_counter']}",
            f"next_task={s['next_task']} stop_reason={s['stop_reason']}",
            f"no_insight={s['consecutive_no_insight']} infra_failures={s['consecutive_infra_failures']}",
            *rows,
        ]
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("run").add_argument("--max-cycles", type=int, default=None)
    sub.add_parser("resume").add_argument("--max-cycles", type=int, default=None)
    sub.add_parser("status")
    a = ap.parse_args(argv)
    if a.cmd == "status":
        print(status_text(a.root))
        return 0
    try:
        run_session(a.root, a.max_cycles, resume=a.cmd == "resume")
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(status_text(a.root))
    return 0


if __name__ == "__main__":
    sys.exit(main())
