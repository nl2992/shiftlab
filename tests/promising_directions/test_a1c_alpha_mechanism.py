from __future__ import annotations

import importlib.util
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts/promising_directions"
sys.path.insert(0, str(SCRIPT_DIR))
spec = importlib.util.spec_from_file_location(
    "a1c_alpha_mechanism", SCRIPT_DIR / "a1c_alpha_mechanism.py"
)
a1c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a1c)
a1 = a1c.a1

ROOT = Path(a1.DEFAULT_SOLVER_ROOT)


def test_plan_sizes():
    plan = a1c.plan()
    assert [len(plan[k]) for k in ("p1", "p2", "p3", "p4")] == [10, 14, 6, 1]


@pytest.mark.skipif(not ROOT.exists(), reason="solver root missing")
def test_wrapper_matches_solve_cell():
    a1.verify_solver(ROOT)
    a1.load_solver(str(ROOT))
    p = a1c.cell("1/5", "1/5", 6)
    base = a1.solve_cell(p)
    ext = a1c.solve_cell_ext(p)
    for k in ("J", "C_star", "best_calendar", "rel_gap", "n_calendars", "joint_nodes"):
        assert ext[k] == base[k]
    assert F(ext["joint"]["activation"]) <= 1
    assert F(ext["joint"]["calibrated_risk"]) <= F(1, 5)
