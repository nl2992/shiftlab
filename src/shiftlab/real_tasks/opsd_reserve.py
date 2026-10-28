"""OPSD German day-ahead load reserve task (R1 spec A). Development windows only."""

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
FIRST_FULL_DAY = np.datetime64("2015-01-01")
LOSS_SCALE = 24.0 * COST_SHORTFALL  # 120: max daily cost, maps the loss to [0, 1]
TAU_WINDOW_DAYS = 364
TAU_MIN_COVERAGE = 0.90
TRAIN_END = np.datetime64("2016-12-31")
VALIDATION_START = np.datetime64("2017-01-01")
VALIDATION_END = np.datetime64("2017-12-31")
PENALTY_GRID = (1.0, 10.0, 100.0, 1000.0)
DECISION_OFFSET = np.timedelta64(14, "h")  # T_D = D-1 10:00 UTC = D 00:00 - 14 h
LABEL_AVAILABLE_OFFSET = np.timedelta64(25, "h")  # D+1 01:00 UTC
DEFAULT_WINDOWS = (
    ("validation", np.datetime64("2017-01-01"), np.datetime64("2017-12-31")),
    ("development", np.datetime64("2018-01-01"), np.datetime64("2019-12-31")),
)
COSTS = CostParams(
    budget_fractions=(0.05, 0.10, 0.25),
    primary_budget=0.10,
    query_costs=(0.0, 1.0 / LOSS_SCALE, 3.0 / LOSS_SCALE),
    primary_query_cost=1.0 / LOSS_SCALE,
    switch_costs=(10.0 / LOSS_SCALE, 25.0 / LOSS_SCALE, 50.0 / LOSS_SCALE),
    primary_switch_cost=25.0 / LOSS_SCALE,
    description="imposed research costs (raw 1/3 idle-hours, 10/25/50 units, normalised by 120)",
)


@dataclass(frozen=True)
class HourlySeries:
    actual: pd.Series
    forecast: pd.Series
    irregular_days: frozenset


def load_opsd_hourly(path: str | Path, end_exclusive=OPSD_HOLDOUT_START) -> HourlySeries:
    """Stream the OPSD hourly file and keep only rows strictly before ``end_exclusive``.

    The guard runs before the file is opened. Reading stops at the first row at or past the
    cutoff; rows from the cutoff on are never parsed (only their timestamp prefix is compared).
    """
    cutoff = np.datetime64(end_exclusive, "s")
    if cutoff > OPSD_HOLDOUT_START.astype("datetime64[s]"):
        raise HoldoutAccessError(f"OPSD rows at or after {OPSD_HOLDOUT_START} are locked")
    stamps: list[str] = []
    actual: list[float] = []
    forecast: list[float] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        ia, ib = header.index(ACTUAL_COLUMN), header.index(FORECAST_COLUMN)
        for row in reader:
            stamp = row[0][:19]
            if np.datetime64(stamp) >= cutoff:
                break
            stamps.append(stamp)
            actual.append(float(row[ia]) if row[ia] != "" else np.nan)
            forecast.append(float(row[ib]) if row[ib] != "" else np.nan)
    return _hourly_series(stamps, actual, forecast)


def _hourly_series(stamps, actual, forecast) -> HourlySeries:
    index = pd.DatetimeIndex(np.asarray(stamps, dtype="datetime64[ns]"))
    guard_timestamps(index.values, OPSD_HOLDOUT_START, "OPSD series")
    gaps = np.diff(index.values.astype("datetime64[s]")).astype(np.int64)
    bad = np.flatnonzero(gaps != 3600) + 1
    irregular = frozenset(index[i].to_datetime64().astype("datetime64[D]") for i in bad)
    frame = pd.DataFrame({"a": actual, "f": forecast}, index=index)
    frame = frame[~frame.index.duplicated(keep="first")].sort_index()
    return HourlySeries(frame["a"], frame["f"], irregular)


def _day_matrix(series: pd.Series, first: np.datetime64, last: np.datetime64):
    days = np.arange(first, last + np.timedelta64(1, "D"), dtype="datetime64[D]")
    hours = pd.date_range(days[0].astype("datetime64[ns]"), periods=len(days) * 24, freq="h")
    return days, series.reindex(hours).to_numpy(float).reshape(len(days), 24)


def feature_tensor(actual: np.ndarray, days: np.ndarray, *, drop_lag07: bool = False):
    """(days, 24, nf) candidate features; row i uses only actuals of days <= i-1 and hours <= 07 of
    day i-1 (decision time D-1 10:00 UTC; hour-end plus 1 h publication lag)."""
    n = len(days)
    lags = np.full((n, 24, 3), np.nan)
    for j, lag in enumerate((2, 3, 7)):
        lags[lag:, :, j] = actual[:-lag, :]
    lag07 = np.full((n,), np.nan)
    lag07[1:] = actual[:-1, 7]
    dow = (days.astype("datetime64[D]").astype(np.int64) + 3) % 7  # 1970-01-01 is a Thursday
    onehot = np.eye(7)[dow]
    doy = (days - days.astype("datetime64[Y]")).astype(np.int64) + 1
    angle = 2 * np.pi * doy / 365.25
    harmonics = np.stack(
        [np.sin(angle), np.cos(angle), np.sin(2 * angle), np.cos(2 * angle)], axis=1
    )
    common = [onehot, harmonics] if drop_lag07 else [lag07[:, None], onehot, harmonics]
    block = np.concatenate(common, axis=1)
    tiled = np.broadcast_to(block[:, None, :], (n, 24, block.shape[1]))
    return np.concatenate([lags, tiled], axis=2)


@dataclass(frozen=True)
class RidgeModel:
    penalty: float
    mean: np.ndarray  # (24, nf) train feature mean
    scale: np.ndarray  # (24, nf) train feature sd
    intercept: np.ndarray  # (24,)
    beta: np.ndarray  # (24, nf)
    validation_mse: dict
    n_train: int

    def predict(self, features: np.ndarray) -> np.ndarray:
        z = (features - self.mean[None]) / self.scale[None]
        return self.intercept[None] + np.einsum("dhf,hf->dh", z, self.beta)


def fit_frozen_ridge(features, actual, days, *, penalties=PENALTY_GRID) -> RidgeModel:
    """Train on UTC 2015-01-01..2016-12-31 only; choose the penalty on UTC 2017 only; no refit."""
    train = days <= TRAIN_END
    valid = (days >= VALIDATION_START) & (days <= VALIDATION_END)
    nf = features.shape[2]
    mean, scale = np.zeros((24, nf)), np.ones((24, nf))
    rows = {}
    for h in range(24):
        ok = train & np.isfinite(features[:, h, :]).all(axis=1) & np.isfinite(actual[:, h])
        rows[h] = ok
        mean[h] = features[ok, h, :].mean(axis=0)
        sd = features[ok, h, :].std(axis=0)
        scale[h] = np.where(sd > 0, sd, 1.0)
    mse, fits = {}, {}
    for penalty in penalties:
        beta = np.zeros((24, nf))
        intercept = np.zeros(24)
        for h in range(24):
            ok = rows[h]
            xs = (features[ok, h, :] - mean[h]) / scale[h]
            intercept[h] = actual[ok, h].mean()
            gram = xs.T @ xs + penalty * np.eye(nf)
            beta[h] = np.linalg.solve(gram, xs.T @ (actual[ok, h] - intercept[h]))
        model = RidgeModel(penalty, mean, scale, intercept, beta, {}, int(rows[0].sum()))
        pred = model.predict(features)
        ok = valid[:, None] & np.isfinite(pred) & np.isfinite(actual)
        mse[penalty] = float(np.mean((pred[ok] - actual[ok]) ** 2))
        fits[penalty] = model
    best = min(penalties, key=lambda p: (mse[p], p))
    chosen = fits[best]
    return RidgeModel(
        best, chosen.mean, chosen.scale, chosen.intercept, chosen.beta, mse, chosen.n_train
    )


def rolling_tau(actual: np.ndarray, i: int) -> float:
    """0.90 quantile of hourly actuals of days i-365..i-2 (364 complete days) or NaN."""
    if i < TAU_WINDOW_DAYS + 1:
        return float("nan")
    window = actual[i - TAU_WINDOW_DAYS - 1 : i - 1].ravel()
    finite = window[np.isfinite(window)]
    if finite.size < TAU_MIN_COVERAGE * window.size:
        return float("nan")
    return float(np.quantile(finite, TAU_QUANTILE))


def opsd_informative(disagreement_share: float) -> bool:
    """R1 A.7 rule: the task is uninformative if disagreement share is below 2% or above 60%."""
    return 0.02 <= disagreement_share <= 0.60


def _pack(actions: np.ndarray) -> int:
    return int(sum(int(a) << h for h, a in enumerate(actions)))


def build_opsd_tasks(
    series: HourlySeries,
    windows=DEFAULT_WINDOWS,
    *,
    label_slack_days: int = 0,
    drop_lag07: bool = False,
    fixed_tau: bool = False,
) -> tuple[dict[str, RealTask], RidgeModel]:
    """Fit the frozen ridge and build one ``RealTask`` per window.

    ``label_slack_days`` shifts label availability (spec sensitivity d=3 is slack 1);
    ``drop_lag07`` and ``fixed_tau`` are the pre-declared A.10 sensitivities.
    """
    for _, _, end in windows:
        guard_timestamps(np.array([end]), OPSD_HOLDOUT_START, "OPSD window")
    guard_timestamps(series.actual.index.values, OPSD_HOLDOUT_START, "OPSD series")
    last_day = max(end for _, _, end in windows)
    days, actual = _day_matrix(series.actual, FIRST_FULL_DAY, last_day)
    _, forecast = _day_matrix(series.forecast, FIRST_FULL_DAY, last_day)
    features = feature_tensor(actual, days, drop_lag07=drop_lag07)
    model = fit_frozen_ridge(features, actual, days)
    pred = model.predict(features)
    train_values = actual[days <= TRAIN_END].ravel()
    train_tau = float(np.quantile(train_values[np.isfinite(train_values)], TAU_QUANTILE))
    tasks: dict[str, RealTask] = {}
    for name, start, end in windows:
        tasks[name] = _build_window(
            name,
            days,
            actual,
            forecast,
            pred,
            features,
            start,
            end,
            irregular=series.irregular_days,
            slack=label_slack_days,
            fixed_tau=train_tau if fixed_tau else None,
            penalty=model.penalty,
        )
    return tasks, model


def _build_window(
    name,
    days,
    actual,
    forecast,
    pred,
    features,
    start,
    end,
    *,
    irregular,
    slack,
    fixed_tau,
    penalty,
) -> RealTask:
    idx = np.flatnonzero((days >= start) & (days <= end))
    keep, taus = [], {}
    excl = {
        "calendar_irregular": 0,
        "missing_actual_or_incumbent": 0,
        "missing_candidate_feature": 0,
        "tau_unavailable": 0,
    }
    for i in idx:
        tau = fixed_tau if fixed_tau is not None else rolling_tau(actual, int(i))
        if days[i] in irregular:
            excl["calendar_irregular"] += 1
        elif not (np.isfinite(actual[i]).all() and np.isfinite(forecast[i]).all()):
            excl["missing_actual_or_incumbent"] += 1
        elif not (np.isfinite(features[i]).all() and np.isfinite(pred[i]).all()):
            excl["missing_candidate_feature"] += 1
        elif not np.isfinite(tau):
            excl["tau_unavailable"] += 1
        else:
            keep.append(int(i))
            taus[int(i)] = tau
    keep_arr = np.asarray(keep, dtype=np.int64)
    n = len(keep_arr)
    dep, ref, units = np.zeros(n, np.int64), np.zeros(n, np.int64), np.zeros(n, np.int64)
    loss0, loss1 = np.zeros(n), np.zeros(n)
    x = np.zeros((n, 50))
    for r, i in enumerate(keep_arr):
        tau = taus[int(i)]
        a0, a1 = reserve_actions(forecast[i], tau), reserve_actions(pred[i], tau)
        dep[r], ref[r], units[r] = _pack(a0), _pack(a1), int((a0 != a1).sum())
        loss0[r] = decision_cost(a0, actual[i], tau).sum() / LOSS_SCALE
        loss1[r] = decision_cost(a1, actual[i], tau).sum() / LOSS_SCALE
        x[r] = np.concatenate([forecast[i], pred[i], [tau, actual[i - 1, 7]]])
    day_ns = days[keep_arr].astype("datetime64[ns]")
    decision = day_ns - DECISION_OFFSET.astype("timedelta64[ns]")
    available = (
        day_ns
        + LABEL_AVAILABLE_OFFSET.astype("timedelta64[ns]")
        + np.timedelta64(24 * slack, "h").astype("timedelta64[ns]")
    )
    adjacent = np.zeros(n, dtype=bool)
    adjacent[1:] = np.diff(days[keep_arr].astype(np.int64)) == 1
    public = PublicRounds(day_ns, decision, x, dep, ref, units, adjacent)
    outcomes = EvaluatorOutcomes(
        loss0, loss1, loss0 - loss1, available, release_rounds(decision, available)
    )
    return RealTask(
        f"opsd_reserve_{name}",
        public,
        outcomes,
        COSTS,
        1.0,
        1.0,
        excl,
        {
            "ridge_penalty": penalty,
            "n_calendar_days": len(idx),
            "label_slack_days": slack,
            "shortfall": COST_SHORTFALL,
            "idle": COST_OVER_PROCUREMENT,
            "first_day": str(days[keep_arr[0]]) if n else None,
            "last_day": str(days[keep_arr[-1]]) if n else None,
        },
    )
