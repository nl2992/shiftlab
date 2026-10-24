import numpy as np

from shiftlab.dive.contextual_stratified_intervention import (
    generate_contextual_streams,
    run_grid,
)
from shiftlab.dive.contextual_stratified_validation import _cp_upper


def test_contextual_generator_has_exact_balanced_group_mean_gains():
    _, _, gains, expected = generate_contextual_streams(
        scenario="heterogeneous_reversal", seeds=4, horizon=200, seed=7, device="cpu"
    )
    assert expected.shape == (400,)
    assert np.allclose(expected[:200], 1.0)
    assert np.allclose(expected[200::2], 0.4)
    assert np.allclose(expected[201::2], -0.47)
    assert np.max(np.abs(gains)) <= 5.0
    assert np.isclose(expected[200:].mean(), -0.035)

    _, _, _, global_boundary = generate_contextual_streams(
        scenario="rollback_boundary_global", seeds=2, horizon=200, seed=8, device="cpu"
    )
    _, _, _, stratified_boundary = generate_contextual_streams(
        scenario="rollback_boundary_stratified", seeds=2, horizon=200, seed=9, device="cpu"
    )
    assert np.allclose(global_boundary[200:], -0.05 / 200)
    assert np.allclose(stratified_boundary[200:], -0.05 / 100)


def test_contextual_stratified_grid_cpu_smoke(tmp_path):
    metrics, contrasts, manifest = run_grid(
        tmp_path,
        seeds=2,
        horizon=200,
        query_rates=(0.4,),
        budget_rates=(0.2,),
        device="cpu",
        bootstrap_replicates=100,
    )
    assert manifest["status"] == "development_only_no_independent_calibration_or_confirmation"
    assert manifest["all_label_caps_respected"]
    assert not manifest["evaluator_oracle_used_by_policy"]
    assert set(metrics.method) == {
        "continue",
        "unconditional_promote",
        "promotion_only",
        "promotion_rollback",
        "stratified_promotion_rollback",
    }
    assert metrics.budget_respected.all()
    contextual = metrics.loc[metrics.method.eq("stratified_promotion_rollback")]
    assert (contextual.labels_queried <= contextual.label_budget).all()
    assert not contrasts.empty
    assert (tmp_path / "metrics.parquet").is_file()
    assert (tmp_path / "manifest.json").is_file()


def test_exact_binomial_upper_bound_handles_zero_events_and_monotonicity():
    assert 0 < _cp_upper(0, 2_000, 0.05 / 8) < 0.01
    assert _cp_upper(1, 2_000, 0.05 / 8) > _cp_upper(0, 2_000, 0.05 / 8)
