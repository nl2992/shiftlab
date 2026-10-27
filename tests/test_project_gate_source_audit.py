from __future__ import annotations

import pandas as pd

from scripts.audit_project_gate_source import (
    summarize_followup_response,
    summarize_w3_policy_endpoint,
)


def test_followup_response_uses_linked_ids_and_reports_arm_rates() -> None:
    application = pd.DataFrame(
        {
            "gateid": ["A", "B", "C", "D"],
            "treatment": [0, 0, 1, 1],
            "w1_completed": [1, 0, 1, 1],
        }
    )
    wave1 = pd.DataFrame({"gateid": ["A", "C", "D"]})

    result = summarize_followup_response(application, {"wave1.sas7bdat": wave1})

    by_treatment = result["wave1.sas7bdat"]["by_treatment"]
    assert by_treatment["0"]["linked_followup_n"] == 1
    assert by_treatment["0"]["response_rate"] == 0.5
    assert by_treatment["1"]["response_rate"] == 1.0
    assert by_treatment["0"]["completion_flag_mismatches_link"] == 0
    assert by_treatment["1"]["completion_flag_mismatches_link"] == 0


def test_w3_endpoint_screen_only_emits_aggregate_outcome_and_timing() -> None:
    application = pd.DataFrame(
        {
            "gateid": ["A", "B", "C"],
            "treatment": [0, 1, 0],
            "date_random_assignment": pd.to_datetime(["2000-01-01", "2000-01-01", "2000-01-01"]),
        }
    )
    wave3 = pd.DataFrame(
        {
            "gateid": ["A", "B"],
            "int_dt": pd.to_datetime(["2001-01-01", "2002-01-01"]),
            "dwkc_a": [0, 1],
        }
    )

    result = summarize_w3_policy_endpoint(application, wave3)

    assert result["status"] == "aggregate_screen_only"
    assert result["rows_written"] is False
    assert result["counts_by_treatment"]["0"]["endpoint_counts"] == {"0": 1}
    assert result["counts_by_treatment"]["1"]["endpoint_counts"] == {"1": 1}
    assert result["assignment_to_interview_lag"]["valid_pairs"] == 2
    assert result["assignment_to_interview_lag"]["minimum_days"] == 366.0
    bounds = result["no_assumption_attrition_bounds"]
    assert bounds["by_arm"]["0"]["no_assumption_mean_upper"] == 0.5
    assert bounds["ate_bounds"] == {"lower": 0.5, "upper": 1.0}
