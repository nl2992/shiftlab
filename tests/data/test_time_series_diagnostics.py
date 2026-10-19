import numpy as np
import pytest

from scripts.time_series_real_diagnostics import (
    _block_length_sensitivity,
    _bootstrap_mean_interval,
)


def test_block_length_sensitivity_spans_half_baseline_and_double():
    assert _block_length_sensitivity(100) == [5, 10, 20]
    assert _block_length_sensitivity(25) == [2, 5, 10]
    with pytest.raises(ValueError, match="At least four"):
        _block_length_sensitivity(3)


def test_moving_block_interval_is_deterministic_and_ordered():
    values = np.sin(np.arange(100) / 5)
    interval = _bootstrap_mean_interval(values, seed=42, block_length=10)
    assert interval == _bootstrap_mean_interval(values, seed=42, block_length=10)
    assert interval[0] < interval[1]
