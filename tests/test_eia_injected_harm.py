from __future__ import annotations

import numpy as np
import pytest

from shiftlab.dive.eia_injected_harm import (
    inject_under_procurement,
    injected_paired_cost,
    onset_index,
    select_band,
)
from shiftlab.dive.reserve_costs import paired_cost


def test_onset_index_values() -> None:
    assert onset_index(10, 0.25) == 2
    assert onset_index(7, 0.5) == 3
    assert onset_index(1, 0.9) == 0


@pytest.mark.parametrize(
    "n, fraction", [(0, 0.5), (-3, 0.5), (10, 0.0), (10, 1.0), (10, -0.1), (10, float("nan"))]
)
def test_onset_index_rejects_bad_input(n: int, fraction: float) -> None:
    with pytest.raises(ValueError):
        onset_index(n, fraction)


def _rehearsal() -> tuple[np.ndarray, np.ndarray]:
    procure_margin = np.arange(1, 21, dtype=float)  # 20 procure events, margins 1..20, median 10.5
    idle_margin = -np.ones(5)
    margin = np.concatenate([procure_margin, idle_margin])
    action = np.concatenate([np.ones(20, dtype=np.int8), np.zeros(5, dtype=np.int8)])
    return margin, action


def test_select_band_median() -> None:
    margin, action = _rehearsal()
    assert select_band(margin, action) == (0.0, 10.5)


def test_select_band_rejects_shape_mismatch() -> None:
    margin, action = _rehearsal()
    with pytest.raises(ValueError):
        select_band(margin[:-1], action)


def test_select_band_rejects_nonfinite() -> None:
    margin, action = _rehearsal()
    margin[0] = np.nan
    with pytest.raises(ValueError):
        select_band(margin, action)


def test_select_band_rejects_nonbinary() -> None:
    margin, action = _rehearsal()
    action[-1] = 2
    with pytest.raises(ValueError):
        select_band(margin, action)


def test_select_band_rejects_too_few_procure() -> None:
    margin, action = _rehearsal()
    action[0] = 0  # 19 procure events remain
    with pytest.raises(ValueError):
        select_band(margin, action)


def test_select_band_rejects_nonpositive_procure_margin() -> None:
    margin, action = _rehearsal()
    margin[0] = 0.0  # procure event with margin <= 0
    with pytest.raises(ValueError):
        select_band(margin, action)


def test_inject_only_after_onset_inside_band_on_procure() -> None:
    deployed = np.array([1, 1, 1, 1, 1, 0, 1, 1], dtype=np.int64)
    margin = np.array([0.5, 2.0, 3.0, 0.2, 1.5, 1.0, 9.0, 2.5])
    original = deployed.copy()
    margin_before = margin.copy()
    out = inject_under_procurement(deployed, margin, onset=2, band=(0.0, 2.0))
    # i=0,1 before onset; i=2 outside band; i=3,4 in band after onset -> 0;
    # i=5 in band but idle; i=6,7 outside band.
    np.testing.assert_array_equal(out, np.array([1, 1, 1, 0, 0, 0, 1, 1]))
    assert out.dtype == np.int8
    np.testing.assert_array_equal(deployed, original)
    np.testing.assert_array_equal(margin, margin_before)


@pytest.mark.parametrize(
    "deployed, margin, onset, band",
    [
        (np.array([1, 0]), np.array([0.5]), 0, (0.0, 1.0)),  # shape mismatch
        (np.array([1, 2]), np.array([0.5, 0.5]), 0, (0.0, 1.0)),  # non-binary
        (np.array([1, 1]), np.array([0.5, np.nan]), 0, (0.0, 1.0)),  # non-finite margin
        (np.array([1, 1]), np.array([0.5, 0.5]), -1, (0.0, 1.0)),  # onset < 0
        (np.array([1, 1]), np.array([0.5, 0.5]), 3, (0.0, 1.0)),  # onset > n
        (np.array([1, 1]), np.array([0.5, 0.5]), 0, (2.0, 1.0)),  # band not ordered
    ],
)
def test_inject_rejects_bad_input(
    deployed: np.ndarray, margin: np.ndarray, onset: int, band: tuple[float, float]
) -> None:
    with pytest.raises(ValueError):
        inject_under_procurement(deployed, margin, onset, band)


def test_injected_paired_cost_values() -> None:
    # tau = 1.0; demand > tau means shortfall if unprocured.
    demand = np.array([2.0, 0.5, 2.0, 0.5, 3.0])
    tau = 1.0
    reference = np.array([1, 1, 0, 0, 0], dtype=np.int8)
    deployed = np.array([1, 1, 1, 1, 0], dtype=np.int8)
    margin = np.full(5, 0.5)  # all procure events lie in band (0, 1.0]
    band = (0.0, 1.0)

    # Before injection, Z = c(deployed) - c(reference) = [0, 0, -5, 1, 0].
    np.testing.assert_array_equal(
        paired_cost(deployed, reference, demand, tau), [0.0, 0.0, -5.0, 1.0, 0.0]
    )

    new_action, z, disagree = injected_paired_cost(
        deployed, margin, reference, demand, tau, onset=0, band=band
    )

    np.testing.assert_array_equal(new_action, np.zeros(5, dtype=np.int8))
    # i=0: demand>tau, ref=1 -> c(0)=5, c(1)=0 -> Z=+5 (previously 0)
    # i=1: demand<=tau, ref=1 -> c(0)=0, c(1)=1 -> Z=-1 (previously 0)
    # i=2: demand>tau, ref=0 -> c(0)=5, c(0)=5 -> Z=0 (previously -5)
    # i=3: demand<=tau, ref=0 -> c(0)=0, c(0)=0 -> Z=0 (previously +1)
    # i=4: agreement -> Z=0
    np.testing.assert_array_equal(z, [5.0, -1.0, 0.0, 0.0, 0.0])
    assert np.all(np.abs(z) <= 5.0)
    np.testing.assert_array_equal(disagree, [True, True, False, False, False])
    # Z is zero wherever the new actions agree with the reference.
    agree = new_action == reference
    assert np.all(z[agree] == 0.0)
