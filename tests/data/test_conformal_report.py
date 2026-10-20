import numpy as np

from scripts.validate_conformal_presets import (
    _conditional_coverage_passes,
    _conditional_coverage_tolerance,
)


def test_oracle_regime_coverage_gate_accounts_for_dependence_and_rejects_bad_cells():
    assert _conditional_coverage_tolerance(1200) == 8 * np.sqrt(0.09 / 1200)
    assert _conditional_coverage_passes(0.91, 1200)
    assert not _conditional_coverage_passes(0.75, 1200)
    assert not _conditional_coverage_passes(float("nan"), 1200)
    assert not _conditional_coverage_passes(0.9, 0)


def test_oracle_regime_coverage_tolerance_is_bounded_for_small_and_large_cells():
    assert _conditional_coverage_tolerance(1) == 0.15
    assert _conditional_coverage_tolerance(1_000_000) == 0.035
