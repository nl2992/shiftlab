from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/analyze_harm_power_grid.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("harm_power_grid_analysis", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_monotone_fraction_counts_conditioned_parameter_slices():
    data = pd.DataFrame(
        {
            "scenario": ["boundary_local_harm"] * 6,
            "monitor": ["fixed_mixture"] * 6,
            "scenario_severity": [0.75] * 3 + [1.5] * 3,
            "change_fraction": [0.5] * 6,
            "n": [2400, 3200, 4000] * 2,
            "detection_rate_all_material_harm": [0.2, 0.4, 0.6, 0.3, 0.2, 0.9],
        }
    )
    successes, total = MODULE._monotone_fraction(
        data,
        scenario="boundary_local_harm",
        monitor="fixed_mixture",
        factor="n",
        conditioning=["scenario_severity", "change_fraction"],
        order=[2400, 3200, 4000],
        direction="increasing",
    )
    assert (successes, total) == (1, 2)
