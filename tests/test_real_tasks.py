"""Tests for the Lane B real-data tasks: holdout guard, clocks, public-information contract,
bounds, determinism. Synthetic series only, except one optional dev-window check.
"""

from __future__ import annotations

import csv
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shiftlab.contract.baselines import UniformHT
from shiftlab.contract.harness import run_monitor
from shiftlab.real_tasks import (
    BINANCE_HOLDOUT_START,
    OPSD_HOLDOUT_START,
    UNRELEASED,
    HoldoutAccessError,
    guard_timestamps,
    public_stream_audit,
    run_length_summary,
)
from shiftlab.real_tasks import binance_momentum as bm
from shiftlab.real_tasks import opsd_reserve as op

HOUR = np.timedelta64(1, "h")
MAIN_OPSD = Path(
    "C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/data/raw/opsd/2020-10-06/hourly.csv"
)


# ---------------------------------------------------------------- synthetic OPSD


def _opsd_series(seed: int = 0, end: str = "2019-12-31T22:00") -> op.HourlySeries:
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
    index = pd.DatetimeIndex(stamps)
    return op.HourlySeries(
        pd.Series(load, index=index), pd.Series(forecast, index=index), frozenset()
    )


def _perturbed(series, actual_from=None, forecast_from=None, actual_hours=None, actual_day=None):
    actual, forecast = series.actual.copy(), series.forecast.copy()
    if actual_from is not None:
        actual[actual.index >= pd.Timestamp(actual_from)] += 25000.0
    if forecast_from is not None:
        forecast[forecast.index >= pd.Timestamp(forecast_from)] += 25000.0
    if actual_day is not None:  # local day, optionally restricted to local clock hours
        local = actual.index.tz_localize("UTC").tz_convert(op.BERLIN)
        mask = local.normalize().tz_localize(None) == pd.Timestamp(actual_day)
        if actual_hours is not None:
            mask = mask & np.isin(local.hour, actual_hours)
        actual[mask] += 25000.0
    return op.HourlySeries(actual, forecast, series.irregular_days)


@pytest.fixture(scope="module")
def opsd():
    series = _opsd_series()
    tasks, model = op.build_opsd_tasks(series)
    return series, tasks, model


def _same_public(a, b, upto=None):
    sl = slice(None) if upto is None else upto
    for name in ("round_time", "decision_time", "x", "deployed_action", "reference_action"):
        np.testing.assert_array_equal(getattr(a.public, name)[sl], getattr(b.public, name)[sl])


# ---------------------------------------------------------------- holdout guard


def test_guard_timestamps_boundary():
    ok = np.array(["2019-12-31T22:00"], dtype="datetime64[ns]")
    guard_timestamps(ok, OPSD_HOLDOUT_START, "x")
    with pytest.raises(HoldoutAccessError):  # first holdout delivery hour = local 2020-01-01 00:00
        guard_timestamps(
            np.array(["2019-12-31T23:00"], dtype="datetime64[ns]"), OPSD_HOLDOUT_START, "x"
        )
    with pytest.raises(HoldoutAccessError):
        guard_timestamps(
            np.array(["2026-03-01T00:00"], dtype="datetime64[ns]"), BINANCE_HOLDOUT_START, "x"
        )


def test_opsd_loader_refuses_holdout_before_opening_file(tmp_path):
    missing = tmp_path / "does_not_exist.csv"
    with pytest.raises(HoldoutAccessError):
        op.load_opsd_hourly(missing, end_exclusive=np.datetime64("2020-02-01"))
    with pytest.raises(FileNotFoundError):  # an allowed window reaches the file system
        op.load_opsd_hourly(missing)


def test_opsd_loader_checks_timestamp_before_parsing_any_field(tmp_path, monkeypatch):
    path = tmp_path / "h.csv"
    path.write_text(
        "utc_timestamp,cet,DE_load_actual_entsoe_transparency,DE_load_forecast_entsoe_transparency\n"
        "2019-12-31T21:00:00Z,x,1.0,2.0\n"
        "2019-12-31T22:00:00Z,x,3.0,4.0\n"
        '2019-12-31T23:00:00Z,"UNBALANCED,GARBAGE,GARBAGE\n'
        "2020-01-01T00:00:00Z,x,GARBAGE,GARBAGE\n",
        encoding="utf-8",
    )
    seen: list[str] = []
    real_reader = csv.reader

    def spy(lines, *args, **kwargs):
        seen.extend(lines)
        return real_reader(lines, *args, **kwargs)

    monkeypatch.setattr(csv, "reader", spy)
    series = op.load_opsd_hourly(path)
    assert len(series.actual) == 2
    assert not any(line.startswith(("2019-12-31T23", "2020")) for line in seen)


def test_opsd_build_refuses_holdout_window_and_series():
    series = _opsd_series()
    with pytest.raises(HoldoutAccessError):
        op.build_opsd_tasks(
            series, (("bad", np.datetime64("2019-06-01"), np.datetime64("2020-03-01")),)
        )
    with pytest.raises(HoldoutAccessError):
        op.build_opsd_tasks(_opsd_series(end="2020-01-02T23:00"))


def test_binance_loader_refuses_holdout_months_without_opening(tmp_path):
    with pytest.raises(HoldoutAccessError):
        bm.load_binance_bars(tmp_path, ["2026-01"])
    with pytest.raises(HoldoutAccessError):
        bm.load_binance_bars(tmp_path, ["2025-12", "2026-03"])  # none of the files exist
    with pytest.raises(FileNotFoundError):
        bm.load_binance_bars(tmp_path, ["2025-12"])


def _bars(n: int, start: str = "2025-01-01T00:00", seed: int = 1, precision: str = "ms") -> bm.Bars:
    rng = np.random.default_rng(seed)
    opens = np.arange(np.datetime64(start), np.datetime64(start) + n * HOUR, HOUR).astype(
        "datetime64[ns]"
    )
    tick = np.timedelta64(1, "ms" if precision == "ms" else "us").astype("timedelta64[ns]")
    close = 3000 * np.exp(np.cumsum(rng.normal(0, 0.004, n)))
    return bm.Bars(opens, opens + HOUR.astype("timedelta64[ns]") - tick, close)


def test_binance_build_refuses_holdout_bars():
    with pytest.raises(HoldoutAccessError):
        bm.build_binance_task(_bars(500, start="2025-12-25T00:00"))


# ---------------------------------------------------------------- OPSD local-day clocks


def test_opsd_rounds_are_local_days_with_regulatory_decision_time(opsd):
    _, tasks, _ = opsd
    task = tasks["development"]
    pub = task.public
    start_local = pd.DatetimeIndex(pub.round_time).tz_localize("UTC").tz_convert(op.BERLIN)
    decision_local = pd.DatetimeIndex(pub.decision_time).tz_localize("UTC").tz_convert(op.BERLIN)
    assert np.all(start_local.hour == 0) and np.all(start_local.minute == 0)
    assert np.all(decision_local.hour == 10) and np.all(decision_local.minute == 0)
    wall = lambda i: i.tz_localize(None).normalize()
    assert np.all(wall(decision_local) == wall(start_local) - pd.Timedelta(days=1))
    hours = pub.x[:, op.X_FIELDS.index("hours_in_local_day")]
    assert set(hours) == {23.0, 24.0, 25.0}
    assert (hours == 23).sum() == 2 and (hours == 25).sum() == 2  # 2018 and 2019 DST changes
    # every delivery hour of round D falls in [start_D, start_{D+1}): deadline is D-1 10:00 local
    nxt = np.append(pub.round_time[1:], pub.round_time[-1] + np.timedelta64(24, "h"))
    assert np.all((nxt - pub.round_time) // HOUR >= 23)


def test_opsd_label_clock_and_release(opsd):
    _, tasks, _ = opsd
    task = tasks["development"]
    pub, out = task.public, task.outcomes
    nxt_start = op.day_start_utc(pub.round_time.astype("datetime64[D]") + np.timedelta64(1, "D"))
    # NB: round_time is UTC; the local day label is recovered through the local calendar
    local_day = (
        pd.DatetimeIndex(pub.round_time)
        .tz_localize("UTC")
        .tz_convert(op.BERLIN)
        .tz_localize(None)
        .values
    ).astype("datetime64[D]")
    nxt_start = op.day_start_utc(local_day + np.timedelta64(1, "D"))
    np.testing.assert_array_equal(
        out.label_available_time, nxt_start + HOUR.astype("timedelta64[ns]")
    )
    assert np.all(out.label_available_time > pub.decision_time)
    delays = out.delay_rounds()
    assert set(delays[out.released]) == {2}  # every delivered label has d = 2
    assert int((~out.released).sum()) == 2  # the last two labels are never released in-stream
    assert np.all(delays[~out.released] == -1)  # marked unreleased, not an offset
    assert np.all(out.release_round[~out.released] >= UNRELEASED)
    inside = out.released
    assert np.all(out.label_available_time[inside] <= pub.decision_time[out.release_round[inside]])
    before = out.release_round[inside] - 1
    assert np.all(out.label_available_time[inside] > pub.decision_time[before])


def test_opsd_label_slack_shifts_release(opsd):
    series, _, _ = opsd
    tasks, _ = op.build_opsd_tasks(series, label_slack_days=1)
    task = tasks["development"]
    out = task.outcomes
    assert set(out.delay_rounds()[out.released]) == {3}
    assert int((~out.released).sum()) == 3


# ---------------------------------------------------------------- public-information contract


def test_opsd_public_x_is_calendar_only_and_ignores_all_outcomes(opsd):
    series, tasks, _ = opsd
    base = tasks["development"]
    assert base.public.x.shape[1] == len(op.X_FIELDS)
    days = (
        pd.DatetimeIndex(base.public.round_time)
        .tz_localize("UTC")
        .tz_convert(op.BERLIN)
        .tz_localize(None)
        .values.astype("datetime64[D]")
    )
    hours = base.public.x[:, -1]
    np.testing.assert_array_equal(base.public.x, op.calendar_features(days, hours))
    # perturb every outcome and forecast from 2016 on (not the training window): x is unchanged,
    # only the actions (a deliberate public channel) and later evaluator quantities may react
    other, _ = op.build_opsd_tasks(
        _perturbed(series, actual_from="2017-06-01", forecast_from="2017-06-01")
    )
    np.testing.assert_array_equal(base.public.x, other["development"].public.x)
    np.testing.assert_array_equal(base.public.round_time, other["development"].public.round_time)
    np.testing.assert_array_equal(
        base.public.decision_time, other["development"].public.decision_time
    )
    assert not np.array_equal(
        base.public.deployed_action, other["development"].public.deployed_action
    )


def test_opsd_no_future_information_in_actions(opsd):
    series, tasks, _ = opsd
    base = tasks["development"]
    s = 400
    t_dec = base.public.decision_time[s]
    cutoff = pd.Timestamp(t_dec) - pd.Timedelta(
        hours=1
    )  # hour starting 09:00 local D-1 is unpublished
    other = op.build_opsd_tasks(
        _perturbed(
            series,
            actual_from=cutoff,
            forecast_from=pd.Timestamp(base.public.round_time[s]) + pd.Timedelta(days=1),
        )
    )[0]["development"]
    _same_public(base, other, slice(0, s + 1))
    assert not np.array_equal(base.public.deployed_action, other.public.deployed_action)


def test_opsd_labels_reach_actions_no_earlier_than_release(opsd):
    """Day s's label is released at the end of day s + 1 h. Perturbing the whole day leaves every
    earlier action unchanged (there is no hour-level early disclosure)."""
    series, tasks, _ = opsd
    base = tasks["development"]
    pub, out = base.public, base.outcomes
    local_days = (
        pd.DatetimeIndex(pub.round_time).tz_localize("UTC").tz_convert(op.BERLIN).tz_localize(None)
    )
    checked = 0
    for s in np.flatnonzero(pub.disagreement & out.observed)[:3]:
        other = op.build_opsd_tasks(_perturbed(series, actual_day=local_days[s]))[0]["development"]
        rel = int(out.release_round[s])
        _same_public(base, other, slice(0, rel))
        assert other.outcomes.paired_cost[s] != out.paired_cost[s]
        checked += 1
    assert checked == 3


@pytest.mark.parametrize(
    "transition",
    ["2018-03-25", "2019-03-31", "2018-10-28", "2019-10-27"],  # spring and autumn, both years
)
def test_opsd_dst_lags_never_use_loads_released_at_or_after_decision(opsd, transition):
    """For every round D within a week either side of a DST change, perturbing every load whose
    local day is >= D-1 (released at D 01:00 local, after the decision at D-1 10:00) must leave all
    actions of rounds <= D unchanged. Elapsed-hour lags failed this on the autumn change."""
    series, tasks, _ = opsd
    base = tasks["development"]
    local_days = (
        pd.DatetimeIndex(base.public.round_time)
        .tz_localize("UTC")
        .tz_convert(op.BERLIN)
        .tz_localize(None)
        .values.astype("datetime64[D]")
    )
    tday = np.datetime64(transition)
    local_hours = series.actual.index.tz_localize("UTC").tz_convert(op.BERLIN).tz_localize(None)
    for offset in range(-2, 9):
        day = tday + np.timedelta64(offset, "D")
        r = int(np.flatnonzero(local_days == day)[0])
        actual = series.actual.copy()
        actual[local_hours.normalize() >= pd.Timestamp(day - np.timedelta64(1, "D"))] += 25000.0
        other = op.build_opsd_tasks(op.HourlySeries(actual, series.forecast, frozenset()))[0][
            "development"
        ]
        _same_public(base, other, slice(0, r + 1))


def test_opsd_lag_release_precedes_decision_for_lags_two_and_up():
    days = np.arange(
        np.datetime64("2018-03-20"), np.datetime64("2018-04-10"), dtype="datetime64[D]"
    )
    avail = op.label_available_utc(days)
    dec = op.decision_time_utc(days)
    assert np.all(avail[:-2] < dec[2:]) and np.all(avail[:-3] < dec[3:])
    assert not np.any(avail[:-1] < dec[1:])  # the previous day is never released in time


def test_opsd_stream_audit_reports_z_not_a_function_of_public_stream(opsd):
    _, tasks, _ = opsd
    audit = public_stream_audit(tasks["development"])
    assert audit["n_labelled_disagreement_rounds"] > 20
    assert audit["coarse_key"]["n_repeated_keys_with_varying_Z"] > 0


# ---------------------------------------------------------------- missing data and embargo


def test_opsd_missing_data_keeps_rounds_and_marks_missing_feedback():
    series = _opsd_series()
    actual, forecast = series.actual.copy(), series.forecast.copy()
    actual[(actual.index >= "2018-05-10T05:00") & (actual.index < "2018-05-10T07:00")] = np.nan
    forecast[(forecast.index >= "2018-08-01T00:00") & (forecast.index < "2018-08-01T03:00")] = (
        np.nan
    )
    tasks, _ = op.build_opsd_tasks(op.HourlySeries(actual, forecast, frozenset()))
    clean, _ = op.build_opsd_tasks(series)
    task, ref = tasks["development"], clean["development"]
    assert len(task) == len(ref) == 729  # 2018-01-01 .. 2019-12-30 after the embargo purge
    assert int((~task.outcomes.observed).sum()) >= 2
    miss = np.flatnonzero(~task.outcomes.observed)
    assert np.all(np.isnan(task.outcomes.paired_cost[miss]))
    assert np.all(np.isfinite(task.outcomes.label_available_time[miss].astype("int64")))
    # rounds are scheduled regardless; release rounds are identical to the clean stream
    np.testing.assert_array_equal(task.outcomes.release_round, ref.outcomes.release_round)
    np.testing.assert_array_equal(task.public.x, ref.public.x)
    assert task.exclusions["label_missing_at_release"] >= 1
    assert task.exclusions["decision_unusable_no_pair"] >= 1


def test_opsd_irregular_timestamps_found_later_do_not_veto_earlier_rounds(opsd):
    series, tasks, _ = opsd
    clean = tasks["development"]
    day = pd.Timestamp("2018-09-10")
    flagged = op.HourlySeries(
        series.actual, series.forecast, frozenset({np.datetime64("2018-09-10")})
    )
    task = op.build_opsd_tasks(flagged)[0]["development"]
    _same_public(clean, task)  # every pair, including the flagged day's, is kept
    local = pd.DatetimeIndex(task.public.round_time).tz_localize("UTC").tz_convert(op.BERLIN)
    r = int(np.flatnonzero(local.tz_localize(None).normalize() == day)[0])
    assert not task.outcomes.observed[r] and np.isnan(task.outcomes.paired_cost[r])
    assert task.outcomes.observed.sum() == clean.outcomes.observed.sum() - 1
    assert (
        task.exclusions["decision_unusable_no_pair"]
        == clean.exclusions["decision_unusable_no_pair"]
    )


def test_opsd_embargo_purges_boundary_rounds(opsd):
    series, tasks, model = opsd
    val, dev = tasks["validation"], tasks["development"]
    assert val.exclusions["purged_by_embargo"] == 1 and dev.exclusions["purged_by_embargo"] == 1
    assert val.meta["last_day"] == "2017-12-30" and dev.meta["last_day"] == "2019-12-30"
    first_dev = dev.public.decision_time[0]
    assert np.all(val.outcomes.label_available_time <= first_dev)
    holdout_first_decision = op.decision_time_utc(np.array(["2020-01-01"], dtype="datetime64[D]"))[
        0
    ]
    assert np.all(dev.outcomes.label_available_time <= holdout_first_decision)
    # outcomes of the purged boundary days cannot touch the fit or the dev stream
    _, model2 = op.build_opsd_tasks(_perturbed(series, actual_day="2017-12-31"))
    np.testing.assert_array_equal(model.beta, model2.beta)
    assert model.penalty == model2.penalty
    other = op.build_opsd_tasks(_perturbed(series, actual_day="2019-12-31"))[0]["development"]
    np.testing.assert_array_equal(dev.outcomes.paired_cost, other.outcomes.paired_cost)


def test_opsd_ridge_frozen_and_validation_only(opsd):
    series, _, model = opsd
    _, model2 = op.build_opsd_tasks(_perturbed(series, actual_from="2018-01-01"))
    np.testing.assert_array_equal(model.beta, model2.beta)
    assert model.penalty in (1.0, 10.0, 100.0, 1000.0)
    assert model.validation_mse[model.penalty] == min(model.validation_mse.values())
    _, model3 = op.build_opsd_tasks(_perturbed(series, actual_from="2016-06-01"))
    assert not np.array_equal(model.beta, model3.beta)


# ---------------------------------------------------------------- bounds and determinism


def test_opsd_paired_loss_bounds(opsd):
    _, tasks, _ = opsd
    for task in tasks.values():
        out, pub = task.outcomes, task.public
        obs = out.observed
        assert np.all((out.loss_incumbent[obs] >= 0) & (out.loss_incumbent[obs] <= 1))
        assert np.all((out.loss_candidate[obs] >= 0) & (out.loss_candidate[obs] <= 1))
        assert np.all(np.abs(out.paired_cost[obs]) <= 1.0)
        np.testing.assert_allclose(
            out.paired_cost[obs], (out.loss_incumbent - out.loss_candidate)[obs]
        )
        assert np.all(out.paired_cost[obs & ~pub.disagreement] == 0.0)  # Assumption L, exact
        assert np.array_equal(pub.disagreement, pub.disagreement_units > 0)


def test_opsd_deterministic():
    a, model_a = op.build_opsd_tasks(_opsd_series())
    b, model_b = op.build_opsd_tasks(_opsd_series())
    np.testing.assert_array_equal(model_a.beta, model_b.beta)
    np.testing.assert_array_equal(
        a["development"].public.deployed_action, b["development"].public.deployed_action
    )
    np.testing.assert_array_equal(
        a["development"].outcomes.paired_cost, b["development"].outcomes.paired_cost
    )


def test_opsd_windows_chronological(opsd):
    _, tasks, _ = opsd
    assert (
        tasks["validation"].public.round_time.max() < tasks["development"].public.round_time.min()
    )
    assert tasks["development"].outcomes.label_available_time.max() <= np.datetime64(
        "2019-12-31T10:00"
    ) - np.timedelta64(0, "h") + np.timedelta64(24, "h")


def test_informativeness_rule():
    assert not op.opsd_informative(0.019) and op.opsd_informative(0.02)
    assert op.opsd_informative(0.60) and not op.opsd_informative(0.601)


# ---------------------------------------------------------------- Binance


def test_binance_clocks_decision_at_hour_boundary_both_precisions():
    for precision, tick in (("ms", np.timedelta64(1, "ms")), ("us", np.timedelta64(1, "us"))):
        bars = _bars(900, precision=precision)
        task = bm.build_binance_task(bars)
        pub, out = task.public, task.outcomes
        n = len(task)
        assert n == 900 - 169 - 1
        np.testing.assert_array_equal(
            pub.decision_time, pub.round_time + HOUR.astype("timedelta64[ns]")
        )
        idx = np.searchsorted(bars.open_time, pub.round_time)
        # the decision instant is after the archived close stamp at either precision
        assert np.all(pub.decision_time - bars.close_time[idx] == tick.astype("timedelta64[ns]"))
        assert np.all(out.release_round[:-1] == np.arange(n - 1) + 1)  # d = 1
        assert not out.released[-1] and out.released[:-1].all()  # last label never released
        np.testing.assert_array_equal(out.label_available_time[:-1], pub.decision_time[1:])
        assert np.all(out.label_available_time > pub.decision_time)


def test_binance_loader_preserves_microsecond_close(tmp_path):
    start = int(pd.Timestamp("2025-01-01", tz="UTC").timestamp())
    rows = []
    for k in range(744):
        o = (start + 3600 * k) * 1_000_000
        rows.append(f"{o},1,1,1,{3000 + k},1,{o + 3600 * 1_000_000 - 1},1,1,1,1,0")
    with zipfile.ZipFile(tmp_path / "ETHUSDT-1h-2025-01.zip", "w") as z:
        z.writestr("ETHUSDT-1h-2025-01.csv", "\n".join(rows) + "\n")
    bars = bm.load_binance_bars(tmp_path, ["2025-01"])
    assert np.all(bars.open_time + np.timedelta64(3600_000_000_000 - 1000, "ns") == bars.close_time)


def test_binance_public_x_is_calendar_only():
    bars = _bars(900)
    task = bm.build_binance_task(bars)
    assert task.public.x.shape[1] == len(bm.X_FIELDS)
    np.testing.assert_array_equal(task.public.x, bm.calendar_features(task.public.round_time))
    # scrambling every close leaves x, round and decision times unchanged (positions react)
    other = bm.build_binance_task(
        bm.Bars(
            bars.open_time,
            bars.close_time,
            bars.close * np.exp(np.random.default_rng(9).normal(0, 0.05, 900)),
        )
    )
    np.testing.assert_array_equal(task.public.x, other.public.x)
    np.testing.assert_array_equal(task.public.decision_time, other.public.decision_time)
    assert not np.array_equal(task.public.deployed_action, other.public.deployed_action)


def test_binance_no_future_information_and_labels_reach_actions_at_release():
    bars = _bars(900)
    task = bm.build_binance_task(bars)
    pub, out = task.public, task.outcomes
    t0 = 500
    cut = np.flatnonzero(bars.open_time == pub.round_time[t0])[0]
    close = bars.close.copy()
    close[cut + 1] *= 1.5  # round t0's own label (the next bar's close)
    other = bm.build_binance_task(bm.Bars(bars.open_time, bars.close_time, close))
    _same_public(task, other, slice(0, t0 + 1))
    assert out.release_round[t0] == t0 + 1
    changed = np.flatnonzero(
        (pub.deployed_action != other.public.deployed_action)
        | (pub.reference_action != other.public.reference_action)
    )
    assert changed.size == 0 or changed.min() >= out.release_round[t0]


def test_binance_z_zero_on_agreement_and_gross_loss_formula():
    bars = _bars(1500, seed=5)
    task = bm.build_binance_task(bars)
    pub, out = task.public, task.outcomes
    agree = ~pub.disagreement
    assert agree.any() and (~agree).any()
    assert np.all(out.paired_cost[agree] == 0.0)
    # exact frozen formula: l = 0.5 (1 - clip(p r / 0.10, -1, 1)), Z = l_inc - l_cand, no fees
    c = bars.close
    t = np.arange(169, len(c) - 1)
    r = c[t + 1] / c[t] - 1
    expect = 0.5 * (1 - np.clip(pub.deployed_action * r / 0.10, -1, 1)) - 0.5 * (
        1 - np.clip(pub.reference_action * r / 0.10, -1, 1)
    )
    np.testing.assert_allclose(out.paired_cost, expect)
    assert np.all((out.loss_incumbent >= 0) & (out.loss_incumbent <= 1))
    assert np.all(np.abs(out.paired_cost) <= 1.0)


def test_binance_switch_cost_k_flows_from_fee_and_turnover_is_diagnostic_only():
    bars = _bars(1500, seed=5)
    base = bm.build_binance_task(bars)
    free = bm.build_binance_task(bars, fee=0.0)
    cheap = bm.build_binance_task(bars, fee=0.00075)
    assert base.costs.primary_switch_cost == pytest.approx(0.005)
    assert free.costs.primary_switch_cost == 0.0
    assert cheap.costs.primary_switch_cost == pytest.approx(0.00075 / 0.2)
    np.testing.assert_array_equal(base.outcomes.paired_cost, free.outcomes.paired_cost)
    np.testing.assert_array_equal(base.outcomes.loss_incumbent, free.outcomes.loss_incumbent)
    fee0 = base.outcomes.diagnostic_turnover_fee_incumbent
    assert fee0 is not None and fee0.sum() > 0
    assert np.all(free.outcomes.diagnostic_turnover_fee_incumbent == 0.0)


def test_binance_z_not_function_of_public_stream_and_determinism():
    bars = _bars(4000, seed=3)
    a, b = bm.build_binance_task(bars), bm.build_binance_task(bars)
    np.testing.assert_array_equal(a.outcomes.paired_cost, b.outcomes.paired_cost)
    audit = public_stream_audit(a)
    assert audit["coarse_key"]["n_repeated_keys_with_varying_Z"] > 0
    assert set(np.unique(a.public.deployed_action)) <= {0, 1}


# ---------------------------------------------------------------- generator + harness


def test_generator_feeds_contract_harness(opsd):
    _, tasks, _ = opsd
    task = tasks["development"]
    events = list(task.public_events())
    assert len(events) == len(task)
    assert all(e.disagreement == bool(task.public.disagreement[i]) for i, e in enumerate(events))
    spec = task.task_spec(0.10)
    costs, _ = task.harness_paired_costs()
    coins = np.random.default_rng(0).random(len(events))
    result = run_monitor(UniformHT(0.10), spec, events, costs, coins, np.ones(len(events)))
    assert result.total_spend <= spec.label_budget + 1e-9


def test_run_length_summary_runs_and_gaps():
    flags = np.array([1, 1, 0, 1, 1, 1, 0, 0, 1], dtype=bool)
    adjacent = np.ones(9, dtype=bool)
    s = run_length_summary(flags, adjacent)
    assert s["n_runs"] == 3 and s["run_length_max"] == 3
    adjacent[4] = False
    assert run_length_summary(flags, adjacent)["n_runs"] == 4


@pytest.mark.skipif(not MAIN_OPSD.exists(), reason="raw OPSD snapshot not available")
def test_real_opsd_loader_stays_in_development_window():
    series = op.load_opsd_hourly(MAIN_OPSD)
    assert series.actual.index.max() < pd.Timestamp("2019-12-31T23:00")
