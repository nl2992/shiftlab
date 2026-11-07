"""Correctness tests for the shared SOTA simulator.

These guard the properties the whole comparison rests on: a policy cannot see a label it did not
buy or that has not been released, the hard budget holds pathwise, and propensities are the ones
frozen at issue time rather than anything recomputed later.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/promising_directions/sota"))

from simulator import (
    Event,
    QueryRequest,
    check_budget_feasible,
    check_no_future_access,
    policy_rng,
    run_episode,
)


class AlwaysAsk:
    """Asks for every label; deploys model 0. Used to test the cap and the delay."""

    name = "always_ask"

    def __init__(self):
        self.seen = []

    def predict(self, event: Event) -> int:
        return 0

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        return QueryRequest(requested=True, probability=1.0)

    def observe(self, feedback) -> None:
        self.seen.extend(feedback)

    def state_dict(self) -> dict:
        return {"seen": [f.event_id for f in self.seen]}

    def load_state_dict(self, state: dict) -> None:
        pass


class Flipper:
    """Switches deployed model every k events, to test switch accounting."""

    def __init__(self, k: int):
        self.k = k
        self.name = f"flip{k}"

    def predict(self, event: Event) -> int:
        return (event.t // self.k) % 2

    def request_labels(self, event, remaining_budget) -> QueryRequest:
        return QueryRequest(requested=False)

    def observe(self, feedback) -> None:
        pass

    def state_dict(self) -> dict:
        return {}

    def load_state_dict(self, state) -> None:
        pass


def toy(T=50, n_models=2, seed=0):
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, 2, T)
    preds = rng.integers(0, 2, (T, n_models))
    return preds, labels


def test_hard_budget_is_enforced_pathwise():
    preds, labels = toy(T=100)
    p = AlwaysAsk()
    res = run_episode(
        p,
        model_predictions=preds,
        labels=labels,
        delay=5,
        budget=10,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert res.requested_labels == 10
    assert check_budget_feasible(res, 10) == []
    # it kept asking after the cap; the simulator refused, and that is recorded
    assert res.refused_requests == 90


def test_label_arrives_only_after_the_declared_delay():
    preds, labels = toy(T=60)
    p = AlwaysAsk()
    delay = 7
    run_episode(
        p,
        model_predictions=preds,
        labels=labels,
        delay=delay,
        budget=5,
        label_price=0.05,
        switch_cost=5.0,
    )
    for f in p.seen:
        assert f.t_released - f.t_requested == delay
        assert f.t_released > f.t_requested


def test_policy_never_receives_unrequested_labels():
    preds, labels = toy(T=80)
    p = AlwaysAsk()
    res = run_episode(
        p,
        model_predictions=preds,
        labels=labels,
        delay=3,
        budget=6,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert len(p.seen) <= res.requested_labels
    bought = {r["event_id"] for r in res.records if r["requested"]}
    assert {f.event_id for f in p.seen} <= bought


def test_release_timing_validator_passes_on_a_clean_run():
    preds, labels = toy(T=40)
    res = run_episode(
        AlwaysAsk(),
        model_predictions=preds,
        labels=labels,
        delay=4,
        budget=40,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert check_no_future_access(res, 4) == []


def test_frozen_propensity_travels_with_the_request():
    """The released feedback must carry the issue-time probability, not a later value."""

    class Drifting:
        name = "drifting"

        def __init__(self):
            self.q = 0.9
            self.seen = []

        def predict(self, event):
            return 0

        def request_labels(self, event, remaining_budget):
            r = QueryRequest(requested=True, probability=self.q)
            self.q *= 0.5  # the policy's own estimate moves immediately after issuing
            return r

        def observe(self, feedback):
            self.seen.extend(feedback)

        def state_dict(self):
            return {}

        def load_state_dict(self, s):
            pass

    preds, labels = toy(T=20)
    p = Drifting()
    run_episode(
        p,
        model_predictions=preds,
        labels=labels,
        delay=2,
        budget=20,
        label_price=0.05,
        switch_cost=5.0,
    )
    # event 0 was issued at q = 0.9; by release time the policy's q has moved on
    first = next(f for f in p.seen if f.event_id == 0)
    assert first.query_probability == pytest.approx(0.9)


def test_switch_accounting_counts_every_change():
    preds, labels = toy(T=100)
    res = run_episode(
        Flipper(10),
        model_predictions=preds,
        labels=labels,
        delay=1,
        budget=0,
        label_price=0.05,
        switch_cost=5.0,
        initial_model=0,
    )
    # blocks of 10 alternate 0,1,0,1,...: 9 changes across 100 events
    assert res.deployment_switches == 9
    assert res.net_cost == pytest.approx(res.prediction_loss + 5.0 * 9)


def test_net_cost_is_the_declared_formula():
    preds, labels = toy(T=50)
    res = run_episode(
        AlwaysAsk(),
        model_predictions=preds,
        labels=labels,
        delay=1,
        budget=7,
        label_price=0.25,
        switch_cost=3.0,
    )
    assert res.net_cost == pytest.approx(
        res.prediction_loss + 0.25 * res.requested_labels + 3.0 * res.deployment_switches
    )


def test_policy_rngs_are_independent_and_reproducible():
    a1 = policy_rng(11, 3, "cams").random(5)
    a2 = policy_rng(11, 3, "cams").random(5)
    b = policy_rng(11, 3, "model_picker").random(5)
    assert np.array_equal(a1, a2)
    assert not np.array_equal(a1, b)


def test_delay_zero_is_refused_rather_than_silently_losing_labels():
    """Regression: delay=0 queued a release into a slot already drained, so no label ever
    reached the policy and a learner silently never learned. Two independent ports hit this."""
    preds, labels = toy(T=20)
    with pytest.raises(ValueError, match="delay must be >= 1"):
        run_episode(
            AlwaysAsk(),
            model_predictions=preds,
            labels=labels,
            delay=0,
            budget=20,
            label_price=0.05,
            switch_cost=5.0,
        )


def test_delay_one_is_immediate_feedback_and_does_deliver():
    preds, labels = toy(T=20)
    p = AlwaysAsk()
    run_episode(
        p,
        model_predictions=preds,
        labels=labels,
        delay=1,
        budget=20,
        label_price=0.05,
        switch_cost=5.0,
    )
    assert len(p.seen) > 0
    assert all(f.t_released == f.t_requested + 1 for f in p.seen)
