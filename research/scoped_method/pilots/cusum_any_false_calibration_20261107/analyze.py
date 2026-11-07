"""Recompute all frozen CUSUM calibration/evaluation summaries from JSONL records."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parent
METHODS = (
    "E_srr:gated_deployment",
    "E_swcert",
    "E_rb:gated_adaptive_range",
    "E_srrSR:gated_deployment",
    "CONTROL_never_switch",
)
METRICS = (
    "net",
    "loss",
    "labels",
    "switches",
    "ever_promote",
    "n_rollbacks",
    "first_deploy",
)


def read_rows(*folders: str) -> list[dict]:
    rows = []
    for folder in folders:
        rows.extend(
            json.loads(line)
            for line in (ROOT / folder / "records.jsonl").read_text().splitlines()
            if line
        )
    return rows


def wilson_upper(hits: int, n: int, confidence: float) -> float:
    from scipy.stats import norm

    z = float(norm.ppf(confidence))
    p = hits / n
    den = 1 + z * z / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / den


def mean_ci(x: list[float]) -> tuple[float, float, float]:
    arr = np.asarray(x, dtype=float)
    mean = float(arr.mean())
    half = float(student_t.ppf(0.975, len(arr) - 1) * arr.std(ddof=1) / np.sqrt(len(arr)))
    return mean, mean - half, mean + half


def main() -> None:
    folders = {
        "F0_null": {
            "E_srr:gated_deployment": "eval_candidate_null",
            "E_swcert": "eval_references_null",
            "E_rb:gated_adaptive_range": "eval_references_null",
            "CONTROL_never_switch": "eval_references_null",
            "E_srrSR:gated_deployment": "eval_esr_null",
        },
        "F3_reversal_1200": {
            "E_srr:gated_deployment": "eval_candidate_reversal",
            "E_swcert": "eval_references_reversal",
            "E_rb:gated_adaptive_range": "eval_references_reversal",
            "CONTROL_never_switch": "eval_references_reversal",
            "E_srrSR:gated_deployment": "eval_esr_reversal",
        },
        "F3_reversal_800": {
            "E_srr:gated_deployment": "eval_candidate_reversal",
            "E_swcert": "eval_references_reversal",
            "E_rb:gated_adaptive_range": "eval_references_reversal",
            "CONTROL_never_switch": "eval_references_reversal",
            "E_srrSR:gated_deployment": "eval_esr_reversal",
        },
    }
    all_rows = []
    for regime, policy_folders in folders.items():
        for policy, folder in policy_folders.items():
            data = [r for r in read_rows(folder) if r["regime"] == regime and r["policy"] == policy]
            expected = 1000 if regime == "F0_null" else 200
            if len(data) != expected:
                raise ValueError(f"{regime}/{policy}: expected {expected}, found {len(data)}")
            all_rows.extend(data)

    by_key = {(r["regime"], r["ep"], r["seed"], r["policy"]): r for r in all_rows}
    if len(by_key) != len(all_rows):
        raise ValueError("duplicate (regime, episode, seed, policy) result keys")

    lines = [
        "# E-CUSUM independent evaluation results",
        "",
        "**Decision: economic gate FAIL; stop this frozen CUSUM operating-point lane.**",
        "The calibrated CUSUM passes the independent null screen but does not meet the primary",
        "cost-improvement requirement against every registered comparator.",
        "",
        "This is an empirical check of a known detector, not a novel-method result. All intervals",
        "are paired two-sided 95% Student t intervals across shared episode seeds. Lower net cost is",
        "better. The contract is T=2,000, B=200, label cost 0.05, switch cost 5, and alpha values",
        "as frozen in `EVALUATION_FREEZE.md`.",
        "",
        "## Cell outcomes and cost decomposition",
        "",
        "Mean promotion time is conditional on promotion (the raw `-1` sentinel for never-promoted",
        "episodes is excluded). Net cost equals predictive loss + label expenditure + switching",
        "expenditure; expenditure is recomputed from mean counts and the frozen unit costs.",
        "",
        "| Cell | Policy | Net cost | Predictive loss | Label cost | Switch cost | Labels | Switches | Promoted | Rollbacks | Mean first promotion if promoted |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    cell_means: dict[str, dict[str, dict[str, float]]] = {}
    for regime in folders:
        cell_means[regime] = {}
        for policy in METHODS:
            rows = [r for r in all_rows if r["regime"] == regime and r["policy"] == policy]
            means = {m: float(np.mean([r[m] for r in rows])) for m in METRICS}
            cell_means[regime][policy] = means
            label_cost = means["labels"] * 0.05
            switch_cost = means["switches"] * 5.0
            residual = means["net"] - means["loss"] - label_cost - switch_cost
            if abs(residual) > 1e-8:
                raise ValueError(f"cost identity residual {residual} for {regime}/{policy}")
            promoted_rows = [r for r in rows if r["first_deploy"] >= 0]
            first = (
                f"{np.mean([r['first_deploy'] for r in promoted_rows]):.2f}"
                if promoted_rows
                else "NA"
            )
            lines.append(
                f"| {regime} | {policy} | {means['net']:.2f} | {means['loss']:.2f} | "
                f"{label_cost:.2f} | {switch_cost:.2f} | {means['labels']:.2f} | "
                f"{means['switches']:.3f} | {means['ever_promote']:.3f} | "
                f"{means['n_rollbacks']:.3f} | {first} |"
            )

    null_rows = [
        r for r in all_rows if r["regime"] == "F0_null" and r["policy"] == "E_srr:gated_deployment"
    ]
    fp = sum(r["ever_promote"] > 0 for r in null_rows)
    upper = wilson_upper(fp, len(null_rows), 0.95)
    lines += [
        "",
        "## Null gate",
        "",
        f"The candidate promoted in {fp}/{len(null_rows)} independent `F0_null` streams; the",
        f"one-sided 95% Wilson upper bound is {upper:.5f}. The frozen maximum was 0.05:",
        f"**{'PASS' if upper <= 0.05 else 'FAIL'}**. This does not establish a theorem or apply beyond the registered null.",
        "",
        "## Paired cost contrasts",
        "",
        "Candidate minus comparator in net cost; negative favors CUSUM. The primary criterion",
        "requires both a mean of at most -5 and an upper 95% confidence limit below zero for each",
        "registered primary comparator.",
        "",
        "| Cell | Comparator | Mean paired difference | Paired 95% CI |",
        "|---|---|---:|---:|",
    ]
    contrasts = {}
    for regime in folders:
        candidate_rows = [
            r for r in all_rows if r["regime"] == regime and r["policy"] == "E_srr:gated_deployment"
        ]
        for comparator in METHODS:
            if comparator == "E_srr:gated_deployment":
                continue
            diffs = []
            for a in candidate_rows:
                # Seed and episode identify the common generated stream across policy invocations.
                key = (regime, a["ep"], a["seed"], comparator)
                diffs.append(a["net"] - by_key[key]["net"])
            mu, lo, hi = mean_ci(diffs)
            contrasts[(regime, comparator)] = (mu, lo, hi)
            lines.append(f"| {regime} | {comparator} | {mu:.2f} | [{lo:.2f}, {hi:.2f}] |")

    target_pass = all(
        contrasts[("F3_reversal_1200", comp)][0] <= -5
        and contrasts[("F3_reversal_1200", comp)][2] < 0
        for comp in ("E_swcert", "E_rb:gated_adaptive_range", "CONTROL_never_switch")
    )
    adverse_ok = contrasts[("F3_reversal_800", "CONTROL_never_switch")][0] <= 5
    lines += [
        "",
        "## Gate decision and interpretation",
        "",
        f"- Independent null gate: **{'PASS' if upper <= 0.05 else 'FAIL'}** (upper {upper:.5f}).",
        f"- Primary cost gate: **{'PASS' if target_pass else 'FAIL'}**.",
        f"- Adverse short-reversal cost gate: **{'PASS' if adverse_ok else 'FAIL'}**.",
        "",
        "The calibrated CUSUM is not cheaper than the strongest frozen certificate/RMM references",
        "on the worthwhile reversal target and has large excess cost against never-switch. Its null",
        "calibration is useful baseline-fidelity evidence, but the operating point does not repair",
        "the economic failure. Per the frozen rule, do not adjust alpha or substitute another method",
        "using these evaluation outcomes. No real data was opened.",
        "",
        "## Raw artifact hashes",
        "",
        "SHA-256 hashes bind every independent evaluation record file:",
        "",
        "| Run | Records SHA-256 | Manifest SHA-256 |",
        "|---|---|---|",
    ]
    run_names = (
        "eval_candidate_null",
        "eval_candidate_reversal",
        "eval_references_null",
        "eval_references_reversal",
        "eval_esr_null",
        "eval_esr_reversal",
    )
    for name in run_names:
        folder = ROOT / name
        record_hash = hashlib.sha256((folder / "records.jsonl").read_bytes()).hexdigest()
        manifest_hash = hashlib.sha256((folder / "manifest.json").read_bytes()).hexdigest()
        lines.append(f"| {name} | `{record_hash}` | `{manifest_hash}` |")
    (ROOT / "EVALUATION_RESULTS.md").write_text("\n".join(lines) + "\n")
    print(f"Wrote {ROOT / 'EVALUATION_RESULTS.md'}")
    print(f"Rows: {len(all_rows)}; candidate null promotions: {fp}/1000; upper95={upper:.6f}")
    print(
        f"Primary gate: {'PASS' if target_pass else 'FAIL'}; adverse gate: {'PASS' if adverse_ok else 'FAIL'}"
    )


if __name__ == "__main__":
    main()
