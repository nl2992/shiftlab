from dataclasses import replace

import numpy as np
import pytest

from shiftlab.sota_search.adapters import AdapterConfig, SourceCalibration, StreamingAdapter
from shiftlab.sota_search.feedback import FeedbackStream
from shiftlab.sota_search.generators import WorldConfig, make_world


@pytest.mark.parametrize(
    "method",
    [
        "direct",
        "ppe",
        "multiscale",
        "reliable",
        "pprm",
        "pprm_adaptive",
        "cusum",
        "frozen",
        "greedy",
        "hysteresis",
        "certified",
        "reversal",
        "cams_inspired",
    ],
)
def test_adapter_streams_only_arrived_feedback_under_hard_cap(method):
    config = WorldConfig(horizon=128, delay=3, delay_model="independent_random")
    source = make_world(config, seed=51, partition="source")
    world = make_world(config, seed=52)
    calibration = SourceCalibration(
        source.events, source.truth.predictive_losses, source.truth.decision_losses
    )
    track = (
        "Q3"
        if method in ("frozen", "greedy", "hysteresis", "certified", "reversal", "cams_inspired")
        else "Q1"
    )
    adapter = StreamingAdapter(
        AdapterConfig(track=track, method=method, window=16), calibration, horizon=128
    )
    broker = FeedbackStream(world, budget=20, query_seed=53)
    for time in range(128):
        event, feedback = broker.open_round(time)
        adapter.receive(feedback, time=time)
        assert adapter.choose_model(event) in (0, 1, 2)
        q = adapter.propensity(event, remaining=20 - broker.labels_purchased)
        receipt, immediate = broker.request(q)
        adapter.register(event, receipt)
        adapter.receive(immediate, time=time)
    assert broker.labels_purchased <= 20
    assert np.isfinite(adapter.log_e_values).all()


@pytest.mark.parametrize("query", ["variance", "robust", "growth", "mixed", "paced"])
def test_query_rules_respect_nonnegative_factor_floor(query):
    config = WorldConfig(horizon=128)
    source = make_world(config, seed=9, partition="source")
    adapter = StreamingAdapter(
        AdapterConfig(query=query),
        SourceCalibration(
            source.events, source.truth.predictive_losses, source.truth.decision_losses
        ),
        horizon=128,
    )
    for event in source.events[:4]:
        q = adapter.propensity(event, remaining=25)
        assert adapter.floor <= q <= 1
    assert adapter.propensity(source.events[5], remaining=0) == 0


def test_pprm_rejects_selectively_queried_contract():
    with pytest.raises(ValueError, match="uniform"):
        replace(AdapterConfig(method="pprm"), query="growth")
