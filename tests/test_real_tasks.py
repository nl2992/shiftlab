"""Tests for the Lane B real-data tasks: holdout guard, clocks, bounds, determinism.

Synthetic series only (no raw data), except one optional dev-window check.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shiftlab.contract.baselines import UniformHT
from shiftlab.contract.harness import run_monitor
from shiftlab.real_tasks import (
    BINANCE_HOLDOUT_START,
    OPSD_HOLDOUT_START,
    HoldoutAccessError,
    guard_timestamps,
    run_length_summary,
)
from shiftlab.real_tasks.binance_momentum import Bars, build_binance_task, load_binance_bars
from shiftlab.real_tasks.opsd_reserve import (
    DEFAULT_WINDOWS,
    HourlySeries,
    build_opsd_tasks,
    load_opsd_hourly,
    opsd_informative,
)

HOUR = np.timedelta64(1, "h")
MAIN_OPSD = Path(
    "C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/data/raw/opsd/2020-10-06/hourly.csv"
)


def _opsd_series(seed: int = 0, end: str = "2019-12-31T23:00") -> HourlySeries:
    rng = np.random.default_rng(seed)
    stamps = np.arange(np.datetime64("2014-12-31T23:00"), np.datetime64(end) + HOUR, HOUR)
    t = np.arange(len(stamps))
    hour = t % 24
    load = (
        50000
        + 8000 * np.cos(2 * np.pi * t / (24 * 365.25))
        + 9000 * np.sin(2 * np.pi * (hour - 6) / 24)
        + rng.normal(0, 1500, len(t))
    )
    forecast = load + rng.normal(0, 1200, len(t))
    series = HourlySeries(
        pd.Series(load, index=pd.DatetimeIndex(stamps)),
        pd.Series(forecast, index=pd.DatetimeIndex(stamps)),
        frozenset(),
    )
    return series


def _perturbed(
    series: HourlySeries, actual_from=None, forecast_from=None, day_only=None, hours=None
):
    actual, forecast = series.actual.copy(), series.forecast.copy()
    if actual_from is not None:
        actual[actual.index >= pd.Timestamp(actual_from)] += 25000.0
    if forecast_from is not None:
        forecast[forecast.index >= pd.Timestamp(forecast_from)] += 25000.0
    if day_only is not None:
        mask = actual.index.normalize() == pd.Timestamp(day_only)
        if hours is not None:
            mask = mask & np.isin(actual.index.hour, hours)
        actual[mask] += 25000.0
    return HourlySeries(actual, forecast, series.irregular_days)


@pytest.fixture(scope="module")
def opsd():
    series = _opsd_series()
    tasks, model = build_opsd_tasks(series)
    return series, tasks, model


# ---------------------------------------------------------------- holdout guard


def test_guard_timestamps_boundary():
    guard_timestamps(
        np.array(["2019-12-31T23:00"], dtype="datetime64[ns]"), OPSD_HOLDOUT_START, "x"
    )
    with pytest.raises(HoldoutAccessError):
        guard_timestamps(
            np.array(["2020-01-01T00:00"], dtype="datetime64[ns]"), OPSD_HOLDOUT_START, "x"
        )
    with pytest.raises(HoldoutAccessError):
        guard_timestamps(
            np.array(["2026-03-01T00:00"], dtype="datetime64[ns]"), BINANCE_HOLDOUT_START, "x"
        )


def test_opsd_loader_refuses_holdout_before_opening_file(tmp_path):
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(HoldoutAccessError):
        load_opsd_hourly(missing, end_exclusive=np.datetime64("2020-02-01"))
    with pytest.raises(FileNotFoundError):  # allowed window reaches the file system
        load_opsd_hourly(missing)


def test_opsd_loader_never_parses_holdout_rows(tmp_path):
    path = tmp_path / "h.csv"
    path.write_text(
        "utc_timestamp,cet,DE_load_actual_entsoe_transparency,DE_load_forecast_entsoe_transparency\n"
        "2019-12-31T22:00:00Z,x,1.0,2.0\n"
        "2019-12-31T23:00:00Z,x,3.0,4.0\n"
        "2020-01-01T00:00:00Z,x,GARBAGE,GARBAGE\n"
        "2020-01-01T01:00:00Z,x,GARBAGE,GARBAGE\n",
        encoding="utf-8",
    )
    series = load_opsd_hourly(path)
    assert len(series.actual) == 2
    assert series.actual.index.max() < pd.Timestamp("2020-01-01")


def test_opsd_build_refuses_holdout_window_and_series():
    series = _opsd_series()
    with pytest.raises(HoldoutAccessError):
        build_opsd_tasks(
            series, (("bad", np.datetime64("2019-06-01"), np.datetime64("2020-03-01")),)
        )
    longer = _opsd_series(end="2020-01-02T23:00")
    with pytest.raises(HoldoutAccessError):
        build_opsd_tasks(longer)


def test_binance_loader_refuses_holdout_months_without_opening(tmp_path):
    with pytest.raises(HoldoutAccessError):
        load_binance_bars(tmp_path, ["2026-01"])
    with pytest.raises(HoldoutAccessError):
        load_binance_bars(tmp_path, ["2025-12", "2026-03"])  # none of the files exist
    with pytest.raises(FileNotFoundError):
        load_binance_bars(tmp_path, ["2025-12"])


def _bars(n: int, start: str = "2025-01-01T00:00", seed: int = 1) -> Bars:
    rng = np.random.default_rng(seed)
    opens = np.arange(np.datetime64(start), np.datetime64(start) + n * HOUR, HOUR).astype(
        "datetime64[ns]"
    )
    close_time = opens + np.timedelta64(3600_000 - 1, "ms").astype("timedelta64[ns]")
    close = 3000 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    return Bars(opens, close_time, close)


def test_binance_build_refuses_holdout_bars():
    with pytest.raises(HoldoutAccessError):
        build_binance_task(_bars(500, start="2025-12-25T00:00"))


# ---------------------------------------------------------------- OPSD clocks


def test_opsd_decision_and_label_clocks(opsd):
    _, tasks, _ = opsd
    task = tasks["development"]
    pub, out = task.public, task.outcomes
    day = pub.round_time
    assert np.all(pub.decision_time == day - np.timedelta64(14, "h"))  # D-1 10:00 UTC
    assert np.all(out.label_available_time == day + np.timedelta64(25, "h"))  # D+1 01:00
    n = len(task)
    consecutive = pub.adjacent_to_previous[1:]
    assert consecutive.mean() > 0.99
    # nominal delay: a label is first visible at the decision of round t+2, never earlier
    offset = out.release_round - np.arange(n)
    assert set(offset[:-3]) == {2}
    assert np.all(out.label_available_time > pub.decision_time)
    inside = out.release_round < n
    assert np.all(out.label_available_time[inside] <= pub.decision_time[out.release_round[inside]])


def test_opsd_label_slack_shifts_release(opsd):
    series, _, _ = opsd
    tasks, _ = build_opsd_tasks(series, label_slack_days=1)
    task = tasks["development"]
    offset = task.outcomes.release_round - np.arange(len(task))
    assert set(offset[:-4]) == {3}


def test_opsd_no_future_information_in_public_round(opsd):
    series, tasks, _ = opsd
    base = tasks["development"]
    day = pd.Timestamp("2018-06-13")
    cutoff = day - pd.Timedelta(hours=16)  # D-1 08:00: first hour not yet published at T_D
    perturbed, _ = build_opsd_tasks(
        _perturbed(series, actual_from=cutoff, forecast_from=day + pd.Timedelta(days=1))
    )
    other = perturbed["development"]
    upto = base.public.round_time <= np.datetime64(day)
    assert upto.sum() > 100
    np.testing.assert_array_equal(base.public.x[upto], other.public.x[upto])
    np.testing.assert_array_equal(
        base.public.deployed_action[upto], other.public.deployed_action[upto]
    )
    np.testing.assert_array_equal(
        base.public.reference_action[upto], other.public.reference_action[upto]
    )
    # the perturbation is not vacuous: later rounds do see it
    assert not np.array_equal(base.public.x, other.public.x)


def test_opsd_labels_unused_before_release(opsd):
    """A day's 24-hour label is released at D+1 01:00. The only earlier use of day-s actuals is the
    declared hour-07 feature of round s+1 (published 09:00, before T_{s+1} = 10:00)."""
    series, tasks, _ = opsd
    base = tasks["development"]
    pub, out = base.public, base.outcomes
    all_hours = list(range(24))
    for s in (50, 300, 600):
        day = pd.Timestamp(pub.round_time[s])
        before = pub.decision_time < out.label_available_time[s]
        assert before.sum() >= s + 1
        # a first round that may see the full label is exactly the release round
        assert out.release_round[s] == np.flatnonzero(~before)[0]
        without07 = [h for h in all_hours if h != 7]
        other = build_opsd_tasks(_perturbed(series, day_only=day, hours=without07))[0][
            "development"
        ]
        np.testing.assert_array_equal(pub.x[before], other.public.x[before])
        np.testing.assert_array_equal(
            pub.deployed_action[before], other.public.deployed_action[before]
        )
        np.testing.assert_array_equal(
            pub.reference_action[before], other.public.reference_action[before]
        )
        only07 = build_opsd_tasks(_perturbed(series, day_only=day, hours=[7]))[0]["development"]
        changed = np.flatnonzero((pub.x != only07.public.x).any(axis=1) & before)
        assert list(changed) == [s + 1]  # exactly the declared edge-of-availability feature


def test_opsd_ridge_frozen_and_validation_only(opsd):
    series, _, model = opsd
    _, model2 = build_opsd_tasks(_perturbed(series, actual_from="2018-01-01"))
    np.testing.assert_array_equal(model.beta, model2.beta)
    assert model.penalty == model2.penalty
    assert model.penalty in (1.0, 10.0, 100.0, 1000.0)
    assert model.validation_mse[model.penalty] == min(model.validation_mse.values())
    # perturbing the training window must change the fit
    _, model3 = build_opsd_tasks(_perturbed(series, actual_from="2016-06-01"))
    assert not np.array_equal(model.beta, model3.beta)


# ---------------------------------------------------------------- bounds and determinism


def test_opsd_paired_loss_bounds(opsd):
    _, tasks, _ = opsd
    for task in tasks.values():
        out, pub = task.outcomes, task.public
        assert np.all((out.loss_incumbent >= 0) & (out.loss_incumbent <= 1))
        assert np.all((out.loss_candidate >= 0) & (out.loss_candidate <= 1))
        assert np.all(np.abs(out.paired_cost) <= 1.0)
        np.testing.assert_allclose(out.paired_cost, out.loss_incumbent - out.loss_candidate)
        agree = ~pub.disagreement
        assert np.all(out.paired_cost[agree] == 0.0)  # Assumption L holds exactly for OPSD
        assert np.array_equal(pub.disagreement, pub.disagreement_units > 0)


def test_opsd_deterministic():
    a, model_a = build_opsd_tasks(_opsd_series())
    b, model_b = build_opsd_tasks(_opsd_series())
    np.testing.assert_array_equal(model_a.beta, model_b.beta)
    np.testing.assert_array_equal(a["development"].public.x, b["development"].public.x)
    np.testing.assert_array_equal(
        a["development"].outcomes.paired_cost, b["development"].outcomes.paired_cost
    )


def test_opsd_windows_chronological(opsd):
    _, tasks, _ = opsd
    names = [w[0] for w in DEFAULT_WINDOWS]
    assert names == ["validation", "development"]
    assert (
        tasks["validation"].public.round_time.max() < tasks["development"].public.round_time.min()
    )
    assert tasks["development"].public.round_time.max() < np.datetime64(OPSD_HOLDOUT_START, "ns")


def test_informativeness_rule():
    assert not opsd_informative(0.019) and opsd_informative(0.02)
    assert opsd_informative(0.60) and not opsd_informative(0.601)


# ---------------------------------------------------------------- Binance clocks and bounds


def test_binance_clocks_and_actions_use_only_past_closes():
    bars = _bars(900)
    task = build_binance_task(bars)
    pub, out = task.public, task.outcomes
    n = len(task)
    assert n == 900 - 169 - 1
    assert np.all(out.release_round[:-1] == np.arange(n - 1) + 1)  # d = 1
    np.testing.assert_array_equal(out.label_available_time[:-1], pub.decision_time[1:])
    assert np.all(out.label_available_time > pub.decision_time)
    t0 = 500
    cut = np.flatnonzero(bars.open_time == pub.round_time[t0])[0]
    close = bars.close.copy()
    close[cut + 1 :] *= 1.7 ** np.arange(len(close) - cut - 1)
    other = build_binance_task(Bars(bars.open_time, bars.close_time, close))
    np.testing.assert_array_equal(pub.x[: t0 + 1], other.public.x[: t0 + 1])
    np.testing.assert_array_equal(
        pub.deployed_action[: t0 + 1], other.public.deployed_action[: t0 + 1]
    )
    np.testing.assert_array_equal(
        pub.reference_action[: t0 + 1], other.public.reference_action[: t0 + 1]
    )
    assert not np.array_equal(pub.x, other.public.x)
    # label of round t0 is the close of bar t0+1: perturbing only that bar leaves rounds <= t0
    close2 = bars.close.copy()
    close2[cut + 1] *= 1.5
    third = build_binance_task(Bars(bars.open_time, bars.close_time, close2))
    np.testing.assert_array_equal(pub.x[: t0 + 1], third.public.x[: t0 + 1])
    assert not np.array_equal(pub.x[t0 + 1], third.public.x[t0 + 1])  # visible from round t0+1


def test_binance_bounds_and_determinism():
    bars = _bars(2000, seed=3)
    a, b = build_binance_task(bars), build_binance_task(bars)
    out = a.outcomes
    assert np.all((out.loss_incumbent >= 0) & (out.loss_incumbent <= 1))
    assert np.all((out.loss_candidate >= 0) & (out.loss_candidate <= 1))
    assert np.all(np.abs(out.paired_cost) <= 1.0)
    np.testing.assert_array_equal(out.paired_cost, b.outcomes.paired_cost)
    np.testing.assert_array_equal(a.public.x, b.public.x)
    # positions are sign rules without parameters: p in {0, 1}
    assert set(np.unique(a.public.deployed_action)) <= {0, 1}
    assert a.costs.primary_switch_cost == pytest.approx(0.005)


def test_binance_fee_zero_makes_agreement_cost_zero():
    task = build_binance_task(_bars(1500, seed=5), fee=0.0)
    agree = ~task.public.disagreement
    assert np.all(task.outcomes.paired_cost[agree] == 0.0)


# ---------------------------------------------------------------- generator + harness


def test_generator_feeds_contract_harness(opsd):
    _, tasks, _ = opsd
    task = tasks["development"]
    events = list(task.public_events())
    assert len(events) == len(task)
    assert all(e.disagreement == bool(task.public.disagreement[i]) for i, e in enumerate(events))
    spec = task.task_spec(0.10)
    coins = np.random.default_rng(0).random(len(events))
    result = run_monitor(
        UniformHT(0.10), spec, events, task.outcomes.paired_cost, coins, np.ones(len(events))
    )
    assert result.total_spend <= spec.label_budget + 1e-9


def test_run_length_summary_runs_and_gaps():
    flags = np.array([1, 1, 0, 1, 1, 1, 0, 0, 1], dtype=bool)
    adjacent = np.ones(9, dtype=bool)
    s = run_length_summary(flags, adjacent)
    assert s["n_runs"] == 3 and s["run_length_max"] == 3
    adjacent[4] = False  # a calendar gap splits the second run
    assert run_length_summary(flags, adjacent)["n_runs"] == 4


@pytest.mark.skipif(not MAIN_OPSD.exists(), reason="raw OPSD snapshot not available")
def test_real_opsd_loader_stays_in_development_window():
    series = load_opsd_hourly(MAIN_OPSD)
    assert series.actual.index.max() < pd.Timestamp("2020-01-01")
