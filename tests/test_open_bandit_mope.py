from __future__ import annotations

import numpy as np
import pytest

from shiftlab.dive.open_bandit_mope import (
    build_mope_stream,
    choose_best_item,
    fixed_horizon_hoeffding_lower,
    validate_mope_path,
)


def test_choose_best_item_uses_position_and_lowest_id_tie_break() -> None:
    item_ids = np.array([0, 0, 1, 1, 0, 1], dtype=np.int64)
    positions = np.array([1, 1, 1, 1, 2, 2], dtype=np.int64)
    clicks = np.array([1, 0, 0, 0, 0, 1], dtype=np.int64)
    selected, counts, totals = choose_best_item(item_ids, positions, clicks, n_items=2)
    assert selected == 0
    assert counts.tolist() == [2, 2]
    assert totals.tolist() == [1.0, 0.0]


def test_choose_best_item_uses_smallest_id_for_equal_rates() -> None:
    selected, _, _ = choose_best_item(
        np.array([1, 0], dtype=np.int64),
        np.array([1, 1], dtype=np.int64),
        np.array([1, 1], dtype=np.int64),
        n_items=2,
    )
    assert selected == 0


def test_mope_stream_has_exact_zero_or_eighty_weights_and_paired_score() -> None:
    stream, scores = build_mope_stream(
        np.array([2, 3, 2], dtype=np.int64),
        np.array([1, 1, 0], dtype=np.int64),
        np.full(3, 1 / 80),
        target_item=2,
    )
    assert stream[:, 0].tolist() == [80.0, 0.0, 80.0]
    assert scores.tolist() == [79.0, -1.0, 0.0]


def test_mope_stream_rejects_incorrect_propensity() -> None:
    with pytest.raises(ValueError, match="propensities"):
        build_mope_stream(
            np.array([2], dtype=np.int64),
            np.array([1], dtype=np.int64),
            np.array([0.02]),
            target_item=2,
        )


def test_fixed_horizon_lower_bound_uses_declared_range() -> None:
    scores = np.array([1.0, -1.0, 0.0])
    lower = fixed_horizon_hoeffding_lower(scores, alpha=0.05, range_width=2.0)
    assert lower == pytest.approx(-2.0 * np.sqrt(np.log(20.0) / 6.0))


def test_mope_path_validation_reports_first_empty_set() -> None:
    empty = validate_mope_path(
        np.array([-1.0, 0.0, 0.1]), np.array([1.0, 0.5, 0.0]), expected_length=3
    )
    assert empty.tolist() == [2]
