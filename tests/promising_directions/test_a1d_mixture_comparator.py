from __future__ import annotations

import importlib.util
import sys
from fractions import Fraction as F
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts/promising_directions"
sys.path.insert(0, str(SCRIPT_DIR))
spec = importlib.util.spec_from_file_location(
    "a1d_mixture_comparator", SCRIPT_DIR / "a1d_mixture_comparator.py"
)
a1d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a1d)


def pts(*xy):
    return [(F(x), F(y)) for x, y in xy]


def test_lower_hull_drops_nonconvex_and_collinear():
    hull = a1d.lower_hull(pts((0, 4), (1, 1), (2, 3), (3, 2), (4, 0), (2, 5), (1, 2)))
    assert hull == pts((0, 4), (1, 1), (4, 0))
    assert a1d.lower_hull(pts((0, 2), (1, 1), (2, 0))) == pts((0, 2), (2, 0))


def test_evaluate_interpolates_exactly():
    hull = a1d.lower_hull(pts((0, 4), (1, 1), (4, 0)))
    val, sup = a1d.evaluate(hull, F(5, 2))
    assert val == F(1, 2)
    assert sup == pts((1, 1), (4, 0))
    val, sup = a1d.evaluate(hull, F(1))
    assert val == 1
    assert sup == pts((1, 1))


def test_evaluate_uses_smaller_risk_when_envelope_rises():
    hull = a1d.lower_hull(pts((0, 1), (1, 2), (2, 5)))
    val, sup = a1d.evaluate(hull, F(3, 2))
    assert val == 1
    assert sup == pts((0, 1))
