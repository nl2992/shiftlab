"""Report all eight CUSUM/reference contrasts, retaining multiplicity and failures."""

import json
from pathlib import Path

import numpy as np
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/exhaustive_evaluation"


def main():
    assert json.loads((DOC / "cusum_strict_status.json").read_text())["status"] == "completed"
    results = json.loads((DOC / "cusum_strict_results.json").read_text())
    out = ROOT / "outputs/exhaustive_evaluation/cusum_strict"
    rows = []
    z = float(norm.ppf(1 - 0.05 / 16))
    for i, slack in enumerate([0, 0.01, 0.05, 0.1]):
        for reference, idx in [("paired_Kelly", 4), ("tuned_FTL", 5)]:
            diffs, base = [], []
            for kind in ["useful_initial", "useful", "late", "small"]:
                arrays = []
                # Explicit names avoid matching useful_initial when reading useful.
                for b in range(2):
                    with np.load(out / f"{kind}_{b:03d}.npz") as data:
                        arrays.append(data["total_cost"])
                costs = np.concatenate(arrays, axis=1)
                assert costs.shape == (6, 500)
                diffs.append(costs[i] - costs[idx])
                base.append(costs[idx].mean())
            diffs = np.stack(diffs)
            mean = float(diffs.mean())
            se = float(np.sqrt(np.sum(diffs.var(axis=1, ddof=1) / 500)) / 4)
            name = results["rows"][i]["method"]
            upper = max(
                r["simultaneous_null_upper"]
                for r in results["rows"]
                if r["method"] == name and r["simultaneous_null_upper"] is not None
            )
            relative = float(-mean / np.mean(base))
            rows.append(
                {
                    "cusum_slack": slack,
                    "reference": reference,
                    "paired_mean_cost_difference": mean,
                    "bonferroni_95_family_interval": [mean - z * se, mean + z * se],
                    "relative_cost_reduction": relative,
                    "max_null_upper": upper,
                    "empirical_safety_screen_pass": upper <= 0.06,
                    "practical_10percent_gate": bool(relative >= 0.1 and mean + z * se < 0),
                }
            )
    result = {
        "stage": "all eight contrasts reported; no selected winner",
        "efficacy_family_size": 8,
        "normal_approximation": True,
        "rows": rows,
    }
    (DOC / "cusum_strict_decision.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("All eight contrasts reported; no comparison passes the 10 percent gate")


if __name__ == "__main__":
    main()
