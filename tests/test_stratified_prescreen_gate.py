import pandas as pd
import pytest

from scripts.run_stratified_growth_prescreen import MATCHED, decide


@pytest.mark.parametrize(
    "growth,pooled,feasible",
    [(1.0, 0.1, True), (0.0, 0.1, True), (1.0, 0.0, True), (1.0, 0.1, False)],
)
def test_identical_known_composition_never_passes(growth, pooled, feasible):
    rows = []
    for law in ("localized_harm", "homogeneous_harm"):
        for arm in ("stratified_candidate", *MATCHED):
            rows.append(
                {
                    "budget_rate": 0.05,
                    "K": 4,
                    "allocation": "uncapped",
                    "working_law": law,
                    "arm": arm,
                    "mean_growth": growth,
                    "all_feasible": feasible,
                    "mean_pooled_centered_mean": pooled,
                }
            )
    result = decide(pd.DataFrame(rows))
    assert not result["passes"]
    assert len(result["trials"]) == 1
    assert result["trials"][0]["growth_ratio"] == (1.0 if growth > 0 else None)
