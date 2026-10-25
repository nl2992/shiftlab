import pytest

from shiftlab.dive.budgeted_promotion_context_calibration import (
    FAMILY_CELLS,
    _cp_upper,
    _profile_name,
)


def test_null_calibration_has_frozen_36_cell_simultaneous_family():
    assert FAMILY_CELLS == 36
    assert _profile_name(0.9, 0.25, 0.05) == "context_p90_error25_switch05"


def test_exact_upper_bound_is_valid_and_monotone_in_event_count():
    cell_alpha = 0.05 / FAMILY_CELLS
    zero_error_upper = _cp_upper(0, 1000, cell_alpha)
    larger_error_upper = _cp_upper(5, 1000, cell_alpha)
    assert 0 < zero_error_upper < 0.05
    assert zero_error_upper < larger_error_upper < 0.05


@pytest.mark.parametrize(
    ("events", "trials", "alpha"),
    [(-1, 10, 0.05), (11, 10, 0.05), (0, 0, 0.05), (0, 10, 1.0)],
)
def test_exact_upper_bound_rejects_invalid_inputs(events, trials, alpha):
    with pytest.raises(ValueError):
        _cp_upper(events, trials, alpha)
