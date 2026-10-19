import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.binance import calendar


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
