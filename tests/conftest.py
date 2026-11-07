"""Isolate flat script imports between test modules.

Scripts under ``scripts/`` and ``research/`` use flat module names (``regimes``, ``registry``,
``simulator``, ``suite``, ...) that repeat across folders, and each test file puts its own folder
on ``sys.path``. Without isolation, the first test file to import ``regimes`` decides which one
every later file gets. Before each test module is collected, reset ``sys.path`` and forget cached
repo modules (outside ``src/``, ``tests/`` and ``.venv/``) so the module's own path setup applies.
"""

from __future__ import annotations

import os
import sys
from functools import cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_KEEP = tuple(str(ROOT / d) + os.sep for d in ("src", "tests", ".venv"))
_BASE_PATH = list(sys.path)


@cache
def _is_repo_path(path: str) -> bool:
    path = str(Path(path).resolve())
    return path.startswith(str(ROOT) + os.sep) and not path.startswith(_KEEP)


def _is_repo_script(module: object) -> bool:
    path = getattr(module, "__file__", None)
    return bool(path) and _is_repo_path(path)


def pytest_collectstart(collector: pytest.Collector) -> None:
    if not isinstance(collector, pytest.Module):
        return
    sys.path[:] = _BASE_PATH
    for name in [n for n, m in list(sys.modules.items()) if _is_repo_script(m)]:
        del sys.modules[name]
