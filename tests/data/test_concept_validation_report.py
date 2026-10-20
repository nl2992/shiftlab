import json
from pathlib import Path

import pandas as pd


def test_concept_validation_report_gates_every_mechanism_dimension_and_regime():
    path = Path(__file__).parents[2] / "data" / "reports" / "concept_residual_validation.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    evidence = pd.DataFrame(report["evidence"])

    assert report["dimensions"] == [2, 3, 8, 16]
    assert len(evidence) == 224
    assert evidence["passes"].all()
    assert evidence.groupby(["scenario", "dimension", "severity"]).size().isin([1, 2]).all()
    assert evidence.groupby(["dimension", "scenario"]).size().eq(7).all()
