import numpy as np

from shiftlab.dive.promotion_robustness import (
    PromotionRobustnessConfig,
    _rows_for_scenario,
    _schedule,
)
from shiftlab.dive.promotion_timing import _time_splits


def test_reversal_schedule_encodes_onset_duration_and_recovery():
    _, monitor_start, monitor_end = _time_splits(3200)
    length = monitor_end - monitor_start
    schedule = _schedule("reversal_early_short", 3200, monitor_start, monitor_end)
    onset = monitor_start + round(0.2 * length)
    recovery = onset + round(0.2 * 3200)
    assert np.all(schedule[monitor_start:onset] == 0.22)
    assert np.all(schedule[onset:recovery] == -0.04)
    assert np.all(schedule[recovery:] == 0.0)


def test_switching_cost_grid_reuses_seed_streams_and_scores_cost_once():
    config = PromotionRobustnessConfig(
        n=1200,
        seeds=3,
        switching_costs=(0.0, 10.0),
        discovery_fractions=(0.5,),
        device="cpu",
    )
    rows = _rows_for_scenario("persistent_benefit", config=config, scenario_index=0)
    assert len(rows) == 3 * 2 * 6
    low = [r for r in rows if r["switching_cost"] == 0 and r["method"] == "never_promote"]
    high = [r for r in rows if r["switching_cost"] == 10 and r["method"] == "never_promote"]
    assert [r["seed"] for r in low] == [r["seed"] for r in high]
    promoted = next(r for r in rows if r["promoted"] and r["switching_cost"] == 10)
    assert np.isclose(
        promoted["oracle_postpromotion_net_gain"],
        0.12 * (config.n - promoted["evaluation_start_index"]) - 10.0,
    )


def test_config_rejects_unsorted_cost_grid():
    try:
        PromotionRobustnessConfig(switching_costs=(10.0, 0.0)).validate()
    except ValueError as error:
        assert "strictly increasing" in str(error)
    else:
        raise AssertionError("unsorted cost grid should be rejected")
