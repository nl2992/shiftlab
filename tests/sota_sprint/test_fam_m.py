"""P1 x P2 merge (RMM on SUI evidence): budget, null control, and Markov context carried across switches."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

import registry  # noqa: F401  (loads the RMM module fam_m builds on)
import screen
from fam_m import EXTRA, RMMSUI


def _run(name, regime, seed):
    return screen._job(("synthetic", regime, 0, seed, 7770001, [name]))[0]


def test_budget_and_null_control_short():
    for name in EXTRA:
        rows = [_run(name, "F5_dep_null_r95", s) for s in range(6)]
        assert all(r["labels"] <= 200 for r in rows)
        assert sum(r["ever_promote"] for r in rows) <= 1


def test_promotes_on_clear_late_improvement():
    rows = [_run("M_LRMD_SUI", "F1_late_400", s) for s in range(6)]
    assert sum(r["ever_promote"] for r in rows) >= 3


def test_context_carried_across_switch():
    pol = EXTRA["M_LRMD_SUI"](2000, 200, 5.0, 0.05, 0.05, 50, lambda n: np.random.default_rng(0))
    assert isinstance(pol, RMMSUI)
    pol.last = (1, 10)
    det_before = pol.det
    pol._switch_keep()
    assert pol.last == (1, 10) and pol.det is not det_before and pol.override
