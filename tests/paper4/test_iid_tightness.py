"""Fast checks for the IID-tightness checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from shiftlab.paper4.iid_tightness import (
    CELL_TABLE,
    bitset_violations,
    check_cell,
    cover_violations,
    make_cell,
    tape_masks,
)


def _g(horizon, fn):
    n = 1 << horizon
    out = np.zeros(n)
    for idx in range(n):
        y = [(idx >> (horizon - t)) & 1 for t in range(1, horizon + 1)]
        out[idx] = fn(y)
    return out


def test_monotone_detection_hand_built():
    assert cover_violations(_g(2, lambda y: float(y[0] or y[1])), 2)["monotone"]
    assert cover_violations(_g(2, lambda y: 0.5 * y[0]), 2)["monotone"]
    bad = cover_violations(_g(2, lambda y: float(y[0] == 0 and y[1] == 1)), 2)
    assert not bad["monotone"]
    assert bad["max_violation"] == 1.0
    # y = (0,1) -> setting y_1 = 1 gives (1,1): G drops from 1 to 0
    assert bad["n_violating_covers"] == 1
    assert bad["witnesses"][0] == {"y": "01", "t": 1, "G_y": 1.0, "G_y_with_t_set_to_1": 0.0}


def test_bitset_monotone_detection_matches_array():
    horizon = 3
    m0, _ = tape_masks(horizon)
    for fn in (lambda y: y[0] or y[2], lambda y: y[0] == 0 and y[1] == 1, lambda y: y[1] != y[2]):
        values = _g(horizon, lambda y, fn=fn: float(fn(y)))
        event = sum(1 << i for i, v in enumerate(values) if v)
        count, _ = bitset_violations(event, horizon, m0)
        assert count == cover_violations(values, horizon)["n_violating_covers"]


def test_cells_match_scale_runner():
    path = Path(__file__).resolve().parents[2] / "scripts" / "paper4" / "run_fcg_scale.py"
    spec = importlib.util.spec_from_file_location("run_fcg_scale", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("S1", "S2", "S3", "C6"):
        assert make_cell(name) == module.make(name)
    assert set(CELL_TABLE) == {"C1", "C2", "C3", "C4", "C5", "C6", "S1", "S2", "S3"}


def test_c1_is_iid_safe_and_checker_runs():
    result = check_cell(*make_cell("C1"))
    assert result["iid_safe_exact_equality"]
    assert result["R_IID"] == "1/10"
    assert result["G"]["n_covers"] == 5 * 16
    assert result["classification"] in {"EXPLAINED", "NOT EXPLAINED", "UNRESOLVED"}
    assert result["consistency_flags"] == []


def test_c2_unsafe_is_not_monotone_explained():
    """C2 is IID-unsafe (R_causal = 1/5): the theorem forbids all-monotone plans."""
    result = check_cell(*make_cell("C2"))
    assert result["R_causal"] == "1/5"
    assert not result["iid_safe_exact_equality"]
    assert result["classification"] is None
    assert not result["contrast_check"].startswith("CONTRADICTION")
    assert result["consistency_flags"] == []
    plans = result["plans"]
    assert plans["enumerated"]
    assert (not result["G"]["monotone"]) or plans["n_non_monotone_plans"] > 0


def test_cover_violations_rejects_wrong_length():
    with pytest.raises(ValueError):
        cover_violations(np.zeros(3), 2)
