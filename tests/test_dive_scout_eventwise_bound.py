from types import SimpleNamespace

import pytest

from shiftlab.dive.budgeted_promotion import (
    BudgetedPromotionConfig,
    _budget_limited_prefix_length,
    _run_seed,
)
from shiftlab.dive.promotion_grid import _time_splits


@pytest.mark.parametrize(
    ("query_flags", "available_budget", "expected_prefix"),
    [
        ([False, True, False, True], 1, 2),
        ([False, True, False, True], 2, 4),
        ([False, True, False, True], 3, 4),
        ([False, False, False], 1, 3),
        ([True, True], 0, 0),
    ],
)
def test_budget_limited_prefix_matches_eventwise_stop_rule(
    query_flags: list[bool], available_budget: int, expected_prefix: int
):
    assert _budget_limited_prefix_length(query_flags, available_budget) == expected_prefix


@pytest.mark.parametrize("budget_rate", [0.20, 0.40])
def test_eventwise_uniform_propensity_bound_uses_known_query_rate(budget_rate: float):
    config = BudgetedPromotionConfig(
        n=1200,
        d=4,
        seeds=1,
        switching_cost=0.05,
        budget_rates=(budget_rate,),
        query_policies=("uniform",),
        alpha_allocations=("rank",),
        estimators=("direct_ipw",),
        monitoring_rules=("fixed_mixture",),
        context_feature_index=3,
        context_target_prevalence=0.1,
        context_signal_strength=0.0,
        context_proxy_error=0.0,
        context_certification_prevalence=0.9,
        include_scout_context_policy=True,
        scenario_subset=("candidate_context_heterogeneity",),
        create_plot=False,
        device="cpu",
    ).validate()
    scenario = SimpleNamespace(
        name="candidate_context_heterogeneity",
        fn_cost=5.0,
        fp_cost=1.0,
        harmful_adaptation=False,
    )
    rows = _run_seed(
        scenario=scenario,
        seed=20_268_901,
        config=config,
        device="cpu",
        scout_only=True,
        scout_bound_modes=("minimum_propensity", "eventwise_propensity"),
    )

    scout_rows = {row["bound_mode"]: row for row in rows}
    assert set(scout_rows) == {"minimum_propensity", "eventwise_propensity"}
    _, validation_end, monitor_end = _time_splits(config.n)
    deployment_length = config.n - monitor_end
    switching_rate = config.switching_cost / deployment_length
    exact = scout_rows["eventwise_propensity"]
    floor = scout_rows["minimum_propensity"]
    assert exact["mean_event_process_bound"] == pytest.approx(5 / budget_rate + switching_rate)
    assert floor["mean_event_process_bound"] == pytest.approx(
        5 / (budget_rate / 2) + switching_rate
    )
    assert exact["global_process_bound"] == pytest.approx(floor["global_process_bound"])
    assert exact["mean_event_process_bound"] < floor["mean_event_process_bound"]
    assert exact["candidate_is_monitor_null"]
    assert exact["labels_queried"] <= exact["label_budget"]
    assert validation_end < exact["certification_start_index"] < monitor_end
