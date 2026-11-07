"""Bounded post-cycle-7 development diagnostic; leaves frozen candidate unchanged."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import numpy as np
from run_atlas_cycle7_validation_v1 import make_method
from run_atlas_dss_tuning_v1 import build_cell

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa
from shiftlab.dive.switching_explore import paired_ci, wilson


class FallbackGapDiagnostic(comp.ComposedMethod):
    def _query(self, t):
        if self.dss_uniform and self.used and t - self.last_query < 4:
            return False
        return super()._query(t)


def main():
    out = ROOT / "outputs/failure_atlas_v1_cycle7/fallback_diagnostic"
    out.mkdir(parents=True, exist_ok=True)
    cells = [
        fa.Family3CellSpec(0.8, 0.3, 0.6, "strong", "harmful", 10, 0.25).null_twin(),
        fa.Family3CellSpec(0.5, 0.3, 0.6, "strong", "harmful", 10, 0.5).null_twin(),
        build_cell("on0.6_L1_strong_harmful_d50_b0.05_s0.1"),
        build_cell("f3_rho0_on0.3_L0.6_strong_harmful_d1_b0.1_s0.1"),
    ]
    methods = ("dss", "no_delay_switch", "fallback_gap4_diagnostic", "episode_front")
    manifest = {
        "seeds": [181000, 181040],
        "cells": [c.cell_id for c in cells],
        "methods": methods,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(
            (ROOT / "docs/failure_atlas_cycle7_followup_diagnostic_v1.md").read_bytes()
        ).hexdigest(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    records = []
    lines = [
        "",
        "## Completed development diagnostic",
        "",
        "40 paired development seeds [181000,181040), no new validation. Gap is measured on actual requested rounds.",
        "",
        "| cell | method | cost/round | false promotion [Wilson 95%] | minimum observed query gap | paired cost minus DSS [95% CI] |",
        "|---|---|---|---|---|---|",
    ]
    for cell in cells:
        values = {m: [] for m in methods}
        for seed in range(181000, 181040):
            stream, cfg = fa.make_stream(cell, seed), cell.config(seed)
            for name in methods:
                method = (
                    FallbackGapDiagnostic(comp.dss_spec(4, True))
                    if name == "fallback_gap4_diagnostic"
                    else make_method(name, cfg)
                )
                result = fa.run_for(cell, stream, method, cfg)
                gaps = np.diff(np.flatnonzero(result.query_mask))
                values[name].append(
                    {
                        "seed": seed,
                        "cost": float(result.cost) / cell.T,
                        "fp": int((result.fp_regime or 0) > 0),
                        "correct": int(result.promotions > (result.fp_regime or 0)),
                        "min_gap": int(gaps.min()) if len(gaps) else None,
                        "queries": result.queries,
                    }
                )
        records.append({"cell": cell.cell_id, "values": values})
        for name, rs in values.items():
            fp = sum(r["fp"] for r in rs)
            interval = wilson(fp, 40)
            delta = paired_ci(
                np.array([r["cost"] for r in rs]) - np.array([r["cost"] for r in values["dss"]])
            )
            gap = min((r["min_gap"] for r in rs if r["min_gap"] is not None), default=None)
            lines.append(
                f"| {cell.cell_id} | {name} | {np.mean([r['cost'] for r in rs]):.5f} | {fp}/40 [{interval[1]:.3f},{interval[2]:.3f}] | {gap} | {delta[0]:+.5f} [{delta[1]:+.5f},{delta[2]:+.5f}] |"
            )
        print(cell.cell_id, flush=True)
    (out / "records.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
