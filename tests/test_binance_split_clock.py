"""Tests for the Binance split-clock task (gate D1b). Synthetic bars, plus one optional dev check."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from shiftlab.real_tasks import UNRELEASED, HoldoutAccessError
from shiftlab.real_tasks import binance_momentum as bm
from shiftlab.real_tasks import binance_split_clock as bs

HOUR = np.timedelta64(1, "h")
MAIN_ROOT = Path("C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/data/raw/binance")


def _bars(n=1500, start="2025-01-01T00:00", seed=3) -> bm.Bars:
    rng = np.random.default_rng(seed)
    opens = np.arange(np.datetime64(start), np.datetime64(start) + n * HOUR, HOUR).astype(
        "datetime64[ns]"
    )
    tick = np.timedelta64(1, "ms").astype("timedelta64[ns]")
    close = 3000 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
    return bm.Bars(opens, opens + HOUR.astype("timedelta64[ns]") - tick, close)


@pytest.fixture(scope="module")
def split():
    bars = _bars()
    return bars, bs.build_binance_split(bars)


def test_delays_fast_one_gold_h(split):
    _, t = split
    d = t.delays()
    assert d["fast"] == [1] and d["gold"] == [24]
    r = np.arange(len(t))
    released = t.gold_release_round < UNRELEASED
    assert (t.gold_release_round[released] - r[released] == 24).all()
    assert d["gold_unreleased"] == 24  # last H rounds: label bar t+H is beyond the last round


def test_gold_availability_is_after_decision_and_close_stamp(split):
    bars, t = split
    ok = t.gold_release_round < UNRELEASED
    r = np.arange(len(t))
    end_bar = t.first_bar + r[ok] + 24
    assert (
        t.gold_available_time[ok] == bars.open_time[end_bar] + HOUR.astype("timedelta64[ns]")
    ).all()
    assert (t.gold_available_time[ok] > bars.close_time[end_bar]).all()
    assert (t.gold_available_time[ok] > t.public.decision_time[ok]).all()
    # delivered exactly at the decision of round t+24
    assert (t.public.decision_time[t.gold_release_round[ok]] == t.gold_available_time[ok]).all()


def test_gold_zero_on_agreement_and_bounded(split):
    _, t = split
    agree = ~t.public.disagreement & np.isfinite(t.gold_paired)
    assert (t.gold_paired[agree] == 0.0).all()
    finite = t.gold_paired[np.isfinite(t.gold_paired)]
    assert np.abs(finite).max() <= 1.0
    assert (np.abs(t.gold_paired[t.public.disagreement & np.isfinite(t.gold_paired)]) > 0).any()


def test_fast_channel_is_the_base_task_z(split):
    bars, t = split
    base = bm.build_binance_task(bars)
    np.testing.assert_array_equal(t.fast_paired, base.outcomes.paired_cost)
    np.testing.assert_array_equal(t.public.deployed_action, base.public.deployed_action)


def test_gold_formula_and_horizon_window():
    bars = _bars()
    t = bs.build_binance_split(bars)
    r = int(np.flatnonzero(t.public.disagreement & np.isfinite(t.gold_paired))[5])
    b = t.first_bar + r
    ret = bars.close[b + 24] / bars.close[b] - 1
    s = 0.10 * np.sqrt(24)
    p0, p1 = int(t.public.deployed_action[r]), int(t.public.reference_action[r])
    expect = 0.5 * (1 - np.clip(p0 * ret / s, -1, 1)) - 0.5 * (1 - np.clip(p1 * ret / s, -1, 1))
    assert t.gold_paired[r] == pytest.approx(expect)
    # a close after t+H cannot change gold of round r; the close at t+H can
    later = bars.close.copy()
    later[b + 25 :] *= 1.3
    t2 = bs.build_binance_split(replace(bars, close=later))
    assert t2.gold_paired[r] == pytest.approx(t.gold_paired[r])
    moved = bars.close.copy()
    moved[b + 24 :] *= 1.3
    t3 = bs.build_binance_split(replace(bars, close=moved))
    assert t3.gold_paired[r] != pytest.approx(t.gold_paired[r])


def test_public_side_ignores_future_closes(split):
    bars, t = split
    cut = t.first_bar + 600
    later = bars.close.copy()
    later[cut + 1 :] *= 2.0
    t2 = bs.build_binance_split(replace(bars, close=later))
    for name in ("deployed_action", "reference_action", "x", "decision_time"):
        np.testing.assert_array_equal(getattr(t.public, name)[:600], getattr(t2.public, name)[:600])


def test_holdout_guard():
    with pytest.raises(HoldoutAccessError):
        bs.build_binance_split(_bars(500, start="2025-12-25T00:00"))
    with pytest.raises(HoldoutAccessError):
        bm.load_binance_bars("nonexistent", ["2026-01"])


def test_overlap_handling_rules():
    mask = bs.thinned_phase_mask(500, 24, phase=5)
    idx = np.flatnonzero(mask)
    assert (np.diff(idx) == 24).all()
    # greedy rule: after an allowed query, the next H-1 requests are refused, then allowed again
    req = np.array([0, 1, 5, 23, 24, 30, 47, 48])
    allowed = bs.greedy_nonoverlapping(req, 24)
    assert allowed.tolist() == [True, False, False, False, True, False, False, True]
    kept = req[allowed]
    assert (np.diff(kept) >= 24).all()


def test_overlap_creates_serial_dependence_and_thinning_removes_it(split):
    _, t = split
    ac = bs.gold_autocorrelation(t, lags=(1, 24))
    assert ac[1] > 0.5
    assert abs(ac[24]) < 0.2


@pytest.mark.skipif(not MAIN_ROOT.exists(), reason="raw Binance archive not available")
def test_real_dev_delays_and_floor_constant():
    t = bs.build_binance_split(
        bm.load_binance_bars(MAIN_ROOT, [f"2025-{m:02d}" for m in range(1, 13)])
    )
    assert t.delays()["fast"] == [1] and t.delays()["gold"] == [24]
    assert bs.SIGN_AGREEMENT_FLOOR == 0.6
