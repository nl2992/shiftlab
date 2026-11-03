"""Exact binomial check for the archived P6 fixed-batch counterexample."""

import runpy
from fractions import Fraction
from pathlib import Path


def test_archived_batch_boundary_rate():
    script = (
        Path(__file__).resolve().parents[2] / "scripts/retrospective_audit/audit_batch_boundary.py"
    )
    one_batch = runpy.run_path(str(script))["one_batch_false_promotion"]
    assert one_batch(25, Fraction(3, 10)) == Fraction(1807781, 33554432)
    assert one_batch(25, Fraction(3, 10)) > Fraction(1, 20)


def test_fair_coin_repeated_batch_calibration():
    script = (
        Path(__file__).resolve().parents[2] / "scripts/retrospective_audit/audit_batch_boundary.py"
    )
    one_batch = runpy.run_path(str(script))["one_batch_false_promotion"]
    p = one_batch(25, Fraction(13, 25))
    assert 1 - (1 - p) ** 16 < Fraction(1, 20)
    previous = one_batch(25, Fraction(11, 25))
    assert 1 - (1 - previous) ** 8 > Fraction(1, 20)
