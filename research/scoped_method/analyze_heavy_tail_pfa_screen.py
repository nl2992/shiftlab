"""Analyze the frozen heavy-tail PFA-SR development screen."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from scipy.stats import t

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "research/scoped_method/pilots/heavy_tail_pfa_screen_20261106/run"
RAW = RUN / "records.jsonl"
CELLS = [
    "PFA_tail_late_scarce@B100",
    "PFA_confirm_persistent",
    "PFA_confirm_null",
    "F3_reversal_800",
]
POLICIES = [
    "CONTROL_never_switch",
    "xu_acquisition_only",
    "E_rb:gated_adaptive_range",
    "rmm:gated_adaptive_range+RMM",
    "E_swcert",
    "PFA-SR:gated_adaptive_range",
    "PFA-SR:q1.2:gated_adaptive_range",
]
CANDIDATE = "PFA-SR:q1.2:gated_adaptive_range"
COMPARATORS = [
    "PFA-SR:gated_adaptive_range",
    "rmm:gated_adaptive_range+RMM",
    "xu_acquisition_only",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def mean_ci(values: list[float]) -> tuple[float, float, float]:
    mean = statistics.mean(values)
    half = t.ppf(0.975, len(values) - 1) * statistics.stdev(values) / math.sqrt(len(values))
    return mean, mean - half, mean + half


def main() -> None:
    streams: dict[tuple[str, int], dict[str, dict]] = defaultdict(dict)
    for line in RAW.open():
        row = json.loads(line)
        streams[(row["regime"], row["seed"])][row["policy"]] = row

    rows_by_cell = {
        cell: [records for (regime, _), records in streams.items() if regime == cell]
        for cell in CELLS
    }
    lines = [
        "# Heavy-tail PFA-SR development screen results",
        "",
        "**Decision:** candidate failed its frozen development gate. This finite-budget tail-prior",
        "parameterization does not merit confirmatory evaluation. It is reported in full and does",
        "not revise the earlier canonical PFA-SR confirmation.",
        "",
        "The run has 30 paired streams per cell and 840 policy rows. Net cost is loss + 0.05 × labels",
        "+ 5 × switches. Intervals are paired two-sided 95% t intervals over the shared seeds; no",
        "multiplicity correction. This is a development screen, not independent confirmation.",
        "",
        "## All policies",
        "",
        "| Cell | Policy | Net cost | Loss | Labels | Switches | Promotions | Rollbacks |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    summaries: dict[str, dict[str, dict]] = {}
    max_residual = 0.0
    for cell in CELLS:
        summaries[cell] = {}
        cell_rows = rows_by_cell[cell]
        for policy in POLICIES:
            policy_rows = [stream[policy] for stream in cell_rows]
            net = statistics.mean(row["net"] for row in policy_rows)
            values = {
                "net_mean": net,
                "loss_mean": statistics.mean(row["loss"] for row in policy_rows),
                "labels_mean": statistics.mean(row["labels"] for row in policy_rows),
                "switches_mean": statistics.mean(row["switches"] for row in policy_rows),
                "promotions": sum(row["ever_promote"] for row in policy_rows),
                "rollbacks_mean": statistics.mean(row["n_rollbacks"] for row in policy_rows),
            }
            summaries[cell][policy] = values
            lines.append(
                f"| {cell} | `{policy}` | {net:.2f} | {values['loss_mean']:.2f} | "
                f"{values['labels_mean']:.1f} | {values['switches_mean']:.2f} | "
                f"{values['promotions']}/30 | {values['rollbacks_mean']:.2f} |"
            )
            for row in policy_rows:
                max_residual = max(
                    max_residual,
                    abs(row["net"] - (row["loss"] + 0.05 * row["labels"] + 5 * row["switches"])),
                )

    lines.extend(
        [
            "",
            "## Frozen primary paired contrasts: late improvement with delay and B=100",
            "",
            "Candidate minus comparator net cost; a pass requires at least 5 units savings and the",
            "entire 95% interval below zero against canonical PFA-SR, same-host RMM and Xu adapter.",
            "",
            "| Comparator | Difference [95% CI] | ≥5-unit gate |",
            "|---|---:|---|",
        ]
    )
    primary = rows_by_cell["PFA_tail_late_scarce@B100"]
    contrasts: dict[str, dict] = {}
    for comparator in COMPARATORS:
        differences = [stream[CANDIDATE]["net"] - stream[comparator]["net"] for stream in primary]
        mean, low, high = mean_ci(differences)
        passed = mean <= -5 and high < 0
        contrasts[comparator] = {"mean": mean, "ci95": [low, high], "pass": bool(passed)}
        lines.append(
            f"| `{comparator}` | {mean:+.2f} [{low:+.2f}, {high:+.2f}] | "
            f"{'yes' if passed else 'no'} |"
        )

    null_promotions = summaries["PFA_confirm_null"][CANDIDATE]["promotions"]
    reversal_differences = [
        stream[CANDIDATE]["net"] - stream["CONTROL_never_switch"]["net"]
        for stream in rows_by_cell["F3_reversal_800"]
    ]
    reversal_mean, reversal_low, reversal_high = mean_ci(reversal_differences)
    primary_pass = all(value["pass"] for value in contrasts.values())
    adverse_pass = (
        reversal_mean <= 5 and summaries["PFA_confirm_null"][CANDIDATE]["promotions"] == 0
    )
    lines.extend(
        [
            "",
            "## Gate and interpretation",
            "",
            f"Primary late/scarce gate passed: `{primary_pass}`.",
            f"Null promotions: {null_promotions}/30 (screen only).",
            (
                f"Reversal candidate-minus-never mean: {reversal_mean:+.2f} "
                f"[{reversal_low:+.2f}, {reversal_high:+.2f}]."
            ),
            f"Adverse/null development gate passed: `{adverse_pass}`.",
            "",
            "The candidate did not clear the primary gate. In the registered late/scarce cell it",
            "cost 4.40 more than canonical PFA-SR [−1.27, +10.07], 5.30 more than same-host RMM",
            "[−0.01, +10.61], and 4.09 more than Xu [−0.48, +8.66]. It promoted 1/30 times",
            "versus 3/30 for canonical PFA-SR and 9/30 for same-host RMM; lower promotion here came",
            "with no cost advantage. In the reversal cell it cost materially more than never-switch.",
            "The candidate is stopped under its frozen development rule. A positive strong-persistent",
            "PFA-SR result remains the earlier published-method application signal, not evidence for",
            "this heavier-tail adjustment.",
            "",
            f"Maximum net-cost accounting residual: {max_residual:.12g}.",
            "",
            "## Provenance",
            "",
            f"- Run manifest SHA-256: `{digest(RUN / 'manifest.json')}`.",
            f"- Raw records SHA-256: `{digest(RAW)}`.",
            f"- Frozen protocol SHA-256: `{digest(ROOT / 'research/scoped_method/pilots/heavy_tail_pfa_screen_20261106/protocol.md')}`.",
            f"- Candidate source SHA-256: `{digest(ROOT / 'scripts/sota_sprint/pfa_srr_baseline.py')}`.",
            f"- Source revision in run manifest: `{json.loads((RUN / 'manifest.json').read_text())['git']}`.",
            "",
        ]
    )
    (RUN / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    summary = {
        "primary_pass": primary_pass,
        "adverse_null_pass": adverse_pass,
        "primary_contrasts": contrasts,
        "null_promotions": null_promotions,
        "reversal_candidate_minus_never": {
            "mean": reversal_mean,
            "ci95": [reversal_low, reversal_high],
        },
        "cost_identity_max_abs_residual": max_residual,
        "sha256": {"manifest": digest(RUN / "manifest.json"), "records": digest(RAW)},
    }
    (RUN / "analysis_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
