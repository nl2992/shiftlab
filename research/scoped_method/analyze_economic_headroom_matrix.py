"""Analyze the frozen economic-headroom development matrix."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from scipy.stats import t

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "research/scoped_method/pilots/economic_headroom_matrix_20261106/run"
RAW = RUN / "records.jsonl"
CELLS = [
    "F0_better",
    "F3_reversal_1200",
    "F3_reversal_800",
    "F0_null",
    "F6_delay400_better@B100",
]
POLICIES = [
    "CONTROL_never_switch",
    "gated_adaptive_range",
    "discern_style",
    "xu_acquisition_only",
    "E_rb:gated_adaptive_range",
    "rmm:gated_adaptive_range+RMM",
    "E_swcert",
    "economic_replacement",
    "E_srrSR:gated_deployment",
]
REFERENCES = {
    "F0_better": "xu_acquisition_only",
    "F3_reversal_1200": "CONTROL_never_switch",
    "F3_reversal_800": "CONTROL_never_switch",
    "F0_null": "CONTROL_never_switch",
    "F6_delay400_better@B100": "xu_acquisition_only",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def mean_ci(xs: list[float]) -> tuple[float, float, float]:
    mean = statistics.mean(xs)
    if len(xs) < 2:
        return mean, mean, mean
    half = t.ppf(0.975, len(xs) - 1) * statistics.stdev(xs) / math.sqrt(len(xs))
    return mean, mean - half, mean + half


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    phat = k / n
    den = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / den
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / den
    return center - half, center + half


def main() -> None:
    paired: dict[tuple[str, int], dict[str, dict]] = defaultdict(dict)
    for line in RAW.open():
        row = json.loads(line)
        paired[(row["regime"], row["seed"])][row["policy"]] = row

    cells: dict[str, dict] = {}
    lines = [
        "# Economic headroom matrix — development results",
        "",
        "**Status:** exploratory development pilot, not confirmation. Protocol was committed as",
        "`89e5d060` before the run. Thirty matched synthetic streams per cell; 1,350 policy rows.",
        "",
        "Net cost is predictive loss + 0.05 × requested labels + 5 × deployment switches.",
        "Intervals are two-sided paired t intervals over 30 shared streams. The prespecified primary",
        "contrasts and decision rule are in `protocol.md`; no multiplicity correction is applied to",
        "these screening intervals.",
        "",
        "## Primary frozen contrasts",
        "",
        "| Cell | Policy | Reference | Policy net cost | Paired difference [95% CI] | Loss | Labels | Switches | Promote | Mean first promotion | Mean rollbacks |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    identity_max = 0.0
    for cell in CELLS:
        streams = [v for (c, _), v in paired.items() if c == cell]
        ref = REFERENCES[cell]
        policy_records: dict[str, dict] = {}
        cell_result = {"reference": ref, "policies": policy_records}
        for policy in POLICIES:
            rows = [s[policy] for s in streams]
            costs = [r["net"] for r in rows]
            diffs = [r["net"] - s[ref]["net"] for r, s in zip(rows, streams, strict=True)]
            cost_mean, cost_lo, cost_hi = mean_ci(costs)
            diff_mean, diff_lo, diff_hi = mean_ci(diffs)
            n = len(rows)
            promote = sum(r["ever_promote"] for r in rows)
            first = [r["first_deploy"] for r in rows if r["first_deploy"] >= 0]
            record = {
                "net_mean": cost_mean,
                "net_ci95": [cost_lo, cost_hi],
                "paired_difference_mean": diff_mean,
                "paired_difference_ci95": [diff_lo, diff_hi],
                "loss_mean": statistics.mean(r["loss"] for r in rows),
                "labels_mean": statistics.mean(r["labels"] for r in rows),
                "switches_mean": statistics.mean(r["switches"] for r in rows),
                "promotions": promote,
                "promotion_rate": promote / n,
                "promotion_wilson95": list(wilson(promote, n)),
                "first_promotion_mean_among_promoters": statistics.mean(first) if first else None,
                "rollbacks_mean": statistics.mean(r["n_rollbacks"] for r in rows),
            }
            policy_records[policy] = record
            lines.append(
                f"| {cell} | `{policy}` | `{ref}` | {cost_mean:.2f} "
                f"[{cost_lo:.2f}, {cost_hi:.2f}] | {diff_mean:+.2f} "
                f"[{diff_lo:+.2f}, {diff_hi:+.2f}] | {record['loss_mean']:.2f} | "
                f"{record['labels_mean']:.1f} | {record['switches_mean']:.2f} | "
                f"{promote}/{n} | {record['first_promotion_mean_among_promoters'] if first else '—'} | "
                f"{record['rollbacks_mean']:.2f} |"
            )
            identity_max = max(
                identity_max,
                *(
                    abs(r["net"] - (r["loss"] + 0.05 * r["labels"] + 5 * r["switches"]))
                    for r in rows
                ),
            )
        cells[cell] = cell_result

    risk_gate = True
    favorable = []
    for cell in ("F0_better", "F3_reversal_1200", "F6_delay400_better@B100"):
        for policy, rec in cells[cell]["policies"].items():
            if policy in ("economic_replacement", "E_srrSR:gated_deployment"):
                continue
            _lo, hi = rec["paired_difference_ci95"]
            if rec["paired_difference_mean"] <= -5 and hi < 0:
                adverse_harm = max(
                    cells[adverse]["policies"][policy]["net_mean"]
                    - cells[adverse]["policies"]["CONTROL_never_switch"]["net_mean"]
                    for adverse in ("F3_reversal_800", "F0_null")
                )
                if adverse_harm <= 5:
                    favorable.append({"cell": cell, "policy": policy})
                else:
                    risk_gate = False

    # Dynamic economic arithmetic is prospective and parameter-based, not fitted to policy outcomes.
    lines.extend(
        [
            "",
            "## Interpretation and decision",
            "",
            "The primary development gate requires ≥5 units of paired savings with the full interval",
            "below zero on a worthwhile cell and ≤5 units mean harm to never-switch in both the",
            "unfavorable reversal and null cells. No policy met that gate. `economic_replacement` and",
            "`E_srrSR:gated_deployment` were excluded from equal-safety headroom because their prior",
            "stated error controls are not probability-of-any-false-promotion controls; see null rates",
            "below. The E-SR's ARL guarantee is not equivalent to an anytime false-alarm guarantee.",
            "",
            "The two reversal cells share a ±0.08/event advantage schedule. Expected cumulative gain",
            "before switch expenditure is +32 in `F3_reversal_1200` and −32 in `F3_reversal_800`;",
            "thus the former can repay two 5-unit switches while the latter cannot. These are",
            "evaluator-side design facts, not information supplied to methods.",
            "",
            f"Cost identity maximum absolute residual: {identity_max:.12g}.",
            "",
            "**Decision: `BENCHMARK_ONLY`.** This pilot identifies a real economic trade-off and a",
            "promising favorable-reversal cell for future work, but no frozen, safety-qualified",
            "implemented comparator combination met the development gate. The large apparent gains",
            "from the economic selector and E-SR come with null promotion rates that rule out an",
            "equal-safety claim at this sample size. There is no basis for a novel-method claim or",
            "real-data confirmation yet.",
            "",
            "### Smallest next step",
            "",
            "Before proposing a new mechanism, prospectively calibrate the existing conventional",
            "two-sided restart detector to a probability-of-any-false-promotion contract on a",
            "correctly specified null, then repeat only the two reversal cells plus the null and",
            "compare against `E_swcert`, RMM, and never-switch. If the calibrated conventional method",
            "closes the economic gap, stop the novelty search.",
            "",
            "## Provenance",
            "",
            f"- Runner manifest source revision: `{json.loads((RUN / 'manifest.json').read_text())['git']}`.",
            f"- Raw records SHA-256: `{sha256(RAW)}`.",
            f"- Manifest SHA-256: `{sha256(RUN / 'manifest.json')}`.",
            f"- Experiment script SHA-256: `{sha256(ROOT / 'scripts/sota_sprint/screen.py')}`.",
            f"- Analysis script SHA-256: `{sha256(Path(__file__).resolve())}`.",
            f"- Protocol SHA-256: `{sha256(ROOT / 'research/scoped_method/pilots/economic_headroom_matrix_20261106/protocol.md')}`.",
            "- Synthetic only; no real data, confirmation holdout, or oracle policy access.",
        ]
    )
    result = {
        "decision": "BENCHMARK_ONLY",
        "n_streams_per_cell": 30,
        "n_rows": sum(len(v) for v in paired.values()),
        "cost_identity_max_abs_residual": identity_max,
        "risk_qualified_gate_passes": favorable,
        "risk_gate_failed_for_candidate": not risk_gate,
        "cells": cells,
        "sha256": {
            "records.jsonl": sha256(RAW),
            "manifest.json": sha256(RUN / "manifest.json"),
            "screen.py": sha256(ROOT / "scripts/sota_sprint/screen.py"),
            "analyze_economic_headroom_matrix.py": sha256(Path(__file__).resolve()),
            "protocol.md": sha256(
                ROOT / "research/scoped_method/pilots/economic_headroom_matrix_20261106/protocol.md"
            ),
        },
    }
    (RUN / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    (RUN / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(RUN / "RESULTS.md")


if __name__ == "__main__":
    main()
