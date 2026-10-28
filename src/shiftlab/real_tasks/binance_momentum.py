"""Binance ETHUSDT 1h two-rule momentum replay (R1 spec B). Development windows only."""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.real.binance import calendar
from . import (
    BINANCE_HOLDOUT_START,
    CostParams,
    EvaluatorOutcomes,
    HoldoutAccessError,
    PublicRounds,
    RealTask,
    guard_timestamps,
    release_rounds,
)

FAST_BARS = 24
SLOW_BARS = 168
PNL_SCALE = 0.10
FEE_PRIMARY = 0.001
BAR = np.timedelta64(1, "h")
COSTS = CostParams(
    budget_fractions=(0.02, 0.05, 0.10),
    primary_budget=0.05,
    query_costs=(0.0, 0.0005, 0.002),
    primary_query_cost=0.0005,
    switch_costs=(FEE_PRIMARY / (2 * PNL_SCALE),),
    primary_switch_cost=FEE_PRIMARY / (2 * PNL_SCALE),
    description="imposed budget and c; k = f/(2*0.10) with f the one-notional fee (upper bound)",
)


@dataclass(frozen=True)
class Bars:
    open_time: np.ndarray  # datetime64[ns], UTC bar open
    close_time: np.ndarray  # datetime64[ns], bar open + 1 h - 1 ms
    close: np.ndarray


def _month_guard(month: str) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("month must be YYYY-MM")
    start = np.datetime64(month, "M").astype("datetime64[s]")
    if start >= BINANCE_HOLDOUT_START.astype("datetime64[s]"):
        raise HoldoutAccessError(f"Binance month {month} is in the locked holdout")


def load_binance_bars(root: str | Path, months: list[str], symbol: str = "ETHUSDT") -> Bars:
    """Read monthly 1h kline zips for ``months`` only; the guard runs before any file is opened."""
    for month in months:
        _month_guard(month)
    opens, closes, close_px = [], [], []
    for month in months:
        path = Path(root) / f"{symbol}-1h-{month}.zip"
        with zipfile.ZipFile(path) as archive:
            raw = archive.read(archive.namelist()[0])
        frame = pd.read_csv(io.BytesIO(raw), header=None)
        o = frame[0].to_numpy(np.int64)
        c = frame[6].to_numpy(np.int64)
        divisor = calendar(month, "1h", o, c)
        opens.append(o // divisor)
        closes.append(c // (divisor // 1000))  # milliseconds
        close_px.append(pd.to_numeric(frame[4]).to_numpy(float))
    open_s = np.concatenate(opens)
    bars = Bars(
        open_s.astype("datetime64[s]").astype("datetime64[ns]"),
        np.concatenate(closes).astype("datetime64[ms]").astype("datetime64[ns]"),
        np.concatenate(close_px),
    )
    return _validated(bars)


def _validated(bars: Bars) -> Bars:
    guard_timestamps(bars.close_time, BINANCE_HOLDOUT_START, "Binance bars")
    if len(bars.open_time) > 1 and not np.all(
        np.diff(bars.open_time) == BAR.astype("timedelta64[ns]")
    ):
        raise ValueError("bars are not a continuous hourly calendar")
    if not np.isfinite(bars.close).all() or np.any(bars.close <= 0):
        raise ValueError("closes must be finite and positive")
    return bars


def momentum_position(close: np.ndarray, bars: int) -> np.ndarray:
    """p_t = 1 if ln(C_t / C_{t-bars}) > 0 else 0, using closes up to and including t."""
    pos = np.zeros(len(close), dtype=np.int64)
    ret = np.log(close[bars:] / close[:-bars])
    pos[bars:] = (ret > 0).astype(np.int64)
    return pos


def loss_from_pnl(pnl: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 - np.clip(pnl / PNL_SCALE, -1.0, 1.0))


def build_binance_task(bars: Bars, fee: float = FEE_PRIMARY, name: str = "development") -> RealTask:
    """Rounds t = 169 .. N-2: the first round with p_{t-1} defined for both rules; the last round
    whose label (the close of bar t+1) lies inside the supplied bars."""
    bars = _validated(bars)
    c = bars.close
    n_bars = len(c)
    p0 = momentum_position(c, FAST_BARS)
    p1 = momentum_position(c, SLOW_BARS)
    rounds = np.arange(SLOW_BARS + 1, n_bars - 1)
    nxt = c[rounds + 1] / c[rounds] - 1.0
    pnl0 = p0[rounds] * nxt - fee * np.abs(p0[rounds] - p0[rounds - 1])
    pnl1 = p1[rounds] * nxt - fee * np.abs(p1[rounds] - p1[rounds - 1])
    loss0, loss1 = loss_from_pnl(pnl0), loss_from_pnl(pnl1)
    logret = np.diff(np.log(c), prepend=np.nan)
    x = np.zeros((len(rounds), 4))
    for r, t in enumerate(rounds):
        x[r] = [
            logret[t],
            np.log(c[t] / c[t - FAST_BARS]),
            np.log(c[t] / c[t - SLOW_BARS]),
            float(np.std(logret[t - FAST_BARS + 1 : t + 1])),
        ]
    decision = bars.close_time[rounds]
    available = bars.close_time[rounds + 1]
    n = len(rounds)
    public = PublicRounds(
        bars.open_time[rounds],
        decision,
        x,
        p0[rounds],
        p1[rounds],
        (p0[rounds] != p1[rounds]).astype(np.int64),
        np.concatenate([[False], np.ones(n - 1, dtype=bool)]),
    )
    outcomes = EvaluatorOutcomes(
        loss0, loss1, loss0 - loss1, available, release_rounds(decision, available)
    )
    clipped = int((np.abs(pnl0 / PNL_SCALE) > 1).sum() + (np.abs(pnl1 / PNL_SCALE) > 1).sum())
    return RealTask(
        f"binance_momentum_{name}",
        public,
        outcomes,
        COSTS,
        1.0,
        1.0,
        {"clipped_policy_bars": clipped},
        {"fee": fee, "n_bars": n_bars, "n_rounds": n},
    )
