"""Smoke test for scripts/run_atlas_exact_cov_v1.py on one T=6 cell (small seed count)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "run_atlas_exact_cov_v1", ROOT / "scripts" / "run_atlas_exact_cov_v1.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_exact_cov_smoke_cell():
    m = _load()
    (cell,) = m.cell_list(smoke=True)
    assert cell["T"] == 6
    lp = m.lp_task(cell)
    assert "error" not in lp
    # Constraint removal: V_free <= V_valid (so CoV >= 0), V_valid <= never-switch cost.
    assert lp["V_free"] <= lp["V_valid"] + 1e-7
    assert lp["V_valid"] <= lp["continue_cost"] + 1e-7
    assert lp["valid_risk"] <= m.ALPHA + 1e-6
    seeds = tuple(range(210000, 210040))
    alt = m.merge_alt([m.mc_alt_task((cell, seeds))])
    null = m.mc_null_task(((cell["T"], cell["B"], cell["d"]), seeds))["fp"]
    exact = m.exact_null_task((cell["T"], cell["B"], cell["d"]))["exact"]
    row = m.summarise_cell(cell, lp, alt, null, exact)
    assert row["methods"]["no_switch"]["mc_null_risk"] == 0.0
    # An exact iid-boundary risk can never exceed the best-response causal risk.
    for rec in row["methods"].values():
        if rec["exact_null_causal"] is not None:
            assert rec["exact_null_iid"] <= rec["exact_null_causal"] + 1e-12
    assert row["best_safe"] in row["methods"]
    assert row["CoV"] >= -1e-7
