"""Sandboxed execution of external adapters through the contract harness."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from shiftlab.contract import PublicEvent, TaskSpec
from shiftlab.contract.harness import run_monitor
from shiftlab.contract.isolation import check_imports
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
    with pytest.raises(SandboxError, match="FileNotFoundError"):
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
