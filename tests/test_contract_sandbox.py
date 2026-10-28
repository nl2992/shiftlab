"""Sandboxed execution of external adapters through the contract harness."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from shiftlab.contract import PublicEvent, TaskSpec
from shiftlab.contract.harness import run_monitor
from shiftlab.contract.isolation import check_imports, check_source
from shiftlab.contract.sandbox import SandboxedMonitor, SandboxError, build_packet, packet_manifest

README = (
    Path(__file__).resolve().parents[1] / "docs/research_refinement_v1/stage1/CONTRACT_README.md"
)
BASE = """
from interface import Feedback, PublicEvent, TaskSpec
import numpy as np
"""
GOOD = (
    BASE
    + """
class Fixed:
    STAKES = np.array([0.05, 0.1, 0.2, 0.4, 0.8])
    def __init__(self, q=0.5):
        self.q = q
    def reset(self, spec):
        self.spec = spec
        self.bound = spec.cost_bound / self.q + spec.epsilon
        self.w = np.zeros(len(self.STAKES))
    def propensity(self, event):
        return self.q
    def observe(self, event, feedback):
        v = -self.spec.epsilon + (0.0 if feedback is None else feedback.paired_cost / feedback.propensity)
        self.w += np.log1p(self.STAKES * v / self.bound)
    @property
    def log_e_value(self):
        m = self.w.max()
        return float(m + np.log(np.exp(self.w - m).mean()))

def build_monitor():
    return Fixed()
"""
)


def _stream(n=120):
    rng = np.random.default_rng(0)
    events = [
        PublicEvent(i, rng.normal(size=3), int(rng.random() < 0.4), 0, False, 0.0, 0.0)
        for i in range(n)
    ]
    return (
        events,
        np.full(n, 2.0),
        rng.random(n),
        rng.uniform(0.5, 2.5, n),
        TaskSpec(5.0, 0.1, 0.05, n, 400.0, (0.5, 2.5)),
    )


def _write(tmp_path, source, name="adapter.py"):
    path = tmp_path / "src_dir" / name
    path.parent.mkdir(exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def test_sandboxed_adapter_runs_end_to_end(tmp_path):
    events, costs, coins, prices, spec = _stream()
    path = _write(tmp_path, GOOD)
    assert check_imports(path) == []
    with SandboxedMonitor(path) as monitor:
        sandboxed = run_monitor(monitor, spec, events, costs, coins, prices)
    assert sandboxed.processed > 0 and sandboxed.queried.any()
    # The same logic in-process (interface imported from shiftlab) gives identical numbers.
    ns: dict = {}
    exec(GOOD.replace("from interface import", "from shiftlab.contract import"), ns)  # noqa: S102
    local = run_monitor(ns["build_monitor"](), spec, events, costs, coins, prices)
    np.testing.assert_array_equal(sandboxed.log_e, local.log_e)
    assert sandboxed.first_alarm == local.first_alarm


def test_packet_contains_only_expected_files(tmp_path):
    path = _write(tmp_path, GOOD)
    packet = tmp_path / "packet"
    build_packet(path, packet)
    names = set(packet_manifest(packet))
    assert {"interface.py", "adapter.py", "_runner.py"} <= names
    assert all(n.startswith("docs/") or "/" not in n for n in names)
    assert not any("shiftlab" in n or n.endswith(".csv") for n in names)


@pytest.mark.parametrize(
    "body",
    [
        "import shiftlab\n",
        "from shiftlab.dive import eprocess\n",
        "import shiftlab.contract.harness\n",
    ],
)
def test_malicious_import_of_shiftlab_fails(tmp_path, body):
    path = _write(tmp_path, body + GOOD)
    with pytest.raises(SandboxError, match="shiftlab|ModuleNotFound|ImportError"):
        SandboxedMonitor(path)


def test_adapter_cannot_read_repo_by_relative_path(tmp_path):
    source = (
        "from pathlib import Path\n"
        "text = Path('../../src/shiftlab/contract/interface.py').read_text()\n" + GOOD
    )
    with pytest.raises(SandboxError, match="FileNotFoundError|denied"):
        SandboxedMonitor(_write(tmp_path, source))


def test_adapter_stdout_prints_do_not_break_protocol(tmp_path):
    events, costs, coins, prices, spec = _stream(20)
    noisy = GOOD.replace(
        "def propensity(self, event):", "def propensity(self, event):\n        print('noise')"
    )
    with SandboxedMonitor(_write(tmp_path, noisy)) as monitor:
        assert run_monitor(monitor, spec, events, costs, coins, prices).processed > 0


def test_adapter_exception_and_missing_factory_are_reported(tmp_path):
    with pytest.raises(SandboxError, match="build_monitor"):
        SandboxedMonitor(_write(tmp_path, BASE))
    boom = GOOD.replace("self.w += ", "raise RuntimeError('boom')\n        self.w += ")
    events, costs, coins, prices, spec = _stream(5)
    with (
        SandboxedMonitor(_write(tmp_path, boom)) as monitor,
        pytest.raises(SandboxError, match="boom"),
    ):
        run_monitor(monitor, spec, events, costs, coins, prices)


def test_readme_example_adapter_passes_lint_and_runs_in_sandbox(tmp_path):
    text = README.read_text(encoding="utf-8")
    code = re.search(r"```python\n(from __future__.*?)```", text, re.DOTALL).group(1)
    path = _write(tmp_path, code)
    assert check_imports(path) == []
    events, costs, coins, prices, spec = _stream(80)
    with SandboxedMonitor(path) as monitor:
        assert run_monitor(monitor, spec, events, costs, coins, prices).processed > 0


REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "snippet",
    [
        f"open({str(REPO / 'src/shiftlab/contract/harness.py')!r}).read()",
        f"open({str(REPO / 'README.md')!r}, 'rb').read()",
        f"import pathlib; pathlib.Path({str(REPO / 'AGENTS.md')!r}).read_text()",
        f"import os; os.listdir({str(REPO)!r})",
        f"import glob; glob.glob({str(REPO / '*')!r})",
        "import subprocess; subprocess.run(['python', '-c', 'pass'])",
        "import os; os.system('echo hi')",
        "import socket; socket.socket()",
        "import ctypes",
        "import _ctypes",
        f"open({str(REPO / 'pwned.txt')!r}, 'w')",
    ],
)
def test_audit_guard_denies_escapes(tmp_path, snippet):
    source = snippet + "\n" + GOOD
    with pytest.raises(SandboxError, match="denied|PermissionError"):
        SandboxedMonitor(_write(tmp_path, source))
    assert not (REPO / "pwned.txt").exists()


def test_audit_guard_allows_packet_and_numeric_stack(tmp_path):
    source = (
        "import json, math, pathlib\n"
        "import numpy as np\n"
        "from scipy import special, stats\n"
        "special.gammaln(3.0); stats.norm.cdf(0.0)\n"
        "pathlib.Path('scratch.txt').write_text('ok')\n"
        "assert pathlib.Path('interface.py').exists()\n" + GOOD
    )
    events, costs, coins, prices, spec = _stream(30)
    with SandboxedMonitor(_write(tmp_path, source)) as monitor:
        assert run_monitor(monitor, spec, events, costs, coins, prices).processed > 0


@pytest.mark.parametrize(
    "snippet",
    [
        # gc reached without importing it (fresh builtin module), then walking objects
        (
            "import _imp, importlib.machinery as mach\n"
            "g = _imp.create_builtin(mach.ModuleSpec('gc', None))\n"
            "hooks = [o for o in g.get_objects() if getattr(o, '__name__', '') == 'hook']\n"
        ),
        "import gc\nhooks = [o for o in gc.get_objects()]\n",
        "import gc\ngc.get_referrers(object())\n",
        "import sys\nframe = sys._getframe(0)\nframe.f_back.f_globals\n",
        "import sys\nsys._current_frames()\n",
        "import inspect\ninspect.currentframe()\n",
        # rebinding code / closure / defaults of a function
        "def f(): pass\nf.__code__ = (lambda: 1).__code__\n",
        "def f(a=1): pass\nf.__defaults__ = (2,)\n",
        # rebinding module / builtins state
        "import types\ntypes.FunctionType((lambda: 1).__code__, {})\n",
        "import os\nos.chdir('..')\n",
        "import sys\nsys.settrace(lambda *a: None)\n",
    ],
)
def test_audit_guard_denies_introspection_and_tampering(tmp_path, snippet):
    with pytest.raises(SandboxError, match="denied|PermissionError"):
        SandboxedMonitor(_write(tmp_path, snippet + GOOD))


def test_guard_allowlist_lives_only_in_code_constants():
    from shiftlab.contract.sandbox import guard_source

    ns: dict = {}
    exec(compile(guard_source(Path("C:/some/packet")), "<g>", "exec"), ns)  # noqa: S102
    hook = ns["hook"]
    assert hook.__closure__ is None and hook.__defaults__ is None and hook.__kwdefaults__ is None
    assert set(ns) == {"__builtins__", "hook"}  # no helper state in the hook's globals
    roots = str(hook.__code__.co_consts)
    assert "packet" in roots  # allowlist appears as constants in the code object


def test_lint_rejects_introspection_names():
    for src in (
        "import gc\n",
        "import inspect\n",
        "import ctypes\n",
        "import sys\nsys._getframe()\n",
        "f = lambda: 0\nf.__code__\n",
        "f.__closure__\n",
        "c.cell_contents\n",
        "f.__globals__\n",
        "object.__subclasses__()\n",
        "x = __builtins__\n",
        "getattr(f, '__code__')\n",
        "tb.tb_frame.f_back\n",
    ):
        assert check_source(src), src
    assert check_source("import math\nimport numpy as np\nx = np.zeros(3)\n") == []


@pytest.mark.parametrize(
    "patch",
    [
        "import builtins\nbuiltins.isinstance = lambda *a: True\nbuiltins.len = lambda *a: 0\n",
        "import builtins\nbuiltins.type = lambda *a: int\nbuiltins.str = lambda *a: ''\n",
        "import os\nos.path.realpath = lambda p: p\nos.fspath = lambda p: p\n",
        "import os\nos.path.commonpath = lambda x: x[0]\n",
    ],
)
def test_patching_stdlib_or_builtins_does_not_weaken_guard(tmp_path, patch):
    target = str(REPO / "src/shiftlab/contract/harness.py")
    source = patch + f"open({target!r}).read()\n" + GOOD
    # Either the guard denies the read, or a deliberately broken child dies; never a success.
    with pytest.raises(SandboxError):
        SandboxedMonitor(_write(tmp_path, source))
