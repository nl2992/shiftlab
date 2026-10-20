import json
from pathlib import Path

import pandas as pd

from shiftlab.data.synthetic import SCENARIOS


def test_scenario_quantile_report_covers_every_registered_scenario():
    path = Path(__file__).parents[2] / "data" / "reports" / "scenario_quantile_validation.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    evidence = pd.DataFrame(report["evidence"])

    assert report["scenarios"] == list(SCENARIOS)
    assert evidence.scenario.tolist() == list(SCENARIOS)
    assert evidence.passes.all()
    regression = evidence[evidence.status == "validated_regression_quantile"]
    classification = evidence[evidence.status == "classification_without_residual_quantile"]
    assert not regression.empty
    assert len(regression) + len(classification) == len(SCENARIOS)
    assert (regression.max_exact_cdf_error < 1e-8).all()
    assert (regression.max_seed_coverage_error < 0.025).all()
    assert ((regression.pooled_empirical_coverage - 0.9).abs() < 0.015).all()
