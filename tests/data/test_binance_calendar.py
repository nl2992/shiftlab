import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.binance import calendar, prepare


@pytest.mark.parametrize(
    "month,interval,divisor",
    [("2023-01", "1d", 1000), ("2025-01", "1h", 1000000), ("2024-02", "1h", 1000)],
)
def test_exact_calendar_precision_and_boundaries(month, interval, divisor):
    period = pd.Period(month, freq="M")
    start = pd.Timestamp(period.start_time, tz="UTC").value // 10**9
    count = period.days_in_month * (24 if interval == "1h" else 1)
    step = 3600 if interval == "1h" else 86400
    opens = (start + np.arange(count) * step) * divisor
    closes = opens + step * divisor - 1
    assert calendar(month, interval, opens, closes) == divisor
    for broken in [opens[:-1], opens + step * divisor, np.roll(opens, 1)]:
        with pytest.raises(ValueError):
            calendar(month, interval, broken, closes)
    with pytest.raises(ValueError):
        calendar(month, interval, opens, closes + 1)


def test_binance_task_uses_one_future_bar_close_and_masks_nonfinite_returns():
    month, interval = "2025-01", "1h"
    period = pd.Period(month, freq="M")
    start = pd.Timestamp(period.start_time, tz="UTC").value // 10**9
    opens = (start + np.arange(period.days_in_month * 24) * 3600) * 1_000_000
    closes = opens + 3600 * 1_000_000 - 1
    close = np.arange(len(opens), dtype=float) + 100
    close[5] = np.nan
    original = pd.DataFrame(
        {
            0: opens,
            1: close - 1,
            2: close + 1,
            3: close - 2,
            4: close,
            5: np.ones(len(opens)),
            6: closes,
        }
    )
    frame, names = prepare(original, "BTCUSDT", month, interval)
    assert names == ["open", "high", "low", "close", "volume"]
    assert len(frame) == len(opens) - 1
    assert np.isnan(frame.target.iloc[4])
    assert np.isnan(frame.target.iloc[5])
    assert np.isfinite(frame.target.iloc[6])
    assert frame.event_time.iloc[0] == opens[0] / 1_000_000
    assert frame.label_event_time.iloc[0] == closes[1] / 1_000_000
    assert 3600 < frame.label_event_time.iloc[0] - frame.event_time.iloc[0] < 7200
    assert frame.features.iloc[0][3] == close[0]
    assert frame.label_available_time.isna().all()
