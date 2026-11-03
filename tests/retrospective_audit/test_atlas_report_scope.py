"""Report limitations must agree with the comparators actually loaded for a run."""

import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("has_pacing", [False, True])
@pytest.mark.parametrize("recorded_pacing", [None, False, True])
def test_summary_pacing_availability(tmp_path, monkeypatch, has_pacing, recorded_pacing):
    script = runpy.run_path(str(ROOT / "scripts/run_failure_atlas_loop.py"))
    methods = {"online_fwer_spending": (None, True, "fixture")}
    if has_pacing:
        methods["hard_budget_pacing"] = (None, False, "fixture")
    monkeypatch.setattr(script["fa"], "r6_methods", lambda: methods)
    monkeypatch.setattr(script["fa"], "r6_status", lambda: "fixture status")
    runner = script["Runner"](SimpleNamespace(smoke=True, out=str(tmp_path)), None)
    runner.state["registry"] = []
    if recorded_pacing is not None:
        runner.state["methods"] = (
            ["hard_budget_pacing"] if recorded_pacing else ["online_fwer_spending"]
        )
    runner.state["r6_status"] = "R6 baselines loaded: " + ", ".join(methods)
    runner.summary()
    text = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert ("hard-budget pacing comparator is still missing" in text) == (
        not (has_pacing if recorded_pacing is None else recorded_pacing)
    )
