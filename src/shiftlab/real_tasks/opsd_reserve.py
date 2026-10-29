"""OPSD German day-ahead load reserve task (R1 spec A + Amendment A-R3). Development only.

Delivery rounds are Europe/Berlin local days (23, 24 or 25 hours). Decision time is exactly
10:00 local on D-1 (two hours before the 12:00 gate closure). Public ``x`` is calendar-only.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..dive.reserve_costs import (
    COST_OVER_PROCUREMENT,
    COST_SHORTFALL,
    TAU_QUANTILE,
    decision_cost,
    reserve_actions,
)
from . import (
    OPSD_HOLDOUT_START,
    CostParams,
    EvaluatorOutcomes,
    HoldoutAccessError,
    PublicRounds,
    RealTask,
    guard_timestamps,
    release_rounds,
)

ACTUAL_COLUMN = "DE_load_actual_entsoe_transparency"
FORECAST_COLUMN = "DE_load_forecast_entsoe_transparency"
BERLIN = "Europe/Berlin"
FIRST_DAY = np.datetime64("2015-01-01")  # first complete local day
LOSS_SCALE = 25.0 * COST_SHORTFALL  # 125: max daily cost on a 25-hour day maps the loss to [0, 1]
TAU_WINDOW_DAYS = 364
TAU_MIN_COVERAGE = 0.90
TRAIN_END = np.datetime64("2016-12-31")
VALIDATION_START = np.datetime64("2017-01-01")
VALIDATION_END = np.datetime64("2017-12-31")
PENALTY_GRID = (1.0, 10.0, 100.0, 1000.0)
ONE_HOUR = np.timedelta64(1, "h")
DEFAULT_WINDOWS = (
    ("validation", VALIDATION_START, VALIDATION_END),
    ("development", np.datetime64("2018-01-01"), np.datetime64("2019-12-31")),
)
X_FIELDS = (
    *(f"dow{i}" for i in range(7)),
    "doy_sin1",
    "doy_cos1",
    "doy_sin2",
    "doy_cos2",
    "hours_in_local_day",
)
COSTS = CostParams(
    budget_fractions=(0.05, 0.10, 0.25),
    primary_budget=0.10,
    query_costs=(0.0, 1.0 / LOSS_SCALE, 3.0 / LOSS_SCALE),
    primary_query_cost=1.0 / LOSS_SCALE,
    switch_costs=(10.0 / LOSS_SCALE, 25.0 / LOSS_SCALE, 50.0 / LOSS_SCALE),
    primary_switch_cost=25.0 / LOSS_SCALE,
    description="imposed research costs (raw 1/3 idle-hours, 10/25/50 units, normalised by 125)",
)


@dataclass(frozen=True)
class HourlySeries:
    actual: pd.Series
    forecast: pd.Series
    irregular_days: frozenset  # local days (datetime64[D]) containing an irregular timestamp


# ----------------------------------------------------------------------------- loading


def load_opsd_hourly(path: str | Path, end_exclusive=OPSD_HOLDOUT_START) -> HourlySeries:
    """Stream the OPSD hourly file, keeping only rows strictly before ``end_exclusive``.

    The guard runs before the file is opened. Each data line is split only at its timestamp
    prefix (first 19 characters, fixed-format UTC ISO) and compared with the cutoff; a line at or
    past the cutoff ends reading and none of its fields are parsed (``csv`` never sees it).
    """
    cutoff = np.datetime64(end_exclusive, "s")
    if cutoff > OPSD_HOLDOUT_START.astype("datetime64[s]"):
        raise HoldoutAccessError(f"OPSD rows at or after {OPSD_HOLDOUT_START} are locked")
    stamps: list[str] = []
    actual: list[float] = []
    forecast: list[float] = []
    with open(path, encoding="utf-8", newline="") as handle:
        header = next(csv.reader([handle.readline()]))
        ia, ib = header.index(ACTUAL_COLUMN), header.index(FORECAST_COLUMN)
        for line in handle:
            stamp = line[:19]
            if np.datetime64(stamp) >= cutoff:
                break
            row = next(csv.reader([line]))
            stamps.append(stamp)
            actual.append(float(row[ia]) if row[ia] != "" else np.nan)
            forecast.append(float(row[ib]) if row[ib] != "" else np.nan)
    return _hourly_series(stamps, actual, forecast)


def _hourly_series(stamps, actual, forecast) -> HourlySeries:
    index = pd.DatetimeIndex(np.asarray(stamps, dtype="datetime64[ns]"))
    guard_timestamps(index.values, OPSD_HOLDOUT_START, "OPSD series")
    gaps = np.diff(index.values.astype("datetime64[s]")).astype(np.int64)
    bad = index[np.flatnonzero(gaps != 3600) + 1]
    local = bad.tz_localize("UTC").tz_convert(BERLIN).tz_localize(None).normalize()
    irregular = frozenset(local.values.astype("datetime64[D]"))
    frame = pd.DataFrame({"a": actual, "f": forecast}, index=index)
    frame = frame[~frame.index.duplicated(keep="first")].sort_index()
    return HourlySeries(frame["a"], frame["f"], irregular)


# ----------------------------------------------------------------------------- clocks


def _utc(local_naive: pd.DatetimeIndex) -> np.ndarray:
    return (
        local_naive.tz_localize(BERLIN, ambiguous="NaT", nonexistent="NaT")
        .tz_convert("UTC")
        .tz_localize(None)
        .values.astype("datetime64[ns]")
    )


def day_start_utc(days: np.ndarray) -> np.ndarray:
    """UTC instant of local midnight at the start of each local day."""
    return _utc(pd.DatetimeIndex(np.asarray(days).astype("datetime64[ns]")))


def decision_time_utc(days: np.ndarray) -> np.ndarray:
    """10:00 local on D-1, the regulatory deadline for day D's day-ahead forecasts."""
    local = np.asarray(days).astype("datetime64[D]") - np.timedelta64(1, "D")
    return _utc(pd.DatetimeIndex(local.astype("datetime64[ns]") + np.timedelta64(10, "h")))


def label_available_utc(days: np.ndarray, slack_days: int = 0) -> np.ndarray:
    """End of the local delivery day plus one hour (Art. 6(2)(a) latest publication)."""
    nxt = np.asarray(days).astype("datetime64[D]") + np.timedelta64(1, "D")
    return day_start_utc(nxt) + ONE_HOUR + np.timedelta64(24 * slack_days, "h")


def calendar_features(days: np.ndarray, hours_in_day: np.ndarray) -> np.ndarray:
    """Public calendar fields of local days (``X_FIELDS`` order); no outcome information."""
    days = np.asarray(days).astype("datetime64[D]")
    dow = (days.astype(np.int64) + 3) % 7  # 1970-01-01 is a Thursday; Monday = 0
    doy = (days - days.astype("datetime64[Y]")).astype(np.int64) + 1
    angle = 2 * np.pi * doy / 365.25
    harmonics = np.stack(
        [np.sin(angle), np.cos(angle), np.sin(2 * angle), np.cos(2 * angle)], axis=1
    )
    return np.concatenate(
        [np.eye(7)[dow], harmonics, np.asarray(hours_in_day, dtype=float)[:, None]], axis=1
    )


# ----------------------------------------------------------------------------- model


@dataclass(frozen=True)
class RidgeModel:
    penalty: float
    mean: np.ndarray  # (24, nf)
    scale: np.ndarray  # (24, nf)
    intercept: np.ndarray  # (24,)
    beta: np.ndarray  # (24, nf)
    validation_mse: dict
    n_train: int
    n_validation_days: int

    def predict(self, features: np.ndarray, slot: np.ndarray) -> np.ndarray:
        z = (features - self.mean[slot]) / self.scale[slot]
        return self.intercept[slot] + np.einsum("rf,rf->r", z, self.beta[slot])


def fit_frozen_ridge(features, target, slot, row_day_date, validation_days, penalties=PENALTY_GRID):
    """Train on local 2015-2016; choose the penalty on the embargoed local-2017 days; no refit."""
    train = row_day_date <= TRAIN_END
    valid = np.isin(row_day_date, validation_days)
    nf = features.shape[1]
    mean, scale = np.zeros((24, nf)), np.ones((24, nf))
    ok_rows = {}
    for h in range(24):
        ok = train & (slot == h) & np.isfinite(features).all(axis=1) & np.isfinite(target)
        ok_rows[h] = ok
        mean[h] = features[ok].mean(axis=0)
        sd = features[ok].std(axis=0)
        scale[h] = np.where(sd > 0, sd, 1.0)
    mse, fits = {}, {}
    for penalty in penalties:
        beta, intercept = np.zeros((24, nf)), np.zeros(24)
        for h in range(24):
            ok = ok_rows[h]
            xs = (features[ok] - mean[h]) / scale[h]
            intercept[h] = target[ok].mean()
            gram = xs.T @ xs + penalty * np.eye(nf)
            beta[h] = np.linalg.solve(gram, xs.T @ (target[ok] - intercept[h]))
        model = RidgeModel(
            penalty, mean, scale, intercept, beta, {}, int(ok_rows[0].sum()), len(validation_days)
        )
        pred = model.predict(features, slot)
        ok = valid & np.isfinite(pred) & np.isfinite(target)
        mse[penalty] = float(np.mean((pred[ok] - target[ok]) ** 2))
        fits[penalty] = model
    best = min(penalties, key=lambda p: (mse[p], p))
    c = fits[best]
    return RidgeModel(
        best, c.mean, c.scale, c.intercept, c.beta, mse, c.n_train, c.n_validation_days
    )


def opsd_informative(disagreement_share: float) -> bool:
    """R1 A.7 rule: the task is uninformative if disagreement share is below 2% or above 60%."""
    return 0.02 <= disagreement_share <= 0.60


def _pack(actions: np.ndarray) -> int:
    return int(sum(int(a) << h for h, a in enumerate(actions)))


def _days(first, last):
    return np.arange(first, last + np.timedelta64(1, "D"), dtype="datetime64[D]")


# ----------------------------------------------------------------------------- build


def build_opsd_tasks(
    series: HourlySeries,
    windows=DEFAULT_WINDOWS,
    *,
    label_slack_days: int = 0,
    fixed_tau: bool = False,
) -> tuple[dict[str, RealTask], RidgeModel]:
    """Fit the frozen ridge and build one ``RealTask`` per window.

    Every scheduled local day in a window is a round, except rounds purged by the embargo: a
    window's rounds must have their labels released no later than the decision of the first round
    after the window (so no label is released after the next block opens). Missing data never
    removes a round; a missing label is missing feedback at release.
    """
    for _, _, end in windows:
        guard_timestamps(
            day_start_utc(np.array([end]).astype("datetime64[D]")),
            OPSD_HOLDOUT_START,
            "OPSD window end",
        )
    guard_timestamps(series.actual.index.values, OPSD_HOLDOUT_START, "OPSD series")

    def embargoed(first, end):
        days = _days(first, end)
        next_decision = decision_time_utc(np.array([end + np.timedelta64(1, "D")]))[0]
        avail = label_available_utc(days, label_slack_days)
        return days, avail <= next_decision

    purged_counts, window_days = {}, {}
    for name, start, end in windows:
        days, keep = embargoed(start, end)
        window_days[name] = days[keep]
        purged_counts[name] = int((~keep).sum())
    val_days, val_keep = embargoed(VALIDATION_START, VALIDATION_END)
    validation_days = val_days[val_keep]
    last_day = max(d[-1] for d in window_days.values() if len(d))
    all_days = _days(FIRST_DAY, last_day)
    starts = day_start_utc(_days(FIRST_DAY, last_day + np.timedelta64(1, "D")))
    guard_timestamps(starts, OPSD_HOLDOUT_START, "OPSD table")
    n_hours = (np.diff(starts) // ONE_HOUR.astype("timedelta64[ns]")).astype(np.int64)
    idx = pd.date_range(starts[0], starts[-1], freq="h", inclusive="left")
    assert len(idx) == n_hours.sum()
    actual = series.actual.reindex(idx).to_numpy(float)
    forecast = series.forecast.reindex(idx).to_numpy(float)
    offsets = np.concatenate([[0], np.cumsum(n_hours)])
    row_day = np.repeat(np.arange(len(all_days)), n_hours)
    row_date = all_days[row_day]
    slot = idx.tz_localize("UTC").tz_convert(BERLIN).hour.to_numpy()

    # Lags by local calendar day and local delivery slot (not elapsed hours): the value of the same
    # local clock hour 2, 3 and 7 local days earlier. Ambiguous autumn 02:00 uses its first
    # occurrence; the missing spring 02:00 slot falls back to the preceding slot. A lag is used
    # only if its source day's label release (local day end + 1 h) is strictly before the round's
    # decision time, so no feature depends on a load released at or after D-1 10:00 local.
    first = np.ones(len(actual), dtype=bool)
    first[1:] = (row_day[1:] != row_day[:-1]) | (slot[1:] != slot[:-1])
    table = np.full((len(all_days), 24), np.nan)
    exists = np.zeros((len(all_days), 24), dtype=bool)
    table[row_day[first], slot[first]] = actual[first]
    exists[row_day[first], slot[first]] = True
    for s_ in range(1, 24):
        gap = ~exists[:, s_]
        table[gap, s_] = table[gap, s_ - 1]
    release_by_day = label_available_utc(all_days)  # nominal clock; slack only delays delivery
    decision_by_day = decision_time_utc(all_days)

    def lag(k):
        out = np.full(len(actual), np.nan)
        src = row_day - k
        ok = src >= 0
        ok[ok] &= release_by_day[src[ok]] < decision_by_day[row_day[ok]]
        out[ok] = table[src[ok], slot[ok]]
        return out

    cal = calendar_features(all_days, n_hours)[:, :-1]  # calendar block without day length
    blocks = [lag(2)[:, None], lag(3)[:, None], lag(7)[:, None], cal[row_day]]
    features = np.concatenate(blocks, axis=1)

    model = fit_frozen_ridge(features, actual, slot, row_date, validation_days)
    pred = model.predict(features, slot)
    train_values = actual[row_date <= TRAIN_END]
    train_tau = float(np.quantile(train_values[np.isfinite(train_values)], TAU_QUANTILE))

    tasks = {}
    for name, _, _ in windows:
        tasks[name] = _build_window(
            name,
            window_days[name],
            all_days,
            offsets,
            actual,
            forecast,
            pred,
            features,
            n_hours,
            series.irregular_days,
            label_slack_days,
            train_tau if fixed_tau else None,
            model,
            purged_counts[name],
        )
    return tasks, model


def _rolling_tau(actual: np.ndarray, offsets: np.ndarray, i: int) -> float:
    """0.90 quantile of hourly actuals of local days i-365..i-2 (364 days) or NaN."""
    if i < TAU_WINDOW_DAYS + 1:
        return float("nan")
    window = actual[offsets[i - TAU_WINDOW_DAYS - 1] : offsets[i - 1]]
    finite = window[np.isfinite(window)]
    if finite.size < TAU_MIN_COVERAGE * window.size:
        return float("nan")
    return float(np.quantile(finite, TAU_QUANTILE))


def _build_window(
    name,
    days,
    all_days,
    offsets,
    actual,
    forecast,
    pred,
    features,
    n_hours,
    irregular,
    slack,
    fixed_tau,
    model,
    purged,
) -> RealTask:
    n = len(days)
    day_index = np.searchsorted(all_days, days)
    dep, ref, units = np.zeros(n, np.int64), np.zeros(n, np.int64), np.zeros(n, np.int64)
    loss0, loss1 = np.full(n, np.nan), np.full(n, np.nan)
    observed = np.zeros(n, dtype=bool)
    invalid = 0
    for r, i in enumerate(day_index):
        rows = slice(offsets[i], offsets[i + 1])
        tau = fixed_tau if fixed_tau is not None else _rolling_tau(actual, offsets, int(i))
        usable = (
            np.isfinite(forecast[rows]).all() and np.isfinite(pred[rows]).all() and np.isfinite(tau)
        )
        if not usable:  # known at decision time: no policy pair can be formed
            invalid += 1
            continue
        a0, a1 = reserve_actions(forecast[rows], tau), reserve_actions(pred[rows], tau)
        dep[r], ref[r], units[r] = _pack(a0), _pack(a1), int((a0 != a1).sum())
        # archived-timestamp irregularities are found in later data: they only affect the label
        if np.isfinite(actual[rows]).all() and days[r] not in irregular:
            observed[r] = True
            loss0[r] = decision_cost(a0, actual[rows], tau).sum() / LOSS_SCALE
            loss1[r] = decision_cost(a1, actual[rows], tau).sum() / LOSS_SCALE
    day_ns = day_start_utc(days)
    decision = decision_time_utc(days)
    available = label_available_utc(days, slack)
    x = calendar_features(days, n_hours[day_index])
    adjacent = np.zeros(n, dtype=bool)
    adjacent[1:] = np.diff(days.astype(np.int64)) == 1
    public = PublicRounds(day_ns, decision, x, dep, ref, units, adjacent)
    outcomes = EvaluatorOutcomes(
        loss0,
        loss1,
        loss0 - loss1,
        available,
        release_rounds(decision, available),
        label_observed=observed,
    )
    return RealTask(
        f"opsd_reserve_{name}",
        public,
        outcomes,
        COSTS,
        1.0,
        1.0,
        {
            "purged_by_embargo": purged,
            "decision_unusable_no_pair": invalid,
            "label_missing_at_release": int((~observed).sum()) - invalid,
        },
        {
            "ridge_penalty": model.penalty,
            "x_fields": X_FIELDS,
            "label_slack_days": slack,
            "shortfall": COST_SHORTFALL,
            "idle": COST_OVER_PROCUREMENT,
            "first_day": str(days[0]) if n else None,
            "last_day": str(days[-1]) if n else None,
            "n_validation_days": model.n_validation_days,
        },
    )
