"""Check the discrete paired bootstrap used in the WP3 reconciliation."""

import runpy
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[2] / "scripts" / "retrospective_audit"


def bootstrap_interval(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPT_DIR))
    return runpy.run_path(str(SCRIPT_DIR / "audit_wp3_paired.py"))[
        "exact_two_point_bootstrap_interval"
    ]


def test_primary_pair_exact_percentiles(monkeypatch):
    interval = bootstrap_interval(monkeypatch)
    assert interval([-1] * 9 + [0] * 11) == [-0.65, -0.25]


def test_exact_formula_rejects_other_difference_support(monkeypatch):
    interval = bootstrap_interval(monkeypatch)
    with pytest.raises(ValueError, match="requires both"):
        interval([-1, 0, 1])
