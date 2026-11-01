import numpy as np
import pandas as pd

from scripts.exhaustive_evaluation.run_real_development import (
    calendar_features,
    queries_before_alarm,
)


def test_calendar_features_do_not_require_outcomes_or_observed_weather():
    clock = pd.date_range("2011-01-01", periods=48, freq="h")
    x = calendar_features(clock)
    assert x.shape == (48, 9)
    assert np.isfinite(x).all()
    np.testing.assert_array_equal(x, calendar_features(clock))


def test_stop_cost_includes_pending_queries_and_excludes_same_event_issue():
    result = {"first": np.array([0, 3, 10])}
    counts = queries_before_alarm(result, shape=(3, 10), seed=9, budget=10, frac=1)
    np.testing.assert_array_equal(counts, [0, 3, 10])
    counts = queries_before_alarm(result, shape=(3, 10), seed=9, budget=2, frac=1)
    np.testing.assert_array_equal(counts, [0, 2, 2])


def test_batched_query_cost_is_exactly_one_label_per_complete_batch():
    result = {"first": np.array([20, 20])}
    counts = queries_before_alarm(result, shape=(2, 20), seed=2, budget=4, batched=True)
    np.testing.assert_array_equal(counts, [4, 4])
