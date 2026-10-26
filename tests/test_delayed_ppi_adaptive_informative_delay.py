import numpy as np
import pytest

from shiftlab.dive.delayed_ppi_adaptive_informative_delay import _outcome_delays


def test_outcome_dependent_delays_are_assigned_by_sign():
    outcomes = np.array([1.0, -1.0, 0.25, -0.25])
    assert _outcome_delays(outcomes, "fixed12").tolist() == [12, 12, 12, 12]
    assert _outcome_delays(outcomes, "positive_fast").tolist() == [0, 12, 0, 12]
    assert _outcome_delays(outcomes, "positive_slow").tolist() == [12, 0, 12, 0]


def test_unknown_delay_profile_is_rejected():
    with pytest.raises(ValueError, match="unknown delay profile"):
        _outcome_delays(np.array([1.0]), "unknown")
