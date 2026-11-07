"""Unit tests for the Family-H Track-R merge and Pareto recomputation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

from merge_h_trackr import merge  # noqa: E402


def _point(risk: float, cost: float) -> dict:
    return {"alpha": 0.1, "risk": risk, "risk_ci": [0.0, 0.2], "cost": cost,
            "cost_ci": [cost - 1, cost + 1], "pareto": False}


def _source(candidates: dict[str, dict]) -> dict:
    return {"calibration": {name: {"R5": 0.1} for name in candidates},
            "curves": {"R5": candidates}}


def test_merge_keeps_h1_h3_and_shared_controls_once_and_recomputes_frontier():
    existing = _source({"H2": _point(.05, 10), "H4": _point(.08, 9),
                        "D2": _point(.2, 7), "A5b": _point(.05, 12)})
    added = _source({"H1": _point(.05, 11), "H3": _point(.08, 10),
                     "D2": _point(.2, 7), "A5b": _point(.05, 12)})

    result = merge(existing, added)

    assert set(result["calibration"]) == {"H1", "H2", "H3", "H4", "D2", "A5b"}
    points = result["curves"]["R5"]
    assert set(points) == {"H1", "H2", "H3", "H4", "D2", "A5b"}
    assert points["H2"]["pareto"]
    assert not points["H1"]["pareto"]  # same risk, higher cost than H2
    assert points["H4"]["pareto"]
    assert not points["H3"]["pareto"]  # same risk, higher cost than H4
    assert points["D2"]["pareto"]


def test_merge_rejects_missing_candidate_coverage():
    existing = _source({"H2": _point(.05, 10), "H4": _point(.08, 9),
                        "D2": _point(.2, 7), "A5b": _point(.05, 12)})
    added = _source({"H1": _point(.05, 11)})
    with pytest.raises(ValueError, match="expected calibrations"):
        merge(existing, added)


def test_merge_adds_rollback_variants_and_recomputes_family_frontier():
    existing = _source({"H2": _point(.05, 10), "H4": _point(.08, 9),
                        "D2": _point(.2, 7), "A5b": _point(.05, 12)})
    added = _source({"H1": _point(.05, 11), "H3": _point(.08, 10)})
    rollback = _source({"H5": _point(.04, 8), "H6-r10": _point(.04, 8.5),
                        "H6-r15": _point(.04, 9), "H6-r25": _point(.04, 9.5)})

    result = merge(existing, added, rollback)

    assert set(result["calibration"]) == {
        "H1", "H2", "H3", "H4", "H5", "H6-r10", "H6-r15", "H6-r25", "D2", "A5b"
    }
    points = result["curves"]["R5"]
    assert points["H5"]["pareto"]
    assert not points["H6-r10"]["pareto"]
    assert not points["H6-r15"]["pareto"]
    assert not points["H6-r25"]["pareto"]
