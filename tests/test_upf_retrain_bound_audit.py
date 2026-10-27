from scripts.audit_upf_retrain_count_bound import optimal_schedule


def test_upf_published_retrain_count_bound_has_one_step_counterexample():
    result = optimal_schedule([[1.0], [0.0]], retrain_cost=0.25)

    assert result["adjacent_model_difference_bound_L"] == 1.0
    assert result["optimal_cost"] == 0.25
    assert result["optimal_retrains"] == 1
    assert result["proposition_3_1_claimed_upper_bound"] == 0.5
    assert result["violates_claimed_bound"] is True
