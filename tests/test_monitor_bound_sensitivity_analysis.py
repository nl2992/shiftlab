from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/analyze_monitor_bound_sensitivity.py"
SPEC = importlib.util.spec_from_file_location("monitor_bound_sensitivity", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _metrics(detected: bool, *, spend: float = 2.0) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "scenario": ["boundary_local_harm"],
            "seed": [1],
            "method": ["uniform_proxy"],
            "labels_queried": [4],
            "realized_label_spend": [spend],
            "processed_events": [10],
            "budget_remaining": [1.0],
            "budget_respected": [True],
            "material_harm": [True],
            "single_e_detected": [detected],
            "single_e_false_escalation": [False],
            "single_e_delay": [7 if detected else float("nan")],
            "variance_adaptive_detected": [detected],
            "variance_adaptive_false_escalation": [False],
            "variance_adaptive_delay": [7 if detected else float("nan")],
            "pm_eb_detected": [False],
            "pm_eb_false_escalation": [False],
            "pm_eb_delay": [float("nan")],
        }
    )


def test_analysis_reports_paired_detection_change_and_delay() -> None:
    result = MODULE.analyze(_metrics(False), _metrics(True)).set_index("monitor")
    fixed = result.loc["fixed_mixture"]
    assert fixed.qmin_005_detections == 0
    assert fixed.qmin_020_detections == 1
    assert fixed.qmin_020_median_delay == 7
    assert fixed.paired_wins_qmin020 == 1
    assert fixed.paired_losses_qmin020 == 0
    assert fixed.mcnemar_exact_p == pytest.approx(1.0)


def test_analysis_rejects_changed_query_process() -> None:
    with pytest.raises(ValueError, match="realized_label_spend"):
        MODULE.analyze(_metrics(False), _metrics(True, spend=2.1))
