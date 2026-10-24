import numpy as np
import pandas as pd

from scripts.analyze_informative_delay_stress import HARM_SCENARIOS, _paired_bootstrap


def test_stratified_paired_bootstrap_resamples_within_harm_dose():
    rows = []
    for scenario in HARM_SCENARIOS:
        for stream_id in range(30):
            rows.extend(
                [
                    {
                        "scenario": scenario,
                        "stream_id": stream_id,
                        "delay_profile": "positive_fast",
                        "bound_mode": "predictable",
                        "detected": 1,
                    },
                    {
                        "scenario": scenario,
                        "stream_id": stream_id,
                        "delay_profile": "fixed",
                        "bound_mode": "predictable",
                        "detected": 0,
                    },
                ]
            )

    estimate, lower, upper = _paired_bootstrap(
        pd.DataFrame(rows),
        profile_a="positive_fast",
        profile_b="fixed",
        bound_mode="predictable",
        metric="detected",
        rng=np.random.default_rng(71),
        replicates=200,
    )
    assert estimate == lower == upper == 1.0
