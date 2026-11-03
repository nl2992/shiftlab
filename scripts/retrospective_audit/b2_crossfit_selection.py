"""Post hoc disjoint-half comparator selection diagnostic for archived B2 costs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/promising_directions/results/b2"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/B2_DISJOINT_SELECTION_DIAGNOSTIC.json"
POLICIES = ("P0", "P1", "P2", "P3b")
WORLDS = ("W1", "W2", "W3", "W4")


def run(source: Path = SOURCE) -> dict[str, object]:
    summary_path = source / "summary.json"
    raw_path = source / "per_seed.npz"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary["meta"]["seeds"] != 500:
        raise ValueError("unexpected B2 seed count")
    records = []
    with np.load(raw_path, allow_pickle=False) as raw:
        for setting, historical in summary["q1_settings"].items():
            budget, fee = setting.split("_")
            per_policy = {}
            for policy in POLICIES:
                arrays = [raw[f"{world}|{budget}|{fee}|{policy}|cost"] for world in WORLDS]
                if any(array.shape != (500,) for array in arrays):
                    raise ValueError(f"unexpected per-seed shape for {setting}/{policy}")
                per_policy[policy] = np.mean(arrays, axis=0)
            folds = []
            for train_start, eval_start in ((0, 250), (250, 0)):
                train = slice(train_start, train_start + 250)
                evaluation = slice(eval_start, eval_start + 250)
                train_costs = {
                    policy: float(per_policy[policy][train].mean()) for policy in POLICIES[:-1]
                }
                selected = min(train_costs, key=train_costs.get)
                runner_up = sorted(train_costs, key=train_costs.get)[1]
                differences = per_policy["P3b"][evaluation] - per_policy[selected][evaluation]
                reduction = (
                    1
                    - per_policy["P3b"][evaluation].mean() / per_policy[selected][evaluation].mean()
                )
                folds.append(
                    {
                        "selection_index_range": [train_start, train_start + 250],
                        "evaluation_index_range": [eval_start, eval_start + 250],
                        "selected_policy": selected,
                        "selection_margin_to_runner_up_cost_units": train_costs[runner_up]
                        - train_costs[selected],
                        "evaluation_mean_difference": float(differences.mean()),
                        "evaluation_relative_reduction_percent": float(100 * reduction),
                        "evaluation_wins_count": int((differences < 0).sum()),
                        "evaluation_ties_count": int((differences == 0).sum()),
                    }
                )
            historical_best = historical["best"]
            records.append(
                {
                    "setting": setting,
                    "historical_same_seed_best": historical_best,
                    "historical_same_seed_reduction_percent": float(
                        100 * historical["p3b_relative_reduction"]
                    ),
                    "folds": folds,
                    "crossfit_mean_difference": float(
                        np.mean([fold["evaluation_mean_difference"] for fold in folds])
                    ),
                }
            )
    return {
        "status": "POST_HOC_EXPOSED_DATA_DIAGNOSTIC_NOT_CONFIRMATION",
        "summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        "raw_npz_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "selection_rule": "For each setting, choose minimum average among P0/P1/P2 on 250 seed indices, then evaluate P3b versus it on the disjoint other 250; reverse halves.",
        "records": records,
        "limitations": "Both halves are historically exposed; the design and this split were chosen post hoc. The generator and P3b were informed by earlier research. This is a stability diagnostic, not a new validity, efficacy, or selection-adjusted population confidence claim.",
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("B2 four settings: disjoint-half comparator selection diagnostic complete")
