import numpy as np
import pytest

from shiftlab.dive.adg_growth_prescreen import (
    LearnerSlice,
    PrescreenConfig,
    arm_specifications,
    conditional_support,
    expected_increment_mean,
    expected_log_growth,
    learner_slice,
    mixture_rows,
    prescreen_stream,
    solve_tilt,
    spend_matched_propensity,
    tilted_probability,
    unfavourable_outcome_is_positive,
)

FN, FP, EPS = 5.0, 1.0, 0.10


def _toy_stream(n=400, seed=0, disagreement_rate=0.3):
    rng = np.random.default_rng(seed)
    reference = rng.integers(0, 2, n)
    deployed = reference.copy()
    flip = rng.random(n) < disagreement_rate
    deployed[flip] = 1 - deployed[flip]
    lower, upper = conditional_support(deployed, reference, FN, FP)
    return LearnerSlice(
        deployed=deployed,
        reference=reference,
        lower=lower,
        upper=upper,
        probability_unfavourable=rng.uniform(0.05, 0.6, n),
        ridge_centered=np.clip(rng.normal(0, 1, n), -5.1, 5.1),
        residual_second_moment=rng.uniform(0.1, 4.0, n),
        tariff=rng.uniform(0.5, 2.5, n),
        fn=FN,
        fp=FP,
    )


def test_conditional_support_matches_binary_cost_table():
    lower, upper = conditional_support(np.array([1, 0, 1, 0]), np.array([0, 1, 1, 0]), FN, FP)
    np.testing.assert_array_equal(lower, [-5.0, -1.0, 0.0, 0.0])
    np.testing.assert_array_equal(upper, [1.0, 5.0, 0.0, 0.0])
    np.testing.assert_array_equal(
        unfavourable_outcome_is_positive(np.array([1, 0]), np.array([0, 1])), [False, True]
    )


@pytest.mark.parametrize("gated", [False, True])
@pytest.mark.parametrize("gamma", [0.0, 0.5, 1.0])
def test_increment_is_unbiased_for_any_anchor(gated, gamma):
    stream = _toy_stream()
    p = stream.probability_unfavourable
    anchor = stream.lower + gamma * (stream.upper - stream.lower) * 0.4
    q = np.full(len(p), 0.17)
    mean = expected_increment_mean(
        lower=stream.lower,
        upper=stream.upper,
        probability_unfavourable=p,
        propensity=q,
        anchor=anchor,
        gated=gated,
        disagreement=stream.disagreement,
        epsilon=EPS,
    )
    truth = (
        np.where(stream.disagreement, stream.lower + (stream.upper - stream.lower) * p, 0.0) - EPS
    )
    np.testing.assert_allclose(mean, truth, atol=1e-12)


def test_boundary_anchor_bound_is_free_of_propensity():
    stream = _toy_stream()
    for q in (1e-4, 0.01, 0.3, 1.0):
        expected_log_growth(
            lower=stream.lower,
            upper=stream.upper,
            probability_unfavourable=stream.probability_unfavourable,
            propensity=np.full(len(stream.lower), q),
            anchor=stream.lower,
            gated=True,
            disagreement=stream.disagreement,
            epsilon=EPS,
            bound=max(FN, FP) + EPS,
            stakes=(1.0,),
        )


def test_interior_anchor_violates_propensity_free_bound():
    stream = _toy_stream()
    with pytest.raises(ValueError, match="lower tail"):
        expected_log_growth(
            lower=stream.lower,
            upper=stream.upper,
            probability_unfavourable=stream.probability_unfavourable,
            propensity=np.full(len(stream.lower), 0.01),
            anchor=stream.lower + 0.5 * (stream.upper - stream.lower),
            gated=True,
            disagreement=stream.disagreement,
            epsilon=EPS,
            bound=max(FN, FP) + EPS,
            stakes=(1.0,),
        )


def test_full_query_growth_matches_direct_full_feedback():
    stream = _toy_stream()
    p = stream.probability_unfavourable
    growth = expected_log_growth(
        lower=stream.lower,
        upper=stream.upper,
        probability_unfavourable=p,
        propensity=np.ones(len(p)),
        anchor=stream.ridge_centered,
        gated=False,
        disagreement=stream.disagreement,
        epsilon=EPS,
        bound=5.1,
        stakes=(0.4,),
    )
    direct = np.mean(
        (1 - p) * np.log1p(0.4 * (stream.lower - EPS) / 5.1)
        + p * np.log1p(0.4 * (stream.upper - EPS) / 5.1)
    )
    assert growth[0] == pytest.approx(direct, abs=1e-12)


def test_null_growth_is_nonpositive_by_jensen():
    stream = _toy_stream()
    q = np.full(len(stream.lower), 0.2)
    growth = expected_log_growth(
        lower=stream.lower,
        upper=stream.upper,
        probability_unfavourable=np.zeros(len(stream.lower)),
        propensity=q,
        anchor=stream.lower,
        gated=True,
        disagreement=stream.disagreement,
        epsilon=EPS,
        bound=5.1,
    )
    assert np.all(growth <= 0)


def test_gated_agreement_events_spend_no_labels_and_return_minus_epsilon():
    stream = _toy_stream()
    arms = arm_specifications(stream, 0.2, EPS)
    spec = arms["adg_gamma0"]
    agree = ~stream.disagreement
    mean = expected_increment_mean(
        lower=stream.lower,
        upper=stream.upper,
        probability_unfavourable=stream.probability_unfavourable,
        propensity=spec["propensity"],
        anchor=spec["anchor"],
        gated=True,
        disagreement=stream.disagreement,
        epsilon=EPS,
    )
    np.testing.assert_allclose(mean[agree], -EPS)


def test_tilt_reaches_target_excess():
    stream = _toy_stream()
    eta = solve_tilt(
        lower=stream.lower,
        upper=stream.upper,
        probability_unfavourable=stream.probability_unfavourable,
        disagreement=stream.disagreement,
        epsilon=EPS,
        target_excess=0.2,
    )
    p = tilted_probability(stream.probability_unfavourable, stream.disagreement, eta)
    width = stream.upper - stream.lower
    realised = np.mean(np.where(stream.disagreement, stream.lower + width * p, 0.0)) - EPS
    assert realised == pytest.approx(0.2, abs=1e-12)


def test_spend_matching_hits_target_and_respects_bounds():
    rng = np.random.default_rng(3)
    score, tariff = rng.uniform(0, 2, 500), rng.uniform(0.5, 2.5, 500)
    q = spend_matched_propensity(score, tariff, target_spend=0.3, floor=0.1)
    assert np.mean(q * tariff) == pytest.approx(0.3, rel=1e-9)
    assert q.min() >= 0.1 and q.max() <= 1.0
    with pytest.raises(ValueError, match="floor"):
        spend_matched_propensity(score, tariff, target_spend=0.01, floor=0.1)


def test_arms_are_spend_matched_and_anchor_irrelevant_at_full_disagreement_coverage():
    stream = _toy_stream(disagreement_rate=0.05)
    arms = arm_specifications(stream, 0.2, EPS)
    assert arms["adg_gamma0"]["q_gated"] == 1.0
    growth = {
        name: expected_log_growth(
            lower=stream.lower,
            upper=stream.upper,
            probability_unfavourable=stream.probability_unfavourable,
            propensity=arms[name]["propensity"],
            anchor=arms[name]["anchor"],
            gated=True,
            disagreement=stream.disagreement,
            epsilon=EPS,
            bound=arms[name]["bound"],
        )
        for name in ("a3_discern_gated", "adg_gamma0", "adg_gamma1")
    }
    np.testing.assert_allclose(growth["a3_discern_gated"], growth["adg_gamma0"])
    np.testing.assert_allclose(growth["adg_gamma0"], growth["adg_gamma1"])
    spends = {
        name: np.mean(spec["propensity"] * stream.tariff)
        for name, spec in arms.items()
        if not spec["gated"]
    }
    target = 0.2 * stream.tariff.mean()
    assert all(value == pytest.approx(target, rel=1e-9) for value in spends.values())


def test_learner_slice_uses_only_pre_monitor_events_and_is_deterministic():
    config = PrescreenConfig(seeds=1).validate()
    first = learner_slice("stationary", config.seed_offset, config)
    second = learner_slice("stationary", config.seed_offset, config)
    assert len(first.tariff) == 400
    np.testing.assert_array_equal(first.deployed, second.deployed)
    np.testing.assert_allclose(first.probability_unfavourable, second.probability_unfavourable)


def test_prescreen_stream_rows_and_mixture():
    config = PrescreenConfig(seeds=1, budget_rates=(0.2,), primary_budget=0.2).validate()
    rows = mixture_rows(prescreen_stream("boundary_local_harm", 0, config))
    mix = [row for row in rows if row["arm"] == "adg_gamma_mix"]
    assert len(mix) == 1 + len(config.target_excesses)
    for row in rows:
        if row["law"] == "natural":
            assert row["best_growth"] <= 1e-12 or row["mean_increment"] > 0
