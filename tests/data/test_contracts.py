import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from shiftlab.data.chronological_splits import assign_splits, fit_training_scaler
from shiftlab.data.schemas import SyntheticConfig, validate_frame
from shiftlab.data.streaming import Label, Request, replay
from shiftlab.data.synthetic import SCENARIOS, generate_chunks
from shiftlab.data.synthetic.generators import schedule
from shiftlab.data.synthetic.performative import PerformativeEnvironment, indistinguishable_worlds
from shiftlab.data.tasks import forecast_task


@pytest.mark.parametrize("scenario", list(SCENARIOS))
def test_generator_contract(scenario):
    config = SyntheticConfig(scenario=scenario, n=300, d=4, chunk_size=111, delay=3, missing=0.1)
    first = list(generate_chunks(config))
    second = list(generate_chunks(config))
    assert sum(len(frame) for frame, _ in first) == 300
    for (frame, oracle), (other, other_oracle) in zip(first, second):
        assert validate_frame(frame)["rows"] == len(frame)
        pd.testing.assert_frame_equal(frame, other)
        pd.testing.assert_frame_equal(oracle, other_oracle)
        assert frame.regime_id.isna().all()
        assert np.isfinite(np.stack(frame.features)).all()
        assert np.isfinite(frame.target).all()
        assert ((oracle.probability_positive >= 0) & (oracle.probability_positive <= 1)).all()


def test_chronology_and_training_only_scaler():
    times = np.repeat(np.arange(20), 3)
    splits = assign_splits(times)
    for time in np.unique(times):
        assert len(set(splits[times == time])) == 1
    X = np.arange(60)[:, None].astype(float)
    original = fit_training_scaler(X, splits)
    X[splits == "test"] += 10000
    changed = fit_training_scaler(X, splits)
    assert np.array_equal(original.mean_, changed.mean_)
    with pytest.raises(ValueError):
        assign_splits([3, 2, 1, 0])


def test_label_visibility_and_unknown_times():
    config = SyntheticConfig(n=100, delay=3)
    frame, _ = next(generate_chunks(config))
    requested = {}
    for event in replay(frame):
        if isinstance(event, Request):
            requested[event.sample_id] = event.prediction_time
            assert not hasattr(event, "target") and not hasattr(event, "regime_id")
            assert not hasattr(event, "oracle_risk")
        else:
            assert isinstance(event, Label)
            assert event.available_time == requested[event.sample_id] + 3
    broken = frame.copy()
    broken.loc[0, "feature_available_time"] = 1000
    with pytest.raises(ValueError):
        list(replay(broken))
    frame["label_available_time"] = np.nan
    assert all(isinstance(item, Request) for item in replay(frame))
    frame["prediction_time"] = np.nan
    with pytest.raises(ValueError):
        list(replay(frame))


def test_future_targets_do_not_change_requests():
    frame, _ = next(generate_chunks(SyntheticConfig(n=100, delay=5)))
    other = frame.copy()
    other.loc[other.index >= 50, "target"] += 100
    left = [e for e in replay(frame) if isinstance(e, Request)]
    right = [e for e in replay(other) if isinstance(e, Request)]
    assert left == right


@pytest.mark.parametrize(
    "pattern",
    [
        "abrupt",
        "multiple",
        "linear",
        "sigmoid",
        "recurring",
        "hmm",
        "seasonal",
        "temporary",
        "variable_dwell",
    ],
)
def test_pattern_ground_truth(pattern):
    c = SyntheticConfig(scenario="concept", n=1000, pattern=pattern, regimes=5)
    w, truth = schedule(c)
    if pattern in ["linear", "sigmoid", "seasonal"]:
        assert truth["transition_intervals"] and not truth["change_times"]
    else:
        assert truth["change_times"] == (np.flatnonzero(np.diff(w) != 0) + 1).tolist()
    null = SyntheticConfig.model_validate({**c.model_dump(), "severity": 0})
    assert not schedule(null)[0].any()
    assert schedule(null)[1] == {"change_times": [], "transition_intervals": []}


def test_null_severity_and_covariate_conditional():
    a = next(iter(generate_chunks(SyntheticConfig(n=1000, scenario="iid_regression"))))
    b = next(iter(generate_chunks(SyntheticConfig(n=1000, scenario="irrelevant", severity=0))))
    assert np.array_equal(a[0].target, b[0].target)
    cov, oracle = next(generate_chunks(SyntheticConfig(n=1000, scenario="mean")))
    X = np.stack(cov.features)
    assert np.allclose(oracle.conditional_mean, X[:, 0] - 0.9 * X[:, 1])


def test_impossibility_and_performative():
    worlds = indistinguishable_worlds()
    assert worlds["world_A_action"] != worlds["world_B_action"]
    a, b = PerformativeEnvironment(seed=2), PerformativeEnvironment(seed=2)
    assert a.step([1.0, -1.0]) == b.step([1.0, -1.0])
    with pytest.raises(ValueError):
        a.step([100.0])


def test_task_horizon():
    values = np.arange(20.0)
    X, y, prediction, outcome = forecast_task(values, horizon=3, lookback=4)
    assert np.array_equal(X[:, -1], values[prediction])
    assert np.array_equal(y, values[outcome])
    assert np.all(outcome == prediction + 3)


def test_invalid_configuration():
    with pytest.raises(ValidationError):
        SyntheticConfig(d=1)
    with pytest.raises(ValidationError):
        SyntheticConfig(unknown=1)


def test_partition_boundary_delay_purge():
    frame = pd.concat(
        [f for f, _ in generate_chunks(SyntheticConfig(n=1000, chunk_size=100, delay=10))],
        ignore_index=True,
    )
    for split, cutoff in [("train", 200), ("validation", 300), ("calibration", 400)]:
        assert (frame.loc[frame.split == split, "label_available_time"] < cutoff).all()
