import numpy as np

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
