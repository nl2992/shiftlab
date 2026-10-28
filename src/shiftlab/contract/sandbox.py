"""Isolated execution of an external adapter (P4 section 1, Codex review 1).

The AST import check in ``isolation.py`` is only a lint: standard-library modules such as
``pathlib``, ``sys`` or ``inspect`` can still reach repository files. This module runs the
adapter in a separate interpreter instead.

Packet: a temporary directory holding only a standalone copy of ``interface.py``, the adapter
file, the P4 and contract-README documents and a small runner. The adapter runs with
``python -I`` (no user site, no PYTHONPATH, no script directory on the path), ``cwd`` set to the
packet, a stripped environment, and ``shiftlab`` removed from ``sys.path`` and blocked by a
meta-path finder. The harness stays in the parent; events and feedback cross as JSON lines.

Before the adapter is loaded the runner installs a ``sys.addaudithook`` guard (hooks cannot be
removed from Python code). It denies: opening any file outside the packet except read-only access
under the Python prefixes (stdlib and site-packages); ``os.listdir``/``os.scandir``/``glob.glob``
outside the packet and those prefixes; subprocess, ``os.system``, ``os.exec*``, ``os.spawn*``,
``os.posix_spawn``, fork; ``socket.*``; ``ctypes.*``; and importing ctypes/_ctypes/cffi.

Residual, stated plainly: audit hooks are a strong in-process guard, not an OS sandbox. A
determined escape through a native extension is out of scope, and the adapter can still tamper
with in-process state. Full isolation additionally requires the implementer session to receive
only the packet, which is a procedural requirement recorded in the P4 protocol.

The adapter file must define ``build_monitor()`` returning a ``Monitor`` and import the contract
as ``from interface import ...``.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Self

from .interface import Feedback, PublicEvent, TaskSpec

DOC_PATHS = (
    "docs/research_refinement_v1/stage1/P4_benchmark_value_gate.md",
    "docs/research_refinement_v1/stage1/CONTRACT_README.md",
)

RUNNER_SOURCE = """\
import importlib.abc
import importlib.util
import json
import os
import sys
import traceback

PACKET = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if not os.path.isdir(os.path.join(p or ".", "shiftlab"))]
sys.path.insert(0, PACKET)


class _Block(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name == "shiftlab" or name.startswith("shiftlab."):
            raise ImportError("shiftlab is not available inside the sandbox: " + name)
        return None


sys.meta_path.insert(0, _Block())
_out = sys.stdout
sys.stdout = sys.stderr  # adapter prints must not corrupt the protocol


def send(obj):
    _out.write(json.dumps(obj) + "\\n")
    _out.flush()


def _install_guard():
    real, norm, common, fsdecode = os.path.realpath, os.path.normcase, os.path.commonpath, os.fsdecode

    def canon(p):
        return norm(real(fsdecode(p)))

    packet = canon(PACKET)
    std_roots = [
        canon(r) for r in {sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix}
    ]
    blocked_modules = ("ctypes", "_ctypes", "cffi", "_cffi_backend")
    blocked_events = ("os.system", "os.posix_spawn", "os.fork", "os.forkpty", "os.startfile")
    blocked_prefixes = ("subprocess.", "socket.", "ctypes.", "os.exec", "os.spawn")
    write_flags = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC

    def under(path, roots):
        try:
            return any(common([path, r]) == r for r in roots)
        except ValueError:
            return False

    def deny(what):
        raise PermissionError("sandbox audit guard denied: " + what)

    def hook(event, args):
        if event == "open":
            path = args[0]
            if path is None or isinstance(path, int):
                return
            p = canon(path)
            if under(p, [packet]):
                return
            mode = args[1] if len(args) > 1 and isinstance(args[1], str) else "r"
            flags = args[2] if len(args) > 2 and isinstance(args[2], int) else 0
            writing = any(c in mode for c in "wax+") or bool(flags & write_flags)
            if not writing and under(p, std_roots):
                return
            deny("open " + str(path))
        elif event in ("os.listdir", "os.scandir") or event.startswith("glob.glob"):
            path = args[0] if args else None
            if path is None or isinstance(path, int):
                return
            if not under(canon(path), [packet] + std_roots):
                deny(event + " " + str(path))
        elif event == "import":
            name = args[0]
            if name.split(".")[0] in blocked_modules:
                deny("import " + name)
        elif event in blocked_events or event.startswith(blocked_prefixes):
            deny(event)

    sys.addaudithook(hook)


try:
    import numpy as np
    import interface

    # Preload what numeric adapters need so their imports never touch the guard, then forget
    # ctypes so that an adapter importing it triggers an audited (and denied) import.
    for _name in ("scipy.special", "scipy.stats", "scipy.optimize", "scipy.linalg"):
        try:
            __import__(_name)
        except ImportError:
            pass
    for _name in [m for m in sys.modules if m.split(".")[0] in ("ctypes", "_ctypes", "cffi")]:
        del sys.modules[_name]
    _install_guard()

    spec =importlib.util.spec_from_file_location("adapter", os.path.join(PACKET, ADAPTER_NAME))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monitor = module.build_monitor()
    send({"ready": True})
except BaseException:
    send({"error": traceback.format_exc()})
    sys.exit(1)


def make_event(d):
    d = dict(d)
    d["x"] = np.asarray(d["x"], dtype=float)
    return interface.PublicEvent(**d)


for line in sys.stdin:
    try:
        msg = json.loads(line)
        op = msg["op"]
        if op == "reset":
            s = dict(msg["spec"])
            s["price_range"] = tuple(s["price_range"])
            monitor.reset(interface.TaskSpec(**s))
            send({"ok": True})
        elif op == "propensity":
            send({"q": float(monitor.propensity(make_event(msg["event"])))})
        elif op == "observe":
            fb = msg["feedback"]
            fb = None if fb is None else interface.Feedback(**fb)
            monitor.observe(make_event(msg["event"]), fb)
            send({"log_e": float(monitor.log_e_value)})
        elif op == "close":
            break
        else:
            send({"error": "unknown op " + repr(op)})
    except BaseException:
        send({"error": traceback.format_exc()})
"""


class SandboxError(RuntimeError):
    """The sandboxed adapter failed, timed out or exited."""


def build_packet(adapter_path: str | Path, dest: str | Path, docs: tuple[Path, ...] | None = None):
    """Create the implementation packet in ``dest`` and return the adapter file name."""
    adapter = Path(adapter_path)
    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).with_name("interface.py"), root / "interface.py")
    shutil.copyfile(adapter, root / adapter.name)
    (root / "_runner.py").write_text(
        RUNNER_SOURCE.replace("ADAPTER_NAME", repr(adapter.name)), encoding="utf-8"
    )
    repo = Path(__file__).resolve().parents[3]
    doc_files = docs if docs is not None else tuple(repo / p for p in DOC_PATHS)
    (root / "docs").mkdir(exist_ok=True)
    for doc in doc_files:
        if Path(doc).exists():
            shutil.copyfile(doc, root / "docs" / Path(doc).name)
    return adapter.name


def packet_manifest(packet: str | Path) -> dict[str, str]:
    """SHA-256 of every packet file, keyed by posix relative path (for provenance)."""
    root = Path(packet)
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def _stripped_env() -> dict[str, str]:
    keep = ("SYSTEMROOT", "SYSTEMDRIVE", "TEMP", "TMP")  # needed to start Python on Windows
    env = {k: os.environ[k] for k in keep if k in os.environ}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


class SandboxedMonitor:
    """A ``Monitor`` proxy that runs the adapter in an isolated subprocess."""

    def __init__(self, adapter_path: str | Path, *, timeout: float = 60.0, docs=None) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="shiftlab_packet_")
        self.packet = Path(self._tmp.name)
        name = build_packet(adapter_path, self.packet, docs)
        self.manifest = packet_manifest(self.packet)
        self._timeout = timeout
        self._log_e = 0.0
        self._lines: queue.Queue[str | None] = queue.Queue()
        self._proc = subprocess.Popen(
            [sys.executable, "-I", str(self.packet / "_runner.py")],
            cwd=self.packet,
            env=_stripped_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        threading.Thread(target=self._pump, daemon=True).start()
        try:
            if self._read().get("ready") is not True:
                raise SandboxError("adapter did not report ready")
        except BaseException:
            self.close()
            raise
        self.adapter_name = name

    def _pump(self) -> None:
        assert self._proc.stdout is not None
        for line in self._proc.stdout:
            self._lines.put(line)
        self._lines.put(None)

    def _read(self) -> dict:
        try:
            line = self._lines.get(timeout=self._timeout)
        except queue.Empty:
            self._proc.kill()
            raise SandboxError("adapter timed out") from None
        if line is None:
            raise SandboxError("adapter process exited")
        reply = json.loads(line)
        if "error" in reply:
            raise SandboxError(reply["error"])
        return reply

    def _call(self, message: dict) -> dict:
        assert self._proc.stdin is not None
        self._proc.stdin.write(json.dumps(message) + "\n")
        self._proc.stdin.flush()
        return self._read()

    @staticmethod
    def _event(event: PublicEvent) -> dict:
        data = asdict(event)
        data["x"] = [float(v) for v in event.x]
        return data

    def reset(self, spec: TaskSpec) -> None:
        self._log_e = 0.0
        self._call({"op": "reset", "spec": asdict(spec)})

    def propensity(self, event: PublicEvent) -> float:
        return float(self._call({"op": "propensity", "event": self._event(event)})["q"])

    def observe(self, event: PublicEvent, feedback: Feedback | None) -> None:
        reply = self._call(
            {
                "op": "observe",
                "event": self._event(event),
                "feedback": None if feedback is None else asdict(feedback),
            }
        )
        self._log_e = float(reply["log_e"])

    @property
    def log_e_value(self) -> float:
        return self._log_e

    def close(self) -> None:
        if self._proc.poll() is None:
            try:
                assert self._proc.stdin is not None
                self._proc.stdin.write(json.dumps({"op": "close"}) + "\n")
                self._proc.stdin.flush()
                self._proc.wait(timeout=5)
            except (OSError, subprocess.SubprocessError):
                self._proc.kill()
        try:
            self._proc.wait(timeout=5)
        finally:
            for stream in (self._proc.stdin, self._proc.stdout):
                if stream is not None:
                    stream.close()
            self._tmp.cleanup()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
