import numpy as np

from shiftlab.sota_search.active_rcps_learning import FixedRiskPredictor, fixed_question_features
from shiftlab.sota_search.learned_paired_rcps import learned_paired_rcps


def stream(paths=2, horizon=40):
    return {
        "loss": np.ones((paths, horizon)),
        "candidate_loss": np.zeros((paths, horizon)),
        "score": np.full((paths, horizon), 0.5),
        "candidate_score": np.zeros((paths, horizon)),
    }


def test_no_budget_no_evidence_or_queries():
    r = learned_paired_rcps(stream(), budget=0, return_trace=True)
    assert np.all(r["labels"] == 0)
    assert np.all(r["first"] == 40)
    assert np.all(r["trace"]["xi"] == 0)
    assert np.all(r["trace"]["logwealth"] == 0)


def test_no_early_feedback_and_pending_budget():
    r = learned_paired_rcps(
        stream(), frac=1, floor=1, budget=3, delay=5, return_trace=True, switch_cost=0
    )
    assert np.all(r["labels"] == 3)
    assert np.all(r["trace"]["cv"][:, :5] == 0)
    assert np.all(r["trace"]["lambda"][:, :5] == 0)
    assert np.all(r["trace"]["query"][:, :3] == 1)
    assert np.all(r["trace"]["query"][:, 3:] == 0)


def test_hidden_outcomes_cannot_change_pre_release_actions():
    a = stream(horizon=30)
    b = {k: v.copy() for k, v in a.items()}
    b["loss"][:, :5] = 0
    ra = learned_paired_rcps(a, delay=5, seed=7, return_trace=True)
    rb = learned_paired_rcps(b, delay=5, seed=7, return_trace=True)
    for k in ["q", "cv", "lambda", "query", "logwealth"]:
        np.testing.assert_array_equal(ra["trace"][k][:, :5], rb["trace"][k][:, :5])


def test_published_residual_variant_is_not_source_alias():
    a = stream(horizon=60)
    a["loss"][:] = 0.6
    ra = learned_paired_rcps(a, frac=1, floor=0.05, seed=9, return_trace=True)
    rb = learned_paired_rcps(
        a,
        variance_target="residual",
        normalization="paper",
        frac=1,
        floor=0.05,
        seed=9,
        return_trace=True,
    )
    assert not np.array_equal(ra["trace"]["q"], rb["trace"]["q"])
    assert np.all(ra["labels"] <= 60) and np.all(rb["labels"] <= 60)


def test_wealth_uses_frozen_issue_time_factors():
    a = stream(horizon=100)
    a["loss"][:] = 0.6
    result = learned_paired_rcps(a, delay=7, seed=13, return_trace=True)
    trace = result["trace"]
    logs = np.log1p(trace["lambda"] * trace["xi"])
    np.testing.assert_allclose(
        trace["logwealth"][:, 7:], np.cumsum(logs, axis=1)[:, :-7], atol=1e-14
    )


def test_projected_paper_normalizer_stays_finite_at_long_horizon():
    a = stream(paths=1, horizon=2000)
    a["loss"][:] = 0.6
    result = learned_paired_rcps(
        a, variance_target="residual", normalization="paper", seed=19, return_trace=True
    )
    assert np.isfinite(result["total_cost"]).all()
    assert result["labels"][0] <= 400
    assert np.all((result["trace"]["q"] >= 0.05) & (result["trace"]["q"] <= 1))


def test_predictor_bounds_cover_all_proxy_inputs():
    rng = np.random.default_rng(271)
    model = FixedRiskPredictor(7)
    model.optimizer.value[:] = rng.normal(0, 0.2, (7, 13))
    lower, upper = model.bounds()
    for x in np.linspace(0, 1, 101):
        value = model.predict(fixed_question_features(np.full(7, x)))
        assert np.all(value >= lower - 1e-14)
        assert np.all(value <= upper + 1e-14)
    at_knots = np.stack(
        [model.predict(fixed_question_features(np.full(7, x))) for x in [0, 0.5, 1]]
    )
    np.testing.assert_allclose(at_knots.min(0), lower, atol=1e-14)
    np.testing.assert_allclose(at_knots.max(0), upper, atol=1e-14)


def test_predictable_ranges_bound_issued_values_and_factors():
    a = stream(paths=3, horizon=300)
    a["loss"][:] = np.random.default_rng(52).random((3, 300))
    result = learned_paired_rcps(a, cap_mode="predictor", seed=27, return_trace=True)
    trace = result["trace"]
    assert np.all(trace["q"] >= trace["q_bound"] - 1e-12)
    assert np.all(trace["cv"] >= trace["cv_min"] - 1e-12)
    assert np.all(1 + trace["lambda"] * trace["xi"] >= 0.5 - 1e-12)
    np.testing.assert_allclose(
        trace["logwealth"][:, 5:],
        np.cumsum(np.log1p(trace["lambda"] * trace["xi"]), axis=1)[:, :-5],
        atol=1e-12,
    )
