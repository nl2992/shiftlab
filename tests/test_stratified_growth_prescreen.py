from dataclasses import replace

import numpy as np
import pytest

from shiftlab.dive.adg_growth_prescreen import LearnerSlice
from shiftlab.dive.stratified_growth_prescreen import (
    EPSILON,
    _working_design_moments,
    _working_laws,
    evaluate_slice,
    fixed_tariff_strata,
)


def toy_slice() -> LearnerSlice:
    tariffs = [0.5, 2.5, 0.5, 2.5]
    deployed = [0, 0, 0, 0]
    reference = [0, 0, 1, 1]
    # Three repeated observations at each of the seven fixed K=8 disagreement-bin centers.
    for index in range(7):
        center = 0.5 + (index + 0.5) * (2.0 / 7)
        for _ in range(3):
            tariffs.append(center)
            deployed.append(0)
            reference.append(1)
    actions = np.asarray(deployed, dtype=int)
    refs = np.asarray(reference, dtype=int)
    lower = np.where(actions == refs, 0.0, -1.0)
    upper = np.where(actions == refs, 0.0, 5.0)
    return LearnerSlice(
        deployed=actions,
        reference=refs,
        lower=lower,
        upper=upper,
        probability_unfavourable=np.full(len(actions), 0.4),
        ridge_centered=np.linspace(-0.2, 0.2, len(actions)),
        residual_second_moment=np.full(len(actions), 1.0),
        tariff=np.asarray(tariffs, dtype=float),
        fn=5.0,
        fp=1.0,
    )


def reversed_toy_slice() -> LearnerSlice:
    stream = toy_slice()
    disagreement = stream.deployed != stream.reference
    deployed = np.where(disagreement, stream.reference, stream.deployed)
    reference = stream.deployed.copy()
    return replace(
        stream,
        deployed=deployed,
        reference=reference,
        lower=np.where(disagreement, -5.0, 0.0),
        upper=np.where(disagreement, 1.0, 0.0),
    )


@pytest.mark.parametrize("K", [2, 4, 8])
def test_fixed_tariff_mapping_is_role_invariant_and_covers_registered_bins(K):
    stream = toy_slice()
    strata = fixed_tariff_strata(stream, K)
    swapped = fixed_tariff_strata(
        replace(stream, deployed=stream.reference, reference=stream.deployed), K
    )
    np.testing.assert_array_equal(strata, swapped)
    assert np.all(strata[stream.deployed == stream.reference] == 0)
    assert set(np.unique(strata)) == set(range(K))
    assert np.all(strata[stream.tariff == 2.5] <= K - 1)


@pytest.mark.parametrize("K", [2, 4, 8])
@pytest.mark.parametrize("budget", [0.02, 0.20])
def test_allocation_spends_are_feasible_and_candidate_equals_independent_chugg(K, budget):
    stream = toy_slice()
    rows = evaluate_slice(stream, budget, K)
    assert {row["allocation"] for row in rows} == {
        "range_limited",
        "cap_dominated",
        "uncapped",
    }
    assert {row["working_law"] for row in rows} == {
        "homogeneous_harm",
        "localized_harm",
        "mixed_sign",
    }
    candidates = [row for row in rows if row["arm"] == "stratified_candidate"]
    chugg = [row for row in rows if row["arm"] == "chugg_subgroup_composition"]
    assert len(candidates) == len(chugg) == 9
    for candidate, comparator in zip(candidates, chugg, strict=True):
        assert comparator["identity_error"] <= 1e-12
        assert candidate["identity_error"] <= 1e-12
        np.testing.assert_allclose(
            candidate["stake_calendar_rates"],
            comparator["stake_calendar_rates"],
            atol=1e-12,
            rtol=0,
        )
        assert candidate["expected_spend"] <= candidate["target_spend"] + 1e-12
        assert candidate["spend_within_target"]
        assert len(candidate["q_by_stratum"]) == K
        assert len(candidate["bound_by_stratum"]) == K
        assert len(candidate["alpha_L_by_stratum"]) == K
        assert all(row["q"] >= 0.01 and row["q"] <= 1.0 for row in candidate["per_stratum"][1:])

    capped_arms = {
        "stratified_candidate",
        "chugg_subgroup_composition",
        "stratified_common_bound",
        "stratified_proportional_query",
        "pooled_same_query_global_bound",
        "pooled_uniform_correct_bound_U1",
        "gated_pooled_HT_G1f",
    }
    for row in rows:
        if row["arm"] in capped_arms:
            assert row["expected_spend"] <= row["target_spend"] + 1e-12
    assert all(
        not row["label_matched"]
        for row in rows
        if row["arm"] in {"full_feedback", "oracle_strata_upper"}
    )


@pytest.mark.parametrize("K", [2, 4, 8])
def test_mixed_sign_law_has_zero_pooled_mean_when_support_feasible(K):
    rows = evaluate_slice(toy_slice(), 0.20, K)
    mixed = [
        row
        for row in rows
        if row["arm"] == "stratified_candidate" and row["working_law"] == "mixed_sign"
    ]
    assert all(row["feasible"] for row in mixed)
    for row in mixed:
        assert row["pooled_zero_mean_check"]
        assert abs(row["pooled_centered_mean"]) <= 1e-12


def test_working_laws_use_probability_of_upper_loss_for_both_action_orientations():
    for stream, expected_homogeneous_gross in ((toy_slice(), 4.4), (reversed_toy_slice(), 0.4)):
        strata = fixed_tariff_strata(stream, 4)
        laws = _working_laws(stream, strata, 4)
        homogeneous_p_upper = np.asarray(laws["homogeneous_harm"]["probability_unfavourable"])
        disagreement = strata != 0
        gross = (1 - homogeneous_p_upper) * stream.lower + homogeneous_p_upper * stream.upper
        assert np.mean(gross[disagreement]) == pytest.approx(expected_homogeneous_gross, abs=1e-12)

        localized_p_upper = np.asarray(laws["localized_harm"]["probability_unfavourable"])
        localized_gross = (1 - localized_p_upper) * stream.lower + localized_p_upper * stream.upper
        for k in range(2, 4):
            mask = strata == k
            if np.any(mask):
                assert np.mean(localized_gross[mask]) == pytest.approx(0.0, abs=1e-12)


def test_reversed_orientation_mixed_sign_is_pooled_null_when_feasible_and_flags_infeasible():
    stream = reversed_toy_slice()
    K2_laws = _working_laws(stream, fixed_tariff_strata(stream, 2), 2)
    K2_mixed = K2_laws["mixed_sign"]
    assert K2_mixed["feasible"]
    assert K2_mixed["pooled_zero_mean_check"]
    assert abs(K2_mixed["pooled_centered_mean"]) <= 1e-12

    K4_laws = _working_laws(stream, fixed_tariff_strata(stream, 4), 4)
    K4_mixed = K4_laws["mixed_sign"]
    assert not K4_mixed["feasible"]
    upper_probabilities = np.asarray(K4_mixed["probability_unfavourable"])
    assert np.any(upper_probabilities > 1.0)


def test_independent_chugg_rate_matches_hand_enumerated_atoms():
    stream = toy_slice()
    rows = evaluate_slice(stream, 0.20, 4)
    row = next(
        result
        for result in rows
        if result["allocation"] == "range_limited"
        and result["working_law"] == "homogeneous_harm"
        and result["arm"] == "chugg_subgroup_composition"
    )
    k = 1
    per_stratum = row["per_stratum"][k]
    mask = fixed_tariff_strata(stream, 4) == k
    p = np.asarray(
        _working_laws(stream, fixed_tariff_strata(stream, 4), 4)["homogeneous_harm"][
            "probability_unfavourable"
        ]
    )[mask]
    q = float(per_stratum["q"])
    bound = float(per_stratum["bound"])
    h = stream.ridge_centered[mask] + EPSILON
    stake = 0.2
    event_expectations = []
    for index in range(np.count_nonzero(mask)):
        terms = (
            ((1 - p[index]) * (1 - q), h[index] - EPSILON),
            (p[index] * (1 - q), h[index] - EPSILON),
            ((1 - p[index]) * q, h[index] + (stream.lower[mask][index] - h[index]) / q - EPSILON),
            (p[index] * q, h[index] + (stream.upper[mask][index] - h[index]) / q - EPSILON),
        )
        event_expectations.append(
            sum(
                mass * np.log(1 + stake * increment / bound)
                for mass, increment in terms
                if mass > 0
            )
        )
    hand_rate = float(np.mean(event_expectations))
    stake_index = row["stakes"].index(stake)
    assert per_stratum["conditional_stake_growths"][stake_index] == pytest.approx(
        hand_rate, abs=1e-12
    )


def test_empty_disagreement_bins_keep_floor_and_zero_factors_are_minus_infinity():
    actions = np.zeros(8, dtype=int)
    stream = LearnerSlice(
        deployed=actions,
        reference=actions.copy(),
        lower=np.zeros(8),
        upper=np.zeros(8),
        probability_unfavourable=np.full(8, 0.5),
        ridge_centered=np.zeros(8),
        residual_second_moment=np.ones(8),
        tariff=np.full(8, 1.5),
        fn=5.0,
        fp=1.0,
    )
    rows = evaluate_slice(stream, 0.20, 4)
    candidate = next(
        row
        for row in rows
        if row["allocation"] == "range_limited"
        and row["working_law"] == "homogeneous_harm"
        and row["arm"] == "stratified_candidate"
    )
    assert candidate["q_by_stratum"] == [0.0, 0.01, 0.01, 0.01]
    agreement_rates = candidate["per_stratum"][0]["conditional_stake_growths"]
    assert agreement_rates[-1] == float("-inf")
    assert candidate["per_stratum"][0]["reachable_zero_factors_by_stake"][-1] == 16
    for stratum in candidate["per_stratum"][1:]:
        assert stratum["frequency"] == 0
        assert stratum["q"] == 0.01


def test_working_design_moment_decomposition_matches_exact_ppi_second_moment():
    stream = toy_slice()
    strata = fixed_tariff_strata(stream, 4)
    A, C, frequencies = _working_design_moments(stream, strata, 4)
    assert np.all(C > 0)
    assert np.all(frequencies > 0)
    disagreement = strata != 0
    p = np.zeros(len(strata), dtype=float)
    p[disagreement] = (0.35 - stream.lower[disagreement]) / (
        stream.upper[disagreement] - stream.lower[disagreement]
    )
    h = stream.ridge_centered + EPSILON
    d0 = stream.fp * (stream.deployed - stream.reference)
    d1 = stream.fn * (stream.reference - stream.deployed)
    for k in range(1, 4):
        mask = strata == k
        q = 0.37
        residual = (1 - p[mask]) * (d0[mask] - h[mask]) ** 2 + p[mask] * (d1[mask] - h[mask]) ** 2
        score2 = (1 - p[mask]) * (d0[mask] - EPSILON) ** 2 + p[mask] * (d1[mask] - EPSILON) ** 2
        V = float(np.mean(score2 - residual) + np.mean(residual) / q)
        assert V == pytest.approx(A[k - 1] + C[k - 1] / q, abs=1e-12)


def test_registered_budget_and_k_reject_unregistered_values():
    stream = toy_slice()
    with pytest.raises(ValueError, match="registered rates"):
        evaluate_slice(stream, 0.03, 2)
    with pytest.raises(ValueError, match="registered values"):
        evaluate_slice(stream, 0.20, 3)
