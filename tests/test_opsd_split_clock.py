"""Tests for the OPSD split-clock fast channel (gate D1). Synthetic series only, plus one
optional development-window check on the real file."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shiftlab.real_tasks import OPSD_HOLDOUT_START, UNRELEASED, HoldoutAccessError
from shiftlab.real_tasks import opsd_reserve as op
from shiftlab.real_tasks import opsd_split_clock as sc

HOUR = np.timedelta64(1, "h")
MAIN_OPSD = Path(
    "C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/data/raw/opsd/2020-10-06/hourly.csv"
)
DAY = pd.Timestamp("2018-07-11")  # local date of the perturbed round


def _series(seed: int = 0) -> op.HourlySeries:
    rng = np.random.default_rng(seed)
    stamps = np.arange(
        np.datetime64("2014-12-31T23:00"), np.datetime64("2019-12-31T22:00") + HOUR, HOUR
    )
    t = np.arange(len(stamps))
    load = (
        50000
        + 8000 * np.cos(2 * np.pi * t / (24 * 365.25))
        + 9000 * np.sin(2 * np.pi * ((t % 24) - 6) / 24)
        + rng.normal(0, 1500, len(t))
    )
    index = pd.DatetimeIndex(stamps)
    return op.HourlySeries(
        pd.Series(load, index=index),
        pd.Series(load + rng.normal(0, 1200, len(t)), index=index),
        frozenset(),
    )


def _local_hours(series, day):
    start = pd.Timestamp(day).tz_localize("Europe/Berlin").tz_convert("UTC").tz_localize(None)
    end = (pd.Timestamp(day) + pd.Timedelta(days=1)).tz_localize("Europe/Berlin")
    end = end.tz_convert("UTC").tz_localize(None)
    idx = series.actual.index
    hours = idx[(idx >= start) & (idx < end)]
    local = hours.tz_localize("UTC").tz_convert("Europe/Berlin").hour
    return hours, np.asarray(local)


def _bump(series, day, which, *, actual=0.0, forecast=0.0):
    hours, local = _local_hours(series, day)
    sel = hours[which(local)]
    a, f = series.actual.copy(), series.forecast.copy()
    a[sel] += actual
    f[sel] += forecast
    return op.HourlySeries(a, f, series.irregular_days)


@pytest.fixture(scope="module")
def base():
    series = _series()
    tasks, _ = sc.build_split_clock(series)
    return series, tasks["development"]


def _round(task, day):
    local = (
        pd.DatetimeIndex(task.public.round_time).tz_localize("UTC").tz_convert("Europe/Berlin")
    ).tz_localize(None)
    return int(np.flatnonzero(local == pd.Timestamp(day))[0])


def test_fast_clock_strictly_before_next_decision_and_gap_is_one_round(base):
    _, task = base
    pub = task.public
    r = np.arange(len(task) - 1)
    assert (task.fast_available_time[r] < pub.decision_time[r + 1]).all()
    assert (task.fast_available_time[r] > pub.decision_time[r]).all()
    gold = task.base.outcomes
    delivered = (task.fast_release_round[r] < UNRELEASED) & gold.released[r]
    assert (task.fast_release_round[r][delivered] - r[delivered] == 1).all()
    assert (gold.release_round[r][delivered] - r[delivered] == 2).all()
    assert set(task.delay_gap_rounds()[r][delivered]) == {1}
    assert (task.fast_available_time <= gold.label_available_time).all()


def test_fast_available_is_0900_local_across_dst():
    days = np.array(["2018-03-25", "2018-10-28", "2018-07-11"], dtype="datetime64[D]")
    local = (
        pd.DatetimeIndex(sc.fast_available_utc(days)).tz_localize("UTC").tz_convert("Europe/Berlin")
    )
    assert list(local.hour) == [9, 9, 9]
    assert list(local.normalize().tz_localize(None).values.astype("datetime64[D]")) == list(days)


def test_zf_plus_rest_equals_gold_and_zero_on_agreement(base):
    _, task = base
    out = task.base.outcomes
    m = out.observed & task.fast_observed
    np.testing.assert_allclose(
        task.fast_paired[m] + task.rest_paired[m], out.paired_cost[m], atol=1e-12
    )
    agree = ~task.public.disagreement & task.fast_observed
    assert (task.fast_paired[agree] == 0).all()
    assert (np.abs(task.fast_paired[m]) <= 1.0).all()


def test_fast_label_depends_only_on_early_hours_of_that_day(base):
    series, task = base
    r = _round(task, DAY)
    # an incumbent forecast spike in fast hours creates a fast-window disagreement on round r
    spiked = _bump(series, DAY, lambda h: (h >= 2) & (h <= 4), forecast=60000.0)
    t1 = sc.build_split_clock(spiked)[0]["development"]
    assert t1.fast_hours_differing[r] >= 3
    assert t1.fast_paired[r] > 0  # incumbent over-procured while demand stayed below tau
    # moving hours >= 8 changes gold but not the fast label; moving hours < 8 does the converse
    late = _bump(spiked, DAY, lambda h: (h >= 10) & (h <= 12), forecast=60000.0)
    t2 = sc.build_split_clock(late)[0]["development"]
    assert t2.fast_paired[r] == pytest.approx(t1.fast_paired[r])
    assert t2.base.outcomes.paired_cost[r] != pytest.approx(t1.base.outcomes.paired_cost[r])
    early = _bump(spiked, DAY, lambda h: h < 8, actual=30000.0)
    t3 = sc.build_split_clock(early)[0]["development"]
    assert t3.fast_paired[r] != pytest.approx(t1.fast_paired[r])
    assert t3.rest_paired[r] == pytest.approx(t1.rest_paired[r])


def test_fast_missing_only_when_early_hours_missing(base):
    series, task = base
    r = _round(task, DAY)
    late_gap = _bump(series, DAY, lambda h: h == 15, actual=np.nan)
    t1 = sc.build_split_clock(late_gap)[0]["development"]
    assert t1.fast_observed[r] and not t1.base.outcomes.observed[r]
    early_gap = _bump(series, DAY, lambda h: h == 3, actual=np.nan)
    t2 = sc.build_split_clock(early_gap)[0]["development"]
    assert not t2.fast_observed[r] and not t2.base.outcomes.observed[r]


def test_public_side_identical_to_base_task(base):
    series, task = base
    plain = op.build_opsd_tasks(series)[0]["development"]
    for name in ("round_time", "decision_time", "x", "deployed_action", "reference_action"):
        np.testing.assert_array_equal(getattr(task.public, name), getattr(plain.public, name))


def test_holdout_guard_applies():
    series = _series()
    late = np.arange(OPSD_HOLDOUT_START, OPSD_HOLDOUT_START + 5 * HOUR, HOUR)
    bad = op.HourlySeries(
        pd.concat([series.actual, pd.Series(1.0, index=pd.DatetimeIndex(late))]),
        pd.concat([series.forecast, pd.Series(1.0, index=pd.DatetimeIndex(late))]),
        frozenset(),
    )
    with pytest.raises(HoldoutAccessError):
        sc.build_split_clock(bad)
    windows = (("dev", np.datetime64("2018-01-01"), np.datetime64("2020-01-02")),)
    with pytest.raises(HoldoutAccessError):
        sc.build_split_clock(series, windows)


@pytest.mark.skipif(not MAIN_OPSD.exists(), reason="raw OPSD file not available")
def test_real_dev_windows_delay_gap_and_pricing():
    tasks, _ = sc.build_split_clock(op.load_opsd_hourly(MAIN_OPSD))
    d = tasks["development"]
    assert sc.delay_summary(d)["gap_values"] == [-1, 1]
    assert sc.PRICE_GOLD > sc.PRICE_FAST_PRIMARY > 0
