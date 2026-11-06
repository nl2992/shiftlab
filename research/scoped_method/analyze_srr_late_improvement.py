"""Analyze the frozen calibrated-SR late-improvement development screen."""

from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean, stdev

from scipy.stats import norm, t

ROOT = Path(__file__).resolve().parent / "pilots/srr_late_improvement_20261106"
CANDIDATE = "E_srrSR:gated_deployment"


def read(directory: str) -> list[dict]:
    with (ROOT / directory / "records.jsonl").open() as stream:
        return [json.loads(line) for line in stream]


def summary(rows: list[dict]) -> dict:
    times = [row["first_deploy"] for row in rows if row["first_deploy"] >= 0]
    return {
        "n": len(rows),
        "net": mean(row["net"] for row in rows),
        "loss": mean(row["loss"] for row in rows),
        "labels": mean(row["labels"] for row in rows),
        "switches": mean(row["switches"] for row in rows),
        "promotion_episodes": sum(row["ever_promote"] for row in rows),
        "mean_first_promotion": mean(times) if times else None,
        "mean_rollbacks": mean(row["n_rollbacks"] for row in rows),
    }


def paired(candidate: list[dict], reference: list[dict]) -> dict:
    left = {(row["regime"], row["seed"]): row for row in candidate}
    right = {(row["regime"], row["seed"]): row for row in reference}
    keys = sorted(left.keys() & right.keys())
    if len(keys) != len(left) or len(keys) != len(right):
        raise ValueError("candidate and reference do not have identical paired streams")
    deltas = [left[key]["net"] - right[key]["net"] for key in keys]
    center = mean(deltas)
    half = float(t.ppf(0.975, len(deltas) - 1)) * stdev(deltas) / math.sqrt(len(deltas))
    return {"n": len(deltas), "mean": center, "ci95": [center - half, center + half]}


def main() -> None:
    candidate = read("candidate")
    references = read("references")
    result: dict = {
        "candidate": CANDIDATE,
        "alpha": 0.0005,
        "seed_base": 7110601103,
        "regimes": {},
    }
    for regime in ("F1_late_800", "F1_late_1200", "F0_null", "F0_better", "F3_reversal_800"):
        cand_rows = [row for row in candidate if row["regime"] == regime]
        ref_groups = {
            name: [row for row in references if row["regime"] == regime and row["policy"] == name]
            for name in sorted({row["policy"] for row in references})
        }
        result["regimes"][regime] = {
            "candidate": summary(cand_rows),
            "references": {name: summary(rows) for name, rows in ref_groups.items()},
            "candidate_minus_reference_net": {
                name: paired(cand_rows, rows) for name, rows in ref_groups.items()
            },
        }
        if regime == "F0_null":
            k, n = result["regimes"][regime]["candidate"]["promotion_episodes"], len(cand_rows)
            upper = float(norm.ppf(0.95))
            p = k / n
            den = 1.0 + upper * upper / n
            center = (p + upper * upper / (2.0 * n)) / den
            half = upper * math.sqrt((p * (1.0 - p) + upper * upper / (4.0 * n)) / n) / den
            result["regimes"][regime]["one_sided_95_wilson_upper"] = center + half
    out = ROOT / "evaluation_summary.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(out)


if __name__ == "__main__":
    main()
