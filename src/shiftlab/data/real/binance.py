"""Exact UTC monthly kline calendar validation, including the 2025 precision change."""

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
