from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/promising_directions/a1_exact_separation.py"
spec = importlib.util.spec_from_file_location("a1_exact_separation", SCRIPT)
a1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a1)

ROOT = Path(a1.DEFAULT_SOLVER_ROOT)


def test_calendar_enumeration_counts():
    assert len(a1.calendars(6, 3, 2)) == 1 + 4 + 6 + 4
    assert len(a1.calendars(8, 4, 2)) == 57
    assert () in a1.calendars(6, 3, 2)
    assert len(a1.calendars(6, 3, 2, all_slots=True)) == 1 + 6 + 15 + 20


def test_grid_sizes():
    assert len(a1.grid(2)) == 144
    assert len(a1.grid(1)) == 144
    assert len(a1.adversarial_instances()) == 200


@pytest.mark.skipif(not ROOT.exists(), reason="solver root missing")
def test_sanity_cell():
    a1.verify_solver(ROOT)
    a1.load_solver(str(ROOT))
    base = {
        "T": 6, "B": 3, "d": 2, "trans": "1/10", "e0": "1/10", "e1": "9/10",
        "alpha": "1/10", "cq": "1/100", "cs": "1/10", "prior1": "1/2",
    }  # fmt: skip
    r = a1.solve_cell(base)
    assert r["J"] == "22083523/7812500"
    assert r["j_le_cstar_within_tol"]
    assert r["n_calendars"] == 15
