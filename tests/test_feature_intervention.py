import json

import numpy as np
import pytest

from shiftlab.dive.closed_loop_intervention import _simulate_gate
from shiftlab.dive.feature_intervention import (
    GAIN_BOUND,
    _probability_positive,
    generate_feature_cost_streams,
    run_grid,
)
from shiftlab.dive.feature_intervention_calibration import _cp_upper
from shiftlab.dive.feature_intervention_confirmation import run_confirmation


def test_stage_profiles_have_the_registered_expected_gain_directions():
    stationary = _probability_positive("stationary", 100)
    nuisance = _probability_positive("benign_nuisance", 100)
    boundary = _probability_positive("boundary_local_harm", 100)
    reversal = _probability_positive("harmful_adaptation", 100)
    persistent = _probability_positive("persistent_benefit", 100)

    assert np.allclose(0.5 * (6 * stationary - 1), 0)
    assert np.allclose(0.5 * (6 * nuisance - 1), 0)
    assert (boundary[:100] == 1 / 6).all() and (boundary[100:] > 1 / 6).all()
    assert (reversal[:100] > 1 / 6).all() and (reversal[100:] < 1 / 6).all()
    assert (persistent > 1 / 6).all()


def test_rollback_boundary_is_least_favourable_and_exact_cp_is_conservative():
    horizon = 400
    rollback_cost = 0.05
    probability = _probability_positive("rollback_boundary", horizon, rollback_cost)
    expected_gain = 0.5 * (6 * probability - 1)
    assert np.allclose(expected_gain[horizon:], -rollback_cost / horizon, atol=1e-14)
    assert np.isclose(_cp_upper(0, 2000, 0.0125), 1 - 0.0125 ** (1 / 2000))


def test_feature_cost_gain_is_bounded_and_nuisance_shift_preserves_decision_context():
    features, outcomes, gains, oracle = generate_feature_cost_streams(
        scenario="benign_nuisance", seeds=4, horizon=100, seed=12, device="cpu"
    )
    assert features.shape == (4, 200, 8)
    assert outcomes.shape == gains.shape == (4, 200)
    assert np.max(np.abs(gains)) <= GAIN_BOUND
    assert oracle["nuisance_mean_shift_l2"] > 0
    assert np.allclose(oracle["expected_incumbent_minus_candidate_cost"], 0, atol=1e-14)


def test_future_reversal_is_unidentifiable_from_predeployment_stream():
    horizon = 200
    persistent = generate_feature_cost_streams(
        scenario="persistent_benefit", seeds=8, horizon=horizon, seed=91, device="cpu"
    )
    reversal = generate_feature_cost_streams(
        scenario="harmful_adaptation", seeds=8, horizon=horizon, seed=91, device="cpu"
    )

    # Shared randomness is a pathwise witness that both worlds induce the same
    # learner-visible predeployment law; their evaluator-side future gains differ.
    for left, right in zip(persistent[:3], reversal[:3], strict=True):
        assert np.array_equal(left[:, :horizon], right[:, :horizon])
    persistent_future_gain = persistent[3]["expected_incumbent_minus_candidate_cost"][horizon:]
    reversal_future_gain = reversal[3]["expected_incumbent_minus_candidate_cost"][horizon:]
    assert np.all(persistent_future_gain > 0)
    assert np.all(reversal_future_gain < 0)


def test_vectorized_gate_uses_actual_cost_support_and_respects_label_cap():
    horizon = 100
    gains = np.full((3, 2 * horizon), GAIN_BOUND, dtype=float)
    query_uniforms = np.zeros_like(gains)
    gate = _simulate_gate(
        gains,
        query_uniforms,
        query_rate=0.5,
        label_budget=50,
        alpha=0.05,
        promotion_cost=0.05,
        rollback_cost=0.05,
        horizon=horizon,
        gain_bound=GAIN_BOUND,
    )
    assert gate["labels_queried"].tolist() == [50, 50, 50]
    assert gate["budget_respected"].all()
    assert np.all(gate["queried_mask"].sum(axis=1) == 50)


def test_feature_intervention_development_smoke_writes_replayable_results(tmp_path):
    metrics, summary, contrasts, manifest = run_grid(
        tmp_path,
        seeds=2,
        horizon=100,
        query_rate=0.8,
        budget_rate=0.4,
        device="cpu",
        bootstrap_replicates=100,
    )
    assert len(metrics) == 6 * 4 * 2
    assert len(summary) == 6 * 4
    assert not contrasts.empty
    assert metrics.budget_respected.all()
    assert manifest["status"] == "development_only_not_independent_calibration_or_confirmation"
    assert manifest["oracle_is_evaluator_only"]
    assert manifest["contract_replay_events_seed0_stationary"] >= 2 * 200
    assert (tmp_path / "metrics.parquet").is_file()
    assert (tmp_path / "manifest.json").is_file()
    assert "not calibration" in (tmp_path / "report.md").read_text().lower()


def test_confirmation_requires_a_passed_calibration_manifest(tmp_path):
    calibration = tmp_path / "calibration.json"
    calibration.write_text(json.dumps({"status": "failed"}), encoding="utf-8")
    with pytest.raises(ValueError, match="did not pass"):
        run_confirmation(
            tmp_path / "confirmation",
            calibration_manifest=calibration,
            seeds=2,
            horizon=100,
            device="cpu",
        )
