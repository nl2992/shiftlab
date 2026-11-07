"""Reproduce the frozen restarted E-SR slower-pacing screen summary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "research/scoped_method/pilots/srr_tail_pacing_20261106"
CANDIDATE = "E_srrSR:pace_k0.5:gated_deployment"
POLICIES = [
    CANDIDATE,
    "E_srrSR:gated_deployment",
    "PFA-SR:gated_deployment",
    "rmm:gated_deployment+RMM",
    "E_rb:gated_deployment",
    "E_swcert",
    "gated_adaptive_range+front",
    "qiu_delayed_movement",
    "gong_zhang_paid_obs",
    "CONTROL_never_switch",
]


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open()]


def wilson_upper(x: int, n: int, z: float = 1.6448536269514722) -> float:
    p = x / n
    den = 1 + z * z / n
    return ((p + z * z / (2 * n)) + z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / den


def paired_interval(
    left: dict[int, float], right: dict[int, float]
) -> tuple[float, float, float, int]:
    keys = sorted(left.keys() & right.keys())
    d = np.asarray([left[k] - right[k] for k in keys], dtype=float) * 0.5
    se = stats.sem(d)
    q = stats.t.ppf(0.975, len(d) - 1)
    return float(d.mean()), float(d.mean() - q * se), float(d.mean() + q * se), len(d)


def main() -> None:
    cal_path = BASE / "calibration_restart1/records.jsonl"
    null_path = BASE / "evaluation_null_restart1/records.jsonl"
    alt_path = BASE / "evaluation_alternatives_restart1/records.jsonl"
    calibration, null, alternatives = map(read_rows, (cal_path, null_path, alt_path))
    out = ["# Restarted E-SR slower-pacing screen results\n"]
    out.append("Candidate is an existing `k=0.5` acquisition configuration, not a new detector.\n")
    for label, rows, path in (
        ("Calibration null", calibration, cal_path),
        ("Independent evaluation null", null, null_path),
    ):
        x, n = sum(r["ever_promote"] for r in rows), len(rows)
        out.append(
            f"- {label}: {x}/{n} promotions ({x / n:.3%}); one-sided 95% Wilson upper "
            f"{wilson_upper(x, n):.4%}; mean labels {np.mean([r['labels'] for r in rows]):.2f}; "
            f"mean net cost {np.mean([r['net'] for r in rows]):.2f}; records SHA-256 "
            f"`{hashlib.sha256(path.read_bytes()).hexdigest()}`."
        )
    out.append("\n## Candidate cost decomposition by regime\n")
    out.append(
        "| Regime | Loss | Label expense | Switch expense | Net | Labels | Switches | Promoted | Rollbacks | Median promotion event |"
    )
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    regimes = sorted({r["regime"] for r in alternatives})
    for regime in regimes:
        rows = [r for r in alternatives if r["regime"] == regime and r["policy"] == CANDIDATE]
        promoted = [r["first_deploy"] for r in rows if r["first_deploy"] >= 0]
        out.append(
            f"| `{regime}` | {np.mean([r['loss'] for r in rows]):.2f} | "
            f"{0.05 * np.mean([r['labels'] for r in rows]):.2f} | "
            f"{5 * np.mean([r['switches'] for r in rows]):.2f} | "
            f"{np.mean([r['net'] for r in rows]):.2f} | "
            f"{np.mean([r['labels'] for r in rows]):.2f} | "
            f"{np.mean([r['switches'] for r in rows]):.2f} | "
            f"{sum(r['ever_promote'] for r in rows)}/{len(rows)} | "
            f"{np.mean([r['n_rollbacks'] for r in rows]):.2f} | "
            f"{np.median(promoted) if promoted else '—'} |"
        )
    out.append("\n## Paired net-cost contrasts\n")
    for regime in regimes:
        out.append(f"### `{regime}`\n")
        by_policy = {
            p: {
                r["seed"]: r["net"]
                for r in alternatives
                if r["regime"] == regime and r["policy"] == p
            }
            for p in POLICIES
        }
        comp_list = (
            POLICIES[1:]
            if regime == "F1_late_800"
            else ["E_srrSR:gated_deployment", "CONTROL_never_switch"]
        )
        out.append(
            f"\nPaired candidate-minus-comparator net-cost differences, per 1,000 events, `{regime}`:"
        )
        for comparator in comp_list:
            mean, low, high, n = paired_interval(by_policy[CANDIDATE], by_policy[comparator])
            out.append(f"- `{comparator}`: {mean:+.2f} [{low:+.2f}, {high:+.2f}], n={n}.")
        out.append("")
    out.append("## Interpretation and limitations\n")
    out.append(
        "The primary `F1_late_800` contrast to default E-SR is +1.69 per 1,000 "
        "[−0.51,+3.90], so the candidate does not clear its savings gate. It also fails the "
        "adverse-reversal cost gates: on `F3_reversal_800` its excess cost is +20.04/1,000 "
        "[+17.26,+22.82] versus never-switch; on `F3_reversal_1200` it is +15.02/1,000 "
        "[+12.90,+17.14]. The raw runner records promotion time and rollback count but not "
        "rollback event time. Qiu and Gong are common-contract ports without the same safety "
        "guarantees as certificate/restart baselines. This is synthetic development evidence only."
    )
    out.append(
        f"\nAlternative records SHA-256: `{hashlib.sha256(alt_path.read_bytes()).hexdigest()}`. "
        f"Manifest git revision: `{json.loads((BASE / 'evaluation_alternatives_restart1/manifest.json').read_text())['git']}`."
    )
    output = BASE / "RESTART1_RESULTS.md"
    output.write_text("\n".join(out) + "\n")
    print(output)


if __name__ == "__main__":
    main()
