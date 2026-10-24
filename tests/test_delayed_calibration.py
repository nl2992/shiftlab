import numpy as np

from shiftlab.dive.delayed_calibration import (
    CALIBRATION_METHODS,
    DelayedCalibrationConfig,
    _exact_interval,
    calibration_alarm_indices,
    run_calibration,
)
from shiftlab.dive.eprocess import BoundedMeanEProcess, StartedMixtureEProcess
from shiftlab.monitoring import HoeffdingExcessEProcess


def test_vectorized_calibration_matches_online_processes_and_event_order_wall_time():
    contrasts = np.asarray([-0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6])
    events = np.arange(len(contrasts)) * 10
    arrivals = events + np.asarray([4, 2, 5, 1, 3, 6, 2, 4])
    query_rate, n_events, margin, alpha, amplitude = 0.5, 16, 0.02, 0.05, 0.6
    observed = calibration_alarm_indices(
        contrasts,
        events,
        arrivals,
        query_rate=query_rate,
        n_events=n_events,
        margin=margin,
        alpha=alpha,
        amplitude=amplitude,
    )

    bound = amplitude + margin + 1e-6
    horizon = round(query_rate * n_events)
    starts = tuple(sorted({round(horizon * i / 8) for i in range(8)}))
    processes = {
        "paired_cost_eprocess": HoeffdingExcessEProcess(
            epsilon=margin, alpha=alpha, lower=-1.0, upper=1.0
        ),
        "paired_cost_betting": BoundedMeanEProcess(bound=bound, alpha=alpha),
        "restart_mixture_8": StartedMixtureEProcess(bound=bound, alpha=alpha, starts=starts),
    }
    expected = {}
    for method, process in processes.items():
        crossing = None
        for index, value in enumerate(contrasts):
            update = value if method == "paired_cost_eprocess" else value - margin
            log_value = process.update(update)
            if log_value >= np.log(1 / alpha):
                crossing = index
                break
        if crossing is None:
            expected[method] = (None, None)
        else:
            expected[method] = (
                int(events[crossing]),
                int(np.maximum.accumulate(arrivals)[crossing]),
            )
    assert observed == expected
    assert set(observed) == set(CALIBRATION_METHODS)


def test_exact_interval_handles_zero_and_all_false_escalations():
    assert _exact_interval(0, 2000)[0] == 0
    assert 0.001 < _exact_interval(0, 2000)[1] < 0.003
    lower, upper = _exact_interval(2000, 2000)
    assert 0.997 < lower < 1
    assert upper == 1


def test_small_independent_calibration_writes_cellwise_results(tmp_path):
    config = DelayedCalibrationConfig(
        streams_per_cell=3,
        seed_offset=91,
        n_events=120,
        query_rates=(0.25, 0.5),
        device="cpu",
    )
    frame, summary, manifest = run_calibration(config, tmp_path)
    assert len(frame) == 2 * 2 * 3 * len(CALIBRATION_METHODS)
    assert len(summary) == 2 * 2 * len(CALIBRATION_METHODS)
    assert set(summary.streams) == {3}
    assert manifest["resolved_device"] == "cpu"
    assert (tmp_path / "delayed_null_calibration.parquet").is_file()
    assert (tmp_path / "calibration_summary.csv").is_file()
    assert (tmp_path / "results.md").is_file()
