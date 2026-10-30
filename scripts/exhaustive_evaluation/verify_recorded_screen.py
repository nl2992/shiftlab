"""Verify current post-lint implementation against every stored per-path result."""

import hashlib
import json
from pathlib import Path

import numpy as np

from shiftlab.sota_search.combination_screen import combinations, make_world, screen

ROOT = Path(__file__).resolve().parents[2]


def main():
    doc = ROOT / "docs/exhaustive_evaluation"
    out = ROOT / "outputs/exhaustive_evaluation/round1_corrected"
    reg = json.loads((doc / "round1_corrected_registration.json").read_text())
    checked = []
    for i, (kind, delay) in enumerate(reg["cases"]):
        stream = make_world(
            kind, paths=reg["paths"], horizon=reg["horizon"], seed=reg["world_seed_base"] + i
        )
        result = screen(
            stream,
            combinations(),
            frac=reg["frac"],
            budget=reg["budget"],
            delay=delay,
            seed=reg["query_seed_base"] + i,
        )
        name = f"{i:02d}_{kind}_d{delay}"
        with np.load(out / (name + ".npz")) as original:
            for key in result:
                np.testing.assert_array_equal(result[key], original[key])
        checked.append(name)
        print(name, "all per-path arrays identical", flush=True)
    value = {
        "status": "all_recorded_arrays_identical",
        "cases": checked,
        "distinct_configs": len(combinations()),
        "current_engine_sha256": hashlib.sha256(
            (ROOT / "src/shiftlab/sota_search/combination_screen.py").read_bytes()
        ).hexdigest(),
        "original_engine_sha256": reg["engine_sha256"],
        "scope": "post-lint replay, same seeds; not independent confirmation",
    }
    (doc / "post_lint_replay_verification.json").write_text(
        json.dumps(value, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
