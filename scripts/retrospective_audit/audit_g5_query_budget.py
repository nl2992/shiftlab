"""Reconstruct G5 Bernoulli query counts from frozen runner seed mapping."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from shiftlab.sota_search import generators as g

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "H2C_G5_QUERY_COUNTS.json"


def run() -> dict[str, object]:
    cells = []
    for k, (cond, shift) in enumerate((c, s) for c in g.G5_CONDITIONS for s in g.G5_SHIFTS):
        seed = 95000 + k + 1  # runner increments k before invoking each arm
        uniforms = np.random.default_rng(seed).random((600, 2000))
        for frac in (0.1, 0.2):
            counts = (uniforms < frac).sum(axis=1)
            expected = round(frac * 2000)
            cells.append(
                {
                    "condition": cond,
                    "shift": shift,
                    "frac": frac,
                    "label_seed": seed,
                    "min_queries": int(counts.min()),
                    "max_queries": int(counts.max()),
                    "mean_queries": float(counts.mean()),
                    "paths_above_expected_count": int((counts > expected).sum()),
                    "paths": len(counts),
                }
            )
    summary = {}
    for frac in (0.1, 0.2):
        subset = [r for r in cells if r["frac"] == frac]
        summary[str(frac)] = {
            "cells": len(subset),
            "paths": sum(r["paths"] for r in subset),
            "paths_above_expected_count": sum(r["paths_above_expected_count"] for r in subset),
            "min_queries": min(r["min_queries"] for r in subset),
            "max_queries": max(r["max_queries"] for r in subset),
            "mean_queries": float(np.mean([r["mean_queries"] for r in subset])),
        }
    return {
        "method": "np.random.default_rng(95000+k_after_increment).random((600,2000)) < frac",
        "scope": "Exact runner label-mask reconstruction; no detector or path replay",
        "summary": summary,
        "cells": cells,
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["summary"])
