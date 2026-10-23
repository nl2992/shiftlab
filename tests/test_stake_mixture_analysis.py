import pandas as pd

from scripts.analyze_betting_mixture import HARM_SCENARIOS, _cluster_summary


def test_stake_mixture_analysis_bootstraps_seed_clusters_not_rows():
    rows = []
    for seed in range(2):
        for scenario in HARM_SCENARIOS:
            for method in (
                "uniform_proxy",
                "variance_proxy",
                "decision_value_proxy",
                "cost_variance_proxy",
                "cost_stabilized_proxy",
            ):
                rows.append(
                    {
                        "scenario": scenario,
                        "seed": seed,
                        "method": method,
                        "material_harm": True,
                        "harm_reached_before_budget_stop": True,
                        "single_e_detected": True,
                        "protected_e_detected": bool(seed == 1),
                    }
                )

    summary, per_cell, per_scenario = _cluster_summary(
        pd.DataFrame(rows), "protected_e_detected", bootstrap_replicates=100
    )

    assert summary["scenario_policy_cells_per_seed"] == 20
    assert summary["fixed_detections"] == 40
    assert summary["candidate_detections"] == 20
    assert summary["candidate_only"] == 0
    assert summary["fixed_only"] == 20
    assert summary["detection_difference"] == -0.5
    assert len(per_cell) == 20
    assert len(per_scenario) == 4
