from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_harm_power_grid.py"
SPEC = importlib.util.spec_from_file_location("harm_power_grid", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_grid_contains_36_cells_and_only_abrupt_scenarios_vary_onset():
    cells = list(MODULE._cell_configs())
    assert len(cells) == 36
    boundary = [cell for cell in cells if cell[0] == "boundary_local_harm"]
    recurring = [cell for cell in cells if cell[0] == "recurring_regimes"]
    assert len(boundary) == 27
    assert len(recurring) == 9
    assert {cell[3] for cell in boundary} == set(MODULE.ONSET_FRACTIONS)
    assert {cell[3] for cell in recurring} == {0.5}


def test_grid_summary_keeps_unreached_harm_in_primary_denominator():
    rows = []
    for seed, reached, fixed_detected in [(1, True, True), (2, False, False)]:
        rows.append(
            {
                "scenario": "boundary_local_harm",
                "n": 2400,
                "scenario_severity": 0.75,
                "change_fraction": 0.35,
                "seed": seed,
                "material_harm": True,
                "harm_reached_before_budget_stop": reached,
                "single_e_detected": fixed_detected,
                "single_e_delay": 5 if fixed_detected else None,
                "variance_adaptive_detected": False,
                "variance_adaptive_delay": None,
                "pm_eb_detected": False,
                "pm_eb_delay": None,
                "realized_label_spend": 10.0,
                "hard_budget": 12.0,
                "labels_queried": 5,
                "processed_events": 20,
                "monitor_fraction_processed": 0.5,
                "budget_respected": True,
            }
        )
    summary, paired = MODULE._summarize(pd.DataFrame(rows))
    fixed = summary.loc[summary.monitor.eq("fixed_mixture")].iloc[0]
    assert fixed.material_harm_streams == 2
    assert fixed.harm_onsets_reached == 1
    assert fixed.harm_detections == 1
    assert fixed.detection_rate_all_material_harm == 0.5
    assert fixed.detection_rate_reached_harm == 1.0
    assert len(paired) == 2
