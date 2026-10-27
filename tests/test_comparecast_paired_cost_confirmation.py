"""Exact-interval checks for Comparecast's registered alternative confirmation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from scipy.stats import binom

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from confirm_comparecast_paired_cost import cp_interval


def test_simultaneous_interval_uses_bonferroni_adjusted_exact_binomial_tails() -> None:
    lower, upper = cp_interval(90, 300, family_alpha=0.05, family_cells=8)
    tail = 0.05 / 16
    assert lower < 0.3 < upper
    assert binom.sf(89, 300, lower) == pytest.approx(tail, rel=1e-8)
    assert binom.cdf(90, 300, upper) == pytest.approx(tail, rel=1e-8)


def test_boundary_counts_produce_valid_closed_probability_intervals() -> None:
    lower_zero, upper_zero = cp_interval(0, 300, family_alpha=0.05)
    assert lower_zero == 0.0
    assert 0 < upper_zero < 0.05
    lower, upper = cp_interval(300, 300, family_alpha=0.05)
    assert 0.0 < lower < 1.0
    assert upper == 1.0


@pytest.mark.parametrize(
    "events,trials,alpha,cells",
    [(-1, 300, 0.05, 8), (301, 300, 0.05, 8), (1, 0, 0.05, 8), (1, 300, 1.0, 8), (1, 300, 0.05, 0)],
)
def test_invalid_interval_inputs_raise(events: int, trials: int, alpha: float, cells: int) -> None:
    with pytest.raises(ValueError):
        cp_interval(events, trials, family_alpha=alpha, family_cells=cells)
