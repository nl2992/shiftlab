from __future__ import annotations

from dataclasses import asdict, replace

import numpy as np
import pytest

from shiftlab.sota_search.feedback import FeedbackStream
from shiftlab.sota_search.generators import (
    FAMILIES,
    SCENARIOS,
    WorldConfig,
    make_world,
    summarize_world,
)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_all_worlds_bounded_and_public_interface_has_no_evaluator_fields(family, scenario):
    world = make_world(WorldConfig(family=family, scenario=scenario, horizon=128), seed=7)
    for name in (
        "predictive_losses",
        "decision_losses",
        "expected_predictive_losses",
        "expected_decision_losses",
        "nominal_predictive_losses",
        "nominal_decision_losses",
    ):
        values = getattr(world.truth, name)
        assert values.shape == (128, 3)
        assert np.isfinite(values).all() and values.min() >= 0 and values.max() <= 1
    public = asdict(world.events[0])
    assert not set(public) & {
        "outcome",
        "outcomes",
        "regime",
        "regime_weight",
        "hidden_state",
        "availability",
        "expected_predictive_losses",
        "expected_decision_losses",
        "nominal_predictive_losses",
    }
    assert isinstance(world.events[0].features, tuple)
    assert not world.truth.outcomes.flags.writeable


@pytest.mark.parametrize("family", FAMILIES)
def test_three_dimensions_disagree_by_construction(family):
    config = WorldConfig(family=family, horizon=1024)
    harmless = make_world(replace(config, scenario="benign_covariate"), seed=9)
    stationary = make_world(replace(config, scenario="stationary"), seed=9)
    np.testing.assert_array_equal(harmless.truth.outcomes, stationary.truth.outcomes)
    assert summarize_world(harmless)["mean_feature_displacement"] > 2
    assert summarize_world(harmless)["decision_deterioration"] == 0

    risk_only = make_world(replace(config, scenario="risk_without_harm"), seed=9)
    summary = summarize_world(risk_only)
    assert summary["predictive_deterioration"] > 0.01
    assert summary["decision_deterioration"] == pytest.approx(0, abs=1e-14)

    harm_only = make_world(replace(config, scenario="harm_without_accuracy"), seed=9)
    np.testing.assert_array_equal(harm_only.truth.outcomes, stationary.truth.outcomes)
    summary = summarize_world(harm_only)
    assert summary["predictive_deterioration"] == 0
    assert summary["decision_deterioration"] > 0.01


@pytest.mark.parametrize("family", FAMILIES)
def test_model_rankings_transient_permanent_and_ties(family):
    config = WorldConfig(family=family, horizon=2048)
    transient = make_world(replace(config, scenario="transient_challenger"), seed=18)
    benefit = (
        transient.truth.expected_decision_losses[:, 0]
        - transient.truth.expected_decision_losses[:, 1]
    )
    assert benefit[transient.truth.regime_weight == 1].mean() > 0
    assert benefit[transient.truth.regime_weight == 0].mean() < 0
    permanent = make_world(replace(config, scenario="challenger_optimal"), seed=18)
    delta = (
        permanent.truth.expected_decision_losses[:, 0]
        - permanent.truth.expected_decision_losses[:, 1]
    )
    assert delta[permanent.truth.regime_weight == 1].mean() > 0
    tied = make_world(replace(config, scenario="tied_models"), seed=18)
    np.testing.assert_array_equal(
        tied.truth.expected_decision_losses[:, 0], tied.truth.expected_decision_losses[:, 1]
    )


def test_source_partition_is_disjoint_nominal_and_confirmation_is_locked():
    config = WorldConfig(horizon=128)
    source = make_world(config, seed=7, partition="source")
    development = make_world(config, seed=7)
    assert not np.array_equal(source.truth.outcomes, development.truth.outcomes)
    np.testing.assert_array_equal(source.truth.regime_weight, 0)
    np.testing.assert_array_equal(
        source.truth.expected_decision_losses, source.truth.nominal_decision_losses
    )
    with pytest.raises(ValueError, match="unlocked"):
        make_world(config, seed=7, partition="confirmation")


def test_only_purchased_labels_arrive_out_of_order_and_budget_charged_before_release():
    world = make_world(WorldConfig(horizon=128), seed=4)
    availability = np.arange(128)
    availability[0], availability[1] = 4, 2
    missing = np.zeros(128, dtype=bool)
    missing[1] = True
    world = replace(world, truth=replace(world.truth, availability=availability, missing=missing))
    broker = FeedbackStream(world, budget=2, query_seed=1)
    event, released = broker.open_round(0)
    assert event.index == 0 and not released
    receipt, released = broker.request(1)
    assert receipt.purchased and receipt.remaining_labels == 1 and not released
    assert not set(asdict(receipt)) & {"outcome", "availability", "available_time"}
    broker.open_round(1)
    receipt, _ = broker.request(1)
    assert receipt.remaining_labels == 0 and broker.pending_count == 2
    _, released = broker.open_round(2)
    assert len(released) == 1 and released[0].event_index == 1
    assert released[0].missing and released[0].outcome is None
    receipt, _ = broker.request(1)
    assert receipt.effective_propensity == 0 and not receipt.purchased
    broker.open_round(3)
    broker.request(0)
    _, released = broker.open_round(4)
    assert len(released) == 1 and released[0].event_index == 0
    assert released[0].outcome == world.truth.outcomes[0]
    assert broker.money_spent == pytest.approx(2 * world.events[0].label_cost)


def test_broker_refuses_duplicate_queries_and_out_of_order_rounds():
    broker = FeedbackStream(make_world(WorldConfig(horizon=100), seed=1), budget=10, query_seed=1)
    with pytest.raises(ValueError):
        broker.request(0.2)
    broker.open_round(0)
    with pytest.raises(ValueError):
        broker.open_round(1)
    with pytest.raises(ValueError):
        broker.request(float("nan"))
    broker.request(0)
    with pytest.raises(ValueError):
        broker.request(0)


@pytest.mark.parametrize("family", FAMILIES)
def test_oracle_risks_agree_with_independent_sampled_losses(family):
    world = make_world(WorldConfig(family=family, horizon=8192), seed=82)
    for realized, expected in (
        (world.truth.predictive_losses, world.truth.expected_predictive_losses),
        (world.truth.decision_losses, world.truth.expected_decision_losses),
    ):
        # Labels are independent conditional on the generated features/states;
        # 0.025 is a deliberately conservative bounded-average tolerance.
        np.testing.assert_allclose(realized.mean(axis=0), expected.mean(axis=0), atol=0.025)


@pytest.mark.parametrize("family", FAMILIES)
def test_auxiliary_proxy_quality_is_measurable_and_not_assumed_from_name(family):
    config = WorldConfig(family=family, horizon=2048)
    good = make_world(replace(config, proxy_quality="excellent"), seed=31)
    bad = make_world(replace(config, proxy_quality="anti_informative"), seed=31)
    np.testing.assert_array_equal(good.truth.outcomes, bad.truth.outcomes)
    assert (
        summarize_world(good)["proxy_predictive_loss_rmse"]
        < summarize_world(bad)["proxy_predictive_loss_rmse"]
    )
