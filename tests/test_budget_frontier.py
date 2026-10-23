"""Statistical utility checks for the hard-budget frontier analysis."""

import numpy as np
import pytest

from scripts.grid_search_budget_frontier import _paired_rmse_interval, _wilson


def test_wilson_interval_for_zero_events_is_not_degenerate() -> None:
    low, high = _wilson(0, 60)
    assert low == pytest.approx(0.0)
    assert high == pytest.approx(0.0603, abs=0.0002)


def test_wilson_interval_is_symmetric_at_half_successes() -> None:
    low, high = _wilson(30, 60)
    assert low == pytest.approx(1 - high)
    assert low < 0.5 < high


def test_paired_rmse_bootstrap_is_zero_for_identical_streams() -> None:
    errors = np.array([-0.2, -0.1, 0.0, 0.1, 0.2])
    delta, low, high = _paired_rmse_interval(errors, errors.copy(), seed=7, replicates=500)
    assert delta == pytest.approx(0.0)
    assert low == pytest.approx(0.0)
    assert high == pytest.approx(0.0)


def test_paired_rmse_interval_rejects_unmatched_stream_vectors() -> None:
    with pytest.raises(ValueError, match="matching nonempty vectors"):
        _paired_rmse_interval(np.ones(3), np.ones(4), seed=7, replicates=20)
