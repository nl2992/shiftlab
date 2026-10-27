import numpy as np
import pandas as pd
import pytest

import shiftlab.dive.gated_monitor_comparison as comparison
from shiftlab.dive.gated_monitor_comparison import (
    GATED_ARMS,
    DisagreementPacer,
    gated_increment,
    paired_growth,
    replay_gated,
)


def toy_inputs():
    n = 400
    active = np.arange(n) % 5 == 0
    return {
        "x": np.zeros((n, 2)),
        "paired_cost": np.where(active, 5.0, 0.0),
        "disagreement": active,
        "tariffs": np.ones(n),
        "uniforms": np.random.default_rng(7).random(n),
        "validation_disagreement": active[:200],
        "validation_tariffs": np.ones(200),
        "budget_rate": 0.05,
    }


def test_agreement_is_known_and_does_not_query():
    data = toy_inputs()
    data["disagreement"][:] = False
    result = replay_gated(arm="gated_ht_paced", **data)
    assert not result.queried.any()
    assert result.dollars == 0
    np.testing.assert_array_equal(result.increments, -0.1)
    assert len(result.increments) == len(data["x"])


@pytest.mark.parametrize("arm", [a for a in GATED_ARMS if "ppi" not in a])
def test_bounds_and_hard_cap(arm):
    result = replay_gated(arm=arm, **toy_inputs())
    assert np.all(np.abs(result.increments) <= result.bounds)
    assert result.dollars <= result.budget


def test_pacing_ignores_outcomes():
    data = toy_inputs()
    first = replay_gated(arm="gated_ht_paced", **data)
    data["paired_cost"] *= -1
    second = replay_gated(arm="gated_ht_paced", **data)
    np.testing.assert_array_equal(first.propensities, second.propensities)
    np.testing.assert_array_equal(first.queried, second.queried)


def test_current_actions_enter_only_next_propensity():
    pacer = DisagreementPacer(np.ones(200, dtype=bool), np.ones(200), 0.2)
    assert pacer.propensity == pytest.approx(0.2)
    pacer.observe(False, 1.0)
    assert pacer.propensity == pytest.approx(0.2 * 200 / 199)


@pytest.mark.parametrize("q", [0.1, 0.4, 1.0])
@pytest.mark.parametrize("anchor", [-1.0, 0.0, 2.0])
@pytest.mark.parametrize("p", [0.0, 1.1 / 6, 0.8, 1.0])
def test_exact_conditional_mean_identity(q, anchor, p):
    unobserved = gated_increment(
        disagreement=True,
        observed_cost=None,
        propensity=q,
        anchor=anchor,
    )
    queried_mean = sum(
        probability
        * gated_increment(
            disagreement=True,
            observed_cost=z,
            propensity=q,
            anchor=anchor,
        )
        for z, probability in [(-1.0, 1 - p), (5.0, p)]
    )
    assert (1 - q) * unobserved + q * queried_mean == pytest.approx(6 * p - 1.1)


def test_full_query_matches_full_feedback_on_disagreements():
    data = toy_inputs()
    data["budget_rate"] = 1.0
    data["tariffs"][:] = 0.5
    result = replay_gated(arm="gated_ht_fixed", **data)
    assert np.all(result.propensities == 1)
    np.testing.assert_allclose(result.increments, data["paired_cost"] - 0.1)


def test_missing_outcomes_are_never_read():
    data = toy_inputs()
    data["uniforms"][:] = 0.999999
    first = replay_gated(arm="gated_ht_fixed", **data)
    data["paired_cost"][:] = np.nan
    second = replay_gated(arm="gated_ht_fixed", **data)
    np.testing.assert_array_equal(first.increments, second.increments)


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError, match="propensity"):
        gated_increment(disagreement=True, observed_cost=1.0, propensity=0)
    with pytest.raises(ValueError, match="agreement"):
        gated_increment(disagreement=False, observed_cost=0.0, propensity=0.2)
    data = toy_inputs()
    data["tariffs"][0] = 3.0
    with pytest.raises(ValueError, match="tariffs"):
        replay_gated(arm="gated_ht_paced", **data)


def test_growth_uses_pairwise_prefix_and_best_fixed_stake():
    first = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0], [100.0, 100.0]])
    second = np.ones((3, 2)) * 0.25
    result = paired_growth(first, second, onset=1)
    assert result == {"prefix": 3, "first": 1.0, "second": 0.25}
    assert paired_growth(first, second, onset=3)["first"] is None


class ExtremeProxy:
    clip = 5.1

    def __init__(self, value):
        self.value = value

    def predict(self, x):
        return np.full(len(x), self.value)

    def observe(self, x, y):
        assert abs(y) <= self.clip


@pytest.mark.parametrize("anchor", [-5.1, 5.1])
@pytest.mark.parametrize("cost", [-5.0, 5.0])
def test_ppi_bound_covers_anchor_and_outcome_extremes(anchor, cost):
    data = toy_inputs()
    data["paired_cost"][:] = cost
    result = replay_gated(arm="gated_ppi_paced", proxy_template=ExtremeProxy(anchor), **data)
    assert np.all(np.abs(result.increments) <= result.bounds + 1e-12)
    assert result.dollars <= result.budget


def test_runner_matches_existing_ungated_and_oracle_perturbation_is_learner_invariant(monkeypatch):
    # A deterministic unit fixture replaces the DGP; no registered stream is generated.
    positions = np.arange(3200)
    features = np.column_stack([np.sin(positions * (j + 1) / 37) for j in range(16)])
    frame = pd.DataFrame({"features": list(features), "target": np.where(positions % 3, 1.0, -1.0)})
    oracle_probability = [0.2]

    def fixture_generator(*args):
        oracle = pd.DataFrame({"probability_positive": np.full(3200, oracle_probability[0])})
        return None, frame, oracle, {"change_times": [1600]}

    original = comparison._one_method
    old_alarms = []

    def capture_existing(**kwargs):
        row = original(**kwargs)
        old_alarms.append(row["single_e_alarm_time"])
        return row

    monkeypatch.setattr(comparison, "_generate", fixture_generator)
    monkeypatch.setattr(comparison, "_one_method", capture_existing)
    first = comparison.comparison_seed("boundary_local_harm", 123, 0.2, "cpu")
    indexed = {row["arm"]: row for row in first}
    assert indexed["uniform_ppi"]["first_alarm"] == old_alarms[0]
    assert indexed["uniform_ppi_common96p9"]["first_alarm"] == old_alarms[2]
    oracle_probability[0] = 0.8
    second = comparison.comparison_seed("boundary_local_harm", 123, 0.2, "cpu")
    fields = ("arm", "first_alarm", "labels", "dollars", "processed", "q_min", "q_mean", "q_max")
    assert [tuple(r[f] for f in fields) for r in first] == [
        tuple(r[f] for f in fields) for r in second
    ]
    assert "xu_active" in indexed and "ppe_uniform" in indexed and "ppe_gated" in indexed
    for row in first:
        if row["budget"] is not None:
            assert row["dollars"] <= row["budget"]
        if not row["detected"] and row["onset"] is not None:
            assert row["censored_delay"] == 2400 - row["onset"]


class _SaturatedProxy:
    clip = 5.1

    def predict(self, x):
        return np.full(len(x), self.clip)

    def observe(self, x, z):
        return False


def test_ppi_anchor_at_clip_snaps_rounding_to_exact_bound():
    # Saturated proxy plus Z = -5 makes |increment| equal its bound up to ~1e-14 rounding.
    rng = np.random.default_rng(3)
    n = 400
    active = rng.random(n) < 0.3
    result = comparison.replay_gated(
        arm="gated_ppi_paced",
        x=rng.normal(size=(n, 2)),
        paired_cost=np.where(active, -5.0, 0.0),
        disagreement=active,
        tariffs=np.ones(n),
        uniforms=rng.random(n),
        validation_disagreement=rng.random(200) < 0.37,
        validation_tariffs=np.ones(200),
        budget_rate=0.2,
        proxy_template=_SaturatedProxy(),
    )
    assert result.queried.any()
    assert np.all(np.abs(result.increments) <= result.bounds)
