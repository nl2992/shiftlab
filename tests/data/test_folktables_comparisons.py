import numpy as np
import pandas as pd
import pytest

from scripts.folktables_diagnostics import evaluate_comparisons


def frame():
    X = np.random.default_rng(42).normal(size=(80, 2))
    return pd.DataFrame(
        {
            "features": list(X),
            "target": (X[:, 0] > 0).astype(float),
            "sample_weight": np.arange(80) + 1,
            "domain_id": ["CA-2017"] * 40 + ["NJ-2018"] * 40,
            "split": "unassigned",
        }
    )


@pytest.mark.parametrize(
    "train,test", [(["CA-2017"], ["CA-2017"]), (["CA-2017"], ["missing"]), ([], ["NJ-2018"])]
)
def test_invalid_comparison_rejected(train, test):
    with pytest.raises(ValueError, match="disjoint"):
        evaluate_comparisons(
            frame(),
            {"comparisons": [{"train_domains": train, "test_domains": test, "kind": "joint"}]},
        )


def test_retrospective_evidence_preserves_training_boundary_and_weighted_rates():
    source = frame()
    evidence = evaluate_comparisons(
        source,
        {
            "comparisons": [
                {"train_domains": ["CA-2017"], "test_domains": ["NJ-2018"], "kind": "joint"}
            ]
        },
    )
    assert source.split.eq("unassigned").all()
    test = evidence[evidence.split == "test"].iloc[0]
    assert test.domain == "NJ-2018" and test.n == 40
    assert 0 <= test.weighted_accuracy <= 1
    assert 0 <= test.weighted_decision_loss <= 5
    assert "No survey-design" in test.uncertainty
