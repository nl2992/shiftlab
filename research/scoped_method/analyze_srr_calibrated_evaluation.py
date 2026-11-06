"""Summarize the frozen E-SR threshold evaluation from paired screen outputs."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, stdev

from scipy.stats import t

ROOT = Path(__file__).resolve().parent / "pilots/srr_any_false_calibration_20261106"
CANDIDATE = "E_srrSR:gated_deployment"
REFERENCES = ("E_swcert", "CONTROL_never_switch")


def read_rows(directory: str) -> list[dict]:
    with (ROOT / directory / "records.jsonl").open() as stream:
        return [json.loads(line) for line in stream]


def wilson_upper(successes: int, trials: int, confidence: float = 0.95) -> float:
    from scipy.stats import norm

    z = float(norm.ppf(confidence))
    rate = successes / trials
    denominator = 1.0 + z * z / trials
    center = (rate + z * z / (2.0 * trials)) / denominator
    half = z * math.sqrt((rate * (1.0 - rate) + z * z / (4.0 * trials)) / trials) / denominator
    return center + half


def summary(rows: list[dict]) -> dict:
    n = len(rows)
    return {
        "n": n,
        "net": mean(row["net"] for row in rows),
        "loss": mean(row["loss"] for row in rows),
        "labels": mean(row["labels"] for row in rows),
        "switches": mean(row["switches"] for row in rows),
        "promotion_episodes": sum(row["ever_promote"] for row in rows),
        "mean_first_promotion": mean(
            row["first_deploy"] for row in rows if row["first_deploy"] >= 0
        )
        if any(row["first_deploy"] >= 0 for row in rows)
        else None,
        "mean_rollbacks": mean(row["n_rollbacks"] for row in rows),
    }


def paired_difference(left: list[dict], right: list[dict], metric: str = "net") -> dict:
    a = {(row["regime"], row["seed"]): row for row in left}
    b = {(row["regime"], row["seed"]): row for row in right}
    keys = sorted(a.keys() & b.keys())
    if len(keys) != len(a) or len(keys) != len(b):
        raise ValueError("paired streams do not match exactly")
    deltas = [a[key][metric] - b[key][metric] for key in keys]
    n = len(deltas)
    half = float(t.ppf(0.975, n - 1)) * stdev(deltas) / math.sqrt(n)
    average = mean(deltas)
    return {"n": n, "mean": average, "ci95": [average - half, average + half]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "evaluation_summary.json")
    args = parser.parse_args()

    null_candidate = read_rows("evaluation_candidate_null")
    null_refs = read_rows("evaluation_reference_null")
    cand_alt = read_rows("evaluation_candidate_reversals")
    ref_alt = read_rows("evaluation_reference_reversals")
    policies = {
        "null_candidate": [row for row in null_candidate if row["policy"] == CANDIDATE],
        "null_E_swcert": [row for row in null_refs if row["policy"] == "E_swcert"],
        "null_never_switch": [row for row in null_refs if row["policy"] == "CONTROL_never_switch"],
    }
    candidate_null = policies["null_candidate"]
    false_promotions = sum(row["ever_promote"] for row in candidate_null)
    result = {
        "selected_alpha": 0.0005,
        "evaluation_seed_base": 7110601102,
        "null": {
            "n": len(candidate_null),
            "false_promotion_episodes": false_promotions,
            "rate": false_promotions / len(candidate_null),
            "one_sided_95_wilson_upper": wilson_upper(false_promotions, len(candidate_null)),
            "candidate_costs": summary(candidate_null),
            "E_swcert_costs": summary(policies["null_E_swcert"]),
            "never_switch_costs": summary(policies["null_never_switch"]),
        },
        "reversals": {},
    }
    for regime in ("F3_reversal_1200", "F3_reversal_800"):
        candidates = [
            row for row in cand_alt if row["policy"] == CANDIDATE and row["regime"] == regime
        ]
        references = {
            name: [row for row in ref_alt if row["policy"] == name and row["regime"] == regime]
            for name in REFERENCES
        }
        result["reversals"][regime] = {
            "candidate_costs": summary(candidates),
            "reference_costs": {name: summary(rows) for name, rows in references.items()},
            "candidate_minus_reference_net": {
                name: paired_difference(candidates, rows) for name, rows in references.items()
            },
            "candidate_minus_reference_loss": {
                name: paired_difference(candidates, rows, "loss")
                for name, rows in references.items()
            },
            "candidate_minus_reference_labels": {
                name: paired_difference(candidates, rows, "labels")
                for name, rows in references.items()
            },
            "candidate_minus_reference_switches": {
                name: paired_difference(candidates, rows, "switches")
                for name, rows in references.items()
            },
        }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(args.out)


if __name__ == "__main__":
    main()
