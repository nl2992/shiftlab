import numpy as np

from shiftlab.dive.eprocess import StartedMixtureEProcess
from shiftlab.dive.promotion_timing import (
    PromotionTimingConfig,
    _benefit_schedule,
    _evaluate_scenario,
    _time_splits,
    _vectorized_crossing_times,
)


def test_vectorized_crossings_match_started_mixture_reference():
    rng = np.random.default_rng(18)
    gains = rng.uniform(-0.4, 0.7, size=(4, 120))
    starts = (0, 37, 80)
    actual = _vectorized_crossing_times(gains, bound=1.0, alpha=0.05, starts=starts)
    expected = []
    for row in gains:
        process = StartedMixtureEProcess(bound=1.0, alpha=0.05, starts=starts)
        crossing = -1
        for time, gain in enumerate(row):
            if process.update(float(gain)) >= -np.log(0.05) and crossing < 0:
                crossing = time
        expected.append(crossing)
    np.testing.assert_array_equal(actual, expected)


def test_benefit_schedules_are_evaluator_only_and_have_expected_timing():
    train_end, validation_end, monitor_end = _time_splits(3200)
    transient = _benefit_schedule("early_transient", 3200, validation_end, monitor_end)
    assert np.all(transient[:validation_end] == 0)
    assert np.all(transient[validation_end : validation_end + 320] == 0.22)
    assert np.all(transient[validation_end + 320 :] == 0)
    persistent = _benefit_schedule("persistent_benefit", 3200, validation_end, monitor_end)
    assert np.all(persistent[:validation_end] == 0)
    assert np.all(persistent[validation_end:] == 0.12)
    assert train_end < validation_end < monitor_end < 3200


def test_cpu_timing_smoke_preserves_forward_splits_and_candidate_freeze():
    config = PromotionTimingConfig(n=1200, seeds=3, device="cpu")
    rows = _evaluate_scenario("late_persistent", config=config, scenario_index=0)
    assert len(rows) == config.seeds * 5
    for row in rows:
        assert row["training_end_index"] < row["validation_end_index"]
        assert row["validation_end_index"] == row["shadow_start_index"]
        assert row["shadow_end_index"] == row["deployment_start_index"]
        assert row["deployment_end_index"] == config.n
        assert row["oracle_benefit_schedule_id"] == "late_persistent"
        assert "benefit" not in row
