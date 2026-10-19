"""Exact UTC monthly kline calendar validation, including the 2025 precision change."""

import json
import re

import numpy as np
import pandas as pd


def calendar(month, interval, open_times, close_times):
    if not isinstance(month, str) or not re.fullmatch(r"\d{4}-\d{2}", month):
        raise ValueError("Month must be YYYY-MM")
    if interval not in {"1d", "1h"}:
        raise ValueError("Supported intervals are 1d and 1h")
    period = pd.Period(month, freq="M")
    start = pd.Timestamp(period.start_time, tz="UTC")
    stop = pd.Timestamp((period + 1).start_time, tz="UTC")
    divisor = 1_000_000 if start.year >= 2025 else 1000
    step = 86400 if interval == "1d" else 3600
    expected = np.arange(start.value // 10**9, stop.value // 10**9, step, dtype=np.int64) * divisor
    opens = np.asarray(open_times, dtype=np.int64)
    closes = np.asarray(close_times, dtype=np.int64)
    if not np.array_equal(opens, expected):
        raise ValueError("Binance archive has missing, duplicate, shifted or wrong-precision bars")
    if not np.array_equal(closes, expected + step * divisor - 1):
        raise ValueError("Binance close times do not match the complete UTC bar calendar")
    return divisor


def prepare(original: pd.DataFrame, symbol: str, month: str, interval: str):
    """Build the one-bar-ahead close-return task from an official monthly kline table."""
    from ..chronological_splits import assign_splits
    from .adapters import standardize

    if len(original) < 5 or not set(range(7)).issubset(original.columns):
        raise ValueError("Binance kline table is missing required OHLCV/time columns")
    timestamps = pd.to_numeric(original[0], errors="raise").to_numpy(dtype=np.int64)
    divisor = calendar(
        month,
        interval,
        timestamps,
        pd.to_numeric(original[6], errors="raise").to_numpy(dtype=np.int64),
    )
    close = pd.to_numeric(original[4], errors="coerce").to_numpy(dtype=float)
    features = original[[1, 2, 3, 4, 5]].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    metadata = [
        json.dumps(
            {
                "close_time_raw": int(value),
                "timestamp_divisor": divisor,
                "interval": interval,
                "task": "next close return; all current OHLCV require bar close",
            }
        )
        for value in original[6].iloc[:-1]
    ]
    frame = standardize(
        features[:-1],
        close[1:] / close[:-1] - 1,
        symbol,
        f"binance-{symbol}-{month}",
        event_time=timestamps[:-1] / divisor,
        split=assign_splits(timestamps[:-1]),
        metadata=metadata,
    )
    frame["label_event_time"] = pd.to_numeric(original[6]).to_numpy(dtype=np.int64)[1:] / divisor
    return frame, ["open", "high", "low", "close", "volume"]
