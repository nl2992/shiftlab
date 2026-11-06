"""Summarize paired development-only rollback/acquisition pilot screen records."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t


METRICS = (
    "net", "loss", "labels", "switches", "ever_promote", "first_deploy",
    "n_promotions", "n_rollbacks", "frac_on_wrong", "detect_delay",
    "labels_by_500", "labels_after_1000", "exhaust_t",
)
POLICIES = (
    "E_rb:gated_deployment", "E_rb:gated_deployment-a05", "E_srr:gated_deployment",
    "E_srrSR:gated_deployment", "E_srr_noacq:gated_deployment", "B0_host", "B2", "B5",
    "gated_deployment", "CONTROL_never_switch",
)
CONTRASTS = (
    ("E_rb:gated_deployment", "E_rb:gated_deployment-a05"),
    ("E_rb:gated_deployment", "E_srr:gated_deployment"),
    ("E_rb:gated_deployment", "E_srrSR:gated_deployment"),
    ("E_rb:gated_deployment", "E_srr_noacq:gated_deployment"),
    ("E_rb:gated_deployment", "B0_host"),
    ("E_rb:gated_deployment", "B5"),
    ("E_rb:gated_deployment", "gated_deployment"),
    ("E_rb:gated_deployment", "CONTROL_never_switch"),
)


def mean_ci(xs: np.ndarray) -> tuple[float, float, float]:
    xs = np.asarray(xs, dtype=float)
    m = float(xs.mean())
    if xs.size < 2:
        return m, float("nan"), float("nan")
    half = float(student_t.ppf(0.975, xs.size - 1) * xs.std(ddof=1) / np.sqrt(xs.size))
    return m, m - half, m + half


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("records", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    raw = args.records.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line]
    keys = {(r["regime"], int(r["seed"]), r["policy"]): r for r in rows}
    regimes = sorted({r["regime"] for r in rows})
    seeds = sorted({int(r["seed"]) for r in rows})
    summary: dict[str, object] = {
        "records_sha256": hashlib.sha256(raw).hexdigest(),
        "record_count": len(rows),
        "regimes": regimes,
        "seed_count_per_regime": len(seeds),
        "policies": {},
        "paired_net_contrasts_candidate_minus_comparator": {},
        "exactly_equal_B2_and_E_rb_on_common_seed_regime": True,
    }
    policy_table: dict[str, dict[str, dict[str, float]]] = {}
    for policy in POLICIES:
        policy_table[policy] = {}
        for regime in regimes:
            rs = [keys[(regime, seed, policy)] for seed in seeds]
            policy_table[policy][regime] = {
                metric: float(np.mean([r[metric] for r in rs])) for metric in METRICS
            }
        summary["policies"][policy] = policy_table[policy]
    for regime in regimes:
        for seed in seeds:
            a = keys[(regime, seed, "E_rb:gated_deployment")]
            b = keys[(regime, seed, "B2")]
            if any(a[k] != b[k] for k in METRICS):
                summary["exactly_equal_B2_and_E_rb_on_common_seed_regime"] = False
    for candidate, comparator in CONTRASTS:
        entry: dict[str, object] = {}
        for regime in regimes:
            diffs = np.array([
                keys[(regime, seed, candidate)]["net"]
                - keys[(regime, seed, comparator)]["net"]
                for seed in seeds
            ])
            m, lo, hi = mean_ci(diffs)
            entry[regime] = {"mean_delta_net": m, "ci95_low": lo, "ci95_high": hi,
                             "paired_n": int(diffs.size)}
        summary["paired_net_contrasts_candidate_minus_comparator"][
            f"{candidate} - {comparator}"
        ] = entry
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"out": str(args.out), "records_sha256": summary["records_sha256"],
                      "record_count": len(rows), "regimes": regimes,
                      "exactly_equal_B2_and_E_rb_on_common_seed_regime":
                          summary["exactly_equal_B2_and_E_rb_on_common_seed_regime"]}, indent=2))


if __name__ == "__main__":
    main()
