"""Replay an exposed batch to locate spend relative to evaluator-only onset."""

import json
from pathlib import Path

import numpy as np

from shiftlab.sota_search.learned_paired_rcps import learned_paired_rcps
from shiftlab.sota_search.paired_control import paired_world

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    reg = json.loads((DOC / "learned_rcps_development_registration.json").read_text())
    stream = paired_world("late", paths=128, horizon=2000, seed=202654500)
    rows = []
    path = ROOT / "outputs/exhaustive_evaluation/learned_rcps_development/late_000.npz"
    with np.load(path) as original:
        for i in [0, 3, 5]:
            variant = reg["variants"][i]
            result = learned_paired_rcps(
                stream,
                seed=202655500,
                return_trace=True,
                **{k: v for k, v in variant.items() if k != "id"},
            )
            for key in ["first", "labels", "total_cost", "delta_vs_incumbent"]:
                np.testing.assert_array_equal(result[key], original[key][i])
            query = result["trace"]["query"]
            cumulative = query.cumsum(1)
            rows.append(
                {
                    "method": variant["id"],
                    "paths": 128,
                    "same_first_batch_reproduced": True,
                    "mean_labels": float(query.sum(1).mean()),
                    "mean_labels_issued_at_or_after_onset1500": float(
                        query[:, 1500:].sum(1).mean()
                    ),
                    "fraction_budget_exhausted_before_onset": float(
                        (cumulative[:, 1499] >= 400).mean()
                    ),
                    "promotion_rate": float((result["first"] < 2000).mean()),
                    "max_logwealth": float(result["trace"]["logwealth"].max()),
                }
            )
    diagnostic = {
        "stage": "post-hoc causal timing diagnostic on existing development batch, not fresh confirmation",
        "rows": rows,
    }
    output = DOC / "learned_rcps_late_timing_diagnostic.json"
    if output.exists():
        assert json.loads(output.read_text()) == diagnostic, "do not overwrite a changed diagnostic"
    else:
        output.write_text(json.dumps(diagnostic, indent=2), encoding="utf-8")
    print("All three exact-batch timing replays match retained diagnostic")


if __name__ == "__main__":
    main()
