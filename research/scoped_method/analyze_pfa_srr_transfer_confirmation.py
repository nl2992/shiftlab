"""Analyze the frozen matched-host PFA-SR transfer confirmation."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from scipy.stats import t

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "research/scoped_method/pilots/pfa_srr_transfer_confirmation_20261106/run"
RAW = RUN / "records.jsonl"
CELLS = [
    "PFA_confirm_persistent",
    "PFA_confirm_near",
    "PFA_confirm_delay_scarce@B100",
    "PFA_confirm_null",
    "F3_reversal_800",
]
POLICIES = [
    "CONTROL_never_switch",
    "xu_acquisition_only",
    "E_rb:gated_adaptive_range",
    "rmm:gated_deployment+RMM",
    "rmm:gated_adaptive_range+RMM",
    "E_swcert",
    "E_srrSR:gated_deployment",
    "PFA-SR:gated_deployment",
    "PFA-SR:gated_adaptive_range",
]
HOST_REFERENCE = {
    "PFA-SR:gated_deployment": "rmm:gated_deployment+RMM",
    "PFA-SR:gated_adaptive_range": "rmm:gated_adaptive_range+RMM",
}
TARGET_CELLS = [
    "PFA_confirm_persistent",
    "PFA_confirm_near",
    "PFA_confirm_delay_scarce@B100",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def mean_ci(xs: list[float]) -> tuple[float, float, float]:
    m = statistics.mean(xs)
    half = t.ppf(0.975, len(xs) - 1) * statistics.stdev(xs) / math.sqrt(len(xs))
    return m, m - half, m + half


def wilson(k: int, n: int) -> tuple[float, float]:
    z = 1.959963984540054
    phat = k / n
    den = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / den
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / den
    return center - half, center + half


def main() -> None:
    streams: dict[tuple[str, int], dict[str, dict]] = defaultdict(dict)
    for line in RAW.open():
        row = json.loads(line)
        streams[(row["regime"], row["seed"])][row["policy"]] = row

    summaries: dict[str, dict[str, dict]] = {}
    lines = [
        "# PFA-SR matched-host transfer confirmation results",
        "",
        "**Status:** fresh synthetic confirmation of a published detector application, not independent",
        "real-data validation and not a new-method claim. The cross-host development screen is not",
        "pooled. This run uses 100 matched streams in each of five cells (4,500 policy rows).",
        "",
        "Net cost = predictive loss + 0.05 × requested labels + 5 × deployment switches.",
        "Intervals are paired t intervals over the 100 shared streams; the prespecified target-cell",
        "gate requires at least 5 units of savings with the interval below zero against both the",
        "corrected adapter and the same-host RMM. No multiplicity adjustment across target cells.",
        "",
        "## All policy results",
        "",
        "| Cell | Policy | Net [95% CI] | Difference vs never [95% CI] | Loss | Labels | Switches | Promotions | Rollbacks |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    max_residual = 0.0
    for cell in CELLS:
        rows = [v for (c, _), v in streams.items() if c == cell]
        cell_summary: dict[str, dict] = {}
        for policy in POLICIES:
            ys = [stream[policy] for stream in rows]
            net, lo, hi = mean_ci([row["net"] for row in ys])
            diff, dlo, dhi = mean_ci(
                [
                    row["net"] - stream["CONTROL_never_switch"]["net"]
                    for row, stream in zip(ys, rows, strict=True)
                ]
            )
            promos = sum(row["ever_promote"] for row in ys)
            record = {
                "n": len(ys),
                "net_mean": net,
                "net_ci95": [lo, hi],
                "difference_vs_never_mean": diff,
                "difference_vs_never_ci95": [dlo, dhi],
                "loss_mean": statistics.mean(row["loss"] for row in ys),
                "labels_mean": statistics.mean(row["labels"] for row in ys),
                "switches_mean": statistics.mean(row["switches"] for row in ys),
                "promotions": promos,
                "promotion_rate": promos / len(ys),
                "promotion_wilson95": list(wilson(promos, len(ys))),
                "rollbacks_mean": statistics.mean(row["n_rollbacks"] for row in ys),
            }
            cell_summary[policy] = record
            lines.append(
                f"| {cell} | `{policy}` | {net:.2f} [{lo:.2f}, {hi:.2f}] | "
                f"{diff:+.2f} [{dlo:+.2f}, {dhi:+.2f}] | {record['loss_mean']:.2f} | "
                f"{record['labels_mean']:.1f} | {record['switches_mean']:.2f} | "
                f"{promos}/{len(ys)} | {record['rollbacks_mean']:.2f} |"
            )
            for row in ys:
                max_residual = max(
                    max_residual,
                    abs(row["net"] - (row["loss"] + 0.05 * row["labels"] + 5 * row["switches"])),
                )
        summaries[cell] = cell_summary

    contrasts: dict[str, dict[str, dict]] = {}
    for cell in TARGET_CELLS:
        rows = [v for (c, _), v in streams.items() if c == cell]
        contrasts[cell] = {}
        lines.extend(
            [
                "",
                f"## Frozen paired contrasts: {cell}",
                "",
                "| PFA-SR host | Comparator | Difference [95% CI] | Pass ≥5 savings? |",
                "|---|---|---:|---|",
            ]
        )
        for policy, host_reference in HOST_REFERENCE.items():
            comparators = ["xu_acquisition_only", host_reference]
            contrasts[cell][policy] = {}
            for comparator in comparators:
                diffs = [stream[policy]["net"] - stream[comparator]["net"] for stream in rows]
                mean, lo, hi = mean_ci(diffs)
                passed = mean <= -5 and hi < 0
                contrasts[cell][policy][comparator] = {
                    "mean": mean,
                    "ci95": [lo, hi],
                    "pass_five_unit_gate": bool(passed),
                }
                lines.append(
                    f"| `{policy}` | `{comparator}` | {mean:+.2f} [{lo:+.2f}, {hi:+.2f}] | "
                    f"{'yes' if passed else 'no'} |"
                )

    null = summaries["PFA_confirm_null"]
    null_rates = {
        policy: {
            "promotions": null[policy]["promotions"],
            "n": null[policy]["n"],
            "rate": null[policy]["promotion_rate"],
            "wilson95": null[policy]["promotion_wilson95"],
        }
        for policy in ("PFA-SR:gated_deployment", "PFA-SR:gated_adaptive_range")
    }

    persistent_pass = bool(
        all(
            contrasts["PFA_confirm_persistent"][policy][comp]["pass_five_unit_gate"]
            for policy in HOST_REFERENCE
            for comp in ("xu_acquisition_only", HOST_REFERENCE[policy])
        )
    )
    null_pass = bool(all(v["rate"] <= 0.0936 for v in null_rates.values()))
    # The registered claim covers all three persistent/late target alternatives.
    full_target_pass = bool(
        all(
            contrasts[cell][policy][comp]["pass_five_unit_gate"]
            for cell in TARGET_CELLS
            for policy in HOST_REFERENCE
            for comp in ("xu_acquisition_only", HOST_REFERENCE[policy])
        )
        and null_pass
    )

    manifest = json.loads((RUN / "manifest.json").read_text())
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"Strong persistent cell passed both comparator contrasts: `{persistent_pass}`. Null screening gate passed: `{null_pass}`.",
            f"Full frozen target-region gate across strong, near, delayed/scarce cells: `{full_target_pass}`.",
            "",
            "PFA-SR shows a reproducible, practically material synthetic gain in the prespecified",
            "strong-persistent cell, with same-host comparisons and a null promotion rate within the",
            "screening tolerance. It does not pass the full frozen persistent/near/delayed target",
            "region: the weaker near-effect cell has no resolved savings, and the delayed/scarce cell",
            "does not clear the same-host comparison. In the reversal stress cell, both PFA-SR hosts",
            "are substantially more costly than never-switch; report this as an explicit scope limit.",
            "",
            "The 2026 PFA-weighted e-SR is established prior art. Current evidence is an application",
            "signal for the strong-persistent environment, not a novel detector contribution. It may",
            "justify a frozen real-data replay only if the target can be defined without inspecting",
            "evaluation outcomes and the PFA prior remains fixed.",
            "",
            f"Net-cost accounting maximum absolute residual: {max_residual:.12g}.",
            "",
            "## Null promotion intervals",
            "",
        ]
    )
    for policy, values in null_rates.items():
        lo, hi = values["wilson95"]
        lines.append(
            f"- `{policy}`: {values['promotions']}/{values['n']} = {values['rate']:.3f}, "
            f"Wilson 95% CI [{lo:.3f}, {hi:.3f}]."
        )
    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- Source revision: `{manifest['git']}`.",
            f"- Raw records SHA-256: `{digest(RAW)}`.",
            f"- Manifest SHA-256: `{digest(RUN / 'manifest.json')}`.",
            f"- Protocol SHA-256: `{digest(ROOT / 'research/scoped_method/pilots/pfa_srr_transfer_confirmation_20261106/protocol.md')}`.",
            f"- Detector SHA-256: `{digest(ROOT / 'scripts/sota_sprint/pfa_srr_baseline.py')}`.",
            f"- Runner SHA-256: `{digest(ROOT / 'scripts/sota_sprint/screen.py')}`.",
            "- Synthetic only; the oracle truth was evaluator-side and no real or locked holdout was opened.",
        ]
    )
    result = {
        "persistent_cell_pass": persistent_pass,
        "null_screen_pass": null_pass,
        "full_registered_target_gate_pass": full_target_pass,
        "rows": sum(len(v) for v in streams.values()),
        "cost_identity_max_abs_residual": max_residual,
        "null_promotion_rates": null_rates,
        "contrasts": contrasts,
        "cells": summaries,
        "sha256": {
            "records.jsonl": digest(RAW),
            "manifest.json": digest(RUN / "manifest.json"),
            "protocol.md": digest(
                ROOT
                / "research/scoped_method/pilots/pfa_srr_transfer_confirmation_20261106/protocol.md"
            ),
            "pfa_srr_baseline.py": digest(ROOT / "scripts/sota_sprint/pfa_srr_baseline.py"),
            "screen.py": digest(ROOT / "scripts/sota_sprint/screen.py"),
        },
    }
    (RUN / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    (RUN / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print(RUN / "RESULTS.md")


if __name__ == "__main__":
    main()
