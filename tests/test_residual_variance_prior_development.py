import pandas as pd

from shiftlab.dive.residual_variance_prior_development import (
    PRIOR_METHODS,
    _paired_contrasts,
    _select_prior,
)


def test_prior_selection_uses_only_registered_primary_rates_and_tie_break():
    rows = []
    for method in PRIOR_METHODS:
        for severity in (1.5, 3.0, 4.5):
            for query_rate in (0.4, 0.8, 1.0):
                score = 0.60 if method == "quarter_start_beta_4_12" else 0.50
                if method == "early_start_mixture":
                    score = 0.60
                if query_rate == 0.4 and method == "late_start_mixture":
                    score = 1.0
                rows.append(
                    {
                        "method": method,
                        "severity": severity,
                        "query_rate": query_rate,
                        "detection_rate": score,
                    }
                )
    selection = _select_prior(pd.DataFrame(rows))
    winner = selection[selection.selected].iloc[0]
    assert winner.method == "early_start_mixture"
    assert winner.macro_detection_primary_rates == 0.60


def test_prior_screen_contrasts_pair_methods_by_seed():
    rows = []
    detections = {
        "fixed_mixture": [False, False],
        "uniform_start_mixture": [True, False],
        "early_start_mixture": [True, True],
        "late_start_mixture": [False, True],
        "center_start_mixture": [False, False],
        "quarter_start_beta_4_12": [True, False],
    }
    for seed in (1, 2):
        for method, values in detections.items():
            rows.append(
                {
                    "seed": seed,
                    "severity": 4.5,
                    "query_rate": 1.0,
                    "method": method,
                    "detected": values[seed - 1],
                }
            )
    contrasts = _paired_contrasts(pd.DataFrame(rows), bootstrap_replicates=200)
    early = contrasts[contrasts.candidate.eq("early_start_mixture")].iloc[0]
    assert early.paired_detection_difference == 1.0
    assert early.candidate_only == 2
    assert early.reference_only == 0
