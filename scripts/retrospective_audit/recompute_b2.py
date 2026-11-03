"""Reconstruct B2 stored-seed cost effects without executing its simulator."""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = ROOT / "docs/promising_directions/results/b2"
    summary = json.loads((p / "summary.json").read_text(encoding="utf-8"))
    raw = np.load(p / "per_seed.npz", allow_pickle=False)
    n = summary["meta"]["seeds"]
    rng = np.random.default_rng(summary["meta"]["seed_base"] + 7)
    idx = rng.integers(0, n, size=(summary["meta"]["bootstrap_resamples"], n))
    records = []
    for setting, old in summary["q1_settings"].items():
        budget, fee = setting.split("_")
        worlds = {}
        for world in ("W1", "W2", "W3", "W4"):
            worlds[world] = {
                pol: raw[f"{world}|{budget}|{fee}|{pol}|cost"] for pol in old["world_avg_cost"]
            }
        avg = {
            pol: np.mean([v[pol] for v in worlds.values()], axis=0) for pol in old["world_avg_cost"]
        }
        best = min(("P0", "P1", "P2"), key=lambda pol: avg[pol].mean())
        delta = avg["P3b"] - avg[best]
        ci = np.percentile(delta[idx].mean(axis=1), [2.5, 97.5])
        reduction = 1 - avg["P3b"].mean() / avg[best].mean()
        mismatches = []
        for pol, a in avg.items():
            if abs(a.mean() - old["world_avg_cost"][pol]) > 1e-9:
                mismatches.append("mean " + pol)
        for key, value in zip(("mean", "lo", "hi"), (delta.mean(), ci[0], ci[1]), strict=True):
            if abs(value - old["p3b_minus_best"][key]) > 1e-9:
                mismatches.append("CI " + key)
        if best != old["best"] or abs(reduction - old["p3b_relative_reduction"]) > 1e-9:
            mismatches.append("selection/effect")
        records.append(
            {
                "setting": setting,
                "selected_comparator": best,
                "relative_reduction": float(reduction),
                "paired_difference": float(delta.mean()),
                "lo": float(ci[0]),
                "hi": float(ci[1]),
                "world_policy_means": {
                    w: {pol: float(a.mean()) for pol, a in v.items()} for w, v in worlds.items()
                },
                "mismatches": mismatches,
            }
        )
    result = {
        "scope": "Historical stored-seed arithmetic and original bootstrap; four worlds equally weighted; BEST selected on evaluation seeds; no selection-adjusted or population CI claimed",
        "records": records,
        "registered_outcome_preserved": summary["decisions"]["Q1"],
    }
    (ROOT / "docs/retrospective_audit_2026_11_01/B2_RECOMPUTATION.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "settings": len(records),
                "mismatches": sum(len(x["mismatches"]) for x in records),
                "reductions": [x["relative_reduction"] for x in records],
            }
        )
    )


if __name__ == "__main__":
    main()
