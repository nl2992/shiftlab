#!/usr/bin/env python3
"""Verify that Sprint 2's SUI likelihood-factor floors cannot bind at T=2000.

This is an analytic bound over the implemented parameter grids and event gaps >= 1,
not an instrumented scan of every historical policy trajectory. The Markov-null
factors are cellwise upper bounds and the alternative factors are positive mixture
components; bounding each per-event log factor bounds every cumulative array entry.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from fam_a import LOG0, MarkovSUI

ROOT = Path(__file__).resolve().parents[2]


def _collect_horizons(value: Any, out: set[int]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in {"t", "horizon", "horizon_events"} and isinstance(
                child, (int, float)
            ):
                out.add(int(child))
            _collect_horizons(child, out)
    elif isinstance(value, list):
        for child in value:
            _collect_horizons(child, out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="docs/sprint2/sui_clamp_bound.json")
    args = parser.parse_args()

    manifest_paths = sorted((ROOT / "outputs/sprint2").rglob("manifest.json"))
    horizons: set[int] = set()
    manifests_with_horizon = 0
    for path in manifest_paths:
        try:
            manifest = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        local: set[int] = set()
        _collect_horizons(manifest, local)
        if local:
            manifests_with_horizon += 1
            horizons.update(local)
    if not manifest_paths or not manifests_with_horizon or horizons != {2000}:
        raise SystemExit(
            f"Expected every Sprint 2 manifest horizon to be 2000; found {sorted(horizons)} "
            f"across {manifests_with_horizon}/{len(manifest_paths)} manifests"
        )

    process = MarkovSUI()
    null_min_by_case = {}
    alt_min_by_case = {}
    for prev in (None, 0, 1):
        for hit in (0, 1):
            label = f"prev={prev},hit={hit}"
            null_logs = process._null_factor(hit, 1, prev)
            alt_logs = process._alt_factor(hit, 1, prev)
            null_min_by_case[label] = float(np.min(null_logs))
            alt_min_by_case[label] = float(np.min(alt_logs))

    null_step_lower = min(null_min_by_case.values())
    alt_step_lower = min(alt_min_by_case.values())
    horizon = max(horizons)
    null_cumulative_lower = horizon * null_step_lower
    alt_cumulative_lower = horizon * alt_step_lower
    if null_cumulative_lower <= LOG0 or alt_cumulative_lower <= LOG0:
        raise SystemExit("The conservative cumulative bound reaches the configured floor")

    result = {
        "scope": "Sprint 2 saved runs with T=2000; MarkovSUI and subclasses using its factor definitions",
        "manifest_count": len(manifest_paths),
        "manifests_with_horizon": manifests_with_horizon,
        "horizons": sorted(horizons),
        "event_gap_scope": "integer gaps >= 1; one-step minima occur at gap 1 by factor monotonicity",
        "null_min_log_factor_by_case_at_gap_1": null_min_by_case,
        "alternative_min_log_factor_by_case_at_gap_1": alt_min_by_case,
        "null_per_step_lower_bound": null_step_lower,
        "alternative_per_step_lower_bound": alt_step_lower,
        "null_log_cumulative_lower_bound_at_T": null_cumulative_lower,
        "alternative_log_cumulative_lower_bound_at_T": alt_cumulative_lower,
        "log_floor": LOG0,
        "null_floor_can_bind": False,
        "alternative_floor_can_bind": False,
        "method": "For each factor case, the worst gap is gap=1 (or the limiting independent-event probability); multiply the minimum factor log by T. Factors are positive on the implemented grids. Since each resulting lower bound exceeds LOG0, no per-cell cumulative value reaches the floor.",
        "limitation": "This verifies the arithmetic bound from code and saved manifests; it does not instrument each historical run or establish the statistical validity assumptions.",
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
