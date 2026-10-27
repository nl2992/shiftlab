"""Prepare factual aggregate data for a PaperBanana statistical plot.

This script does not render or alter the source analysis. It produces a compact,
labelled copy of the 22 frozen primary contrasts for use in PaperBanana.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = (
    ROOT
    / "outputs"
    / "shiftguard_unified"
    / "integrated_confirmation"
    / "efficacy_100_v1"
    / "analysis_v3"
    / "primary_contrasts.csv"
)
DESTINATION = Path(__file__).resolve().parent / "integrated_efficacy_contrasts.csv"
PAPERBANANA_INPUT = Path(__file__).resolve().parent / "paperbanana_integrated_efficacy_input.md"

PROFILE_LABELS = {
    "stationary": "Stationary",
    "benign_nuisance": "Benign nuisance shift",
    "boundary_local_harm": "Boundary-local harm",
    "post_promotion_reversal": "Post-promotion reversal",
    "recurring_regimes": "Recurring regimes",
    "residual_variance": "Residual-variance shift",
    "harmful_adaptation_at_monitor": "Adaptation begins during monitor",
    "harmful_adaptation_native": "Adaptation begins after monitor",
}
REFERENCE_LABELS = {
    "continue": "Continue",
    "two_gate": "Two-gate",
    "full_pipeline_fixed_certification": "Fixed-candidate pipeline",
}


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as source_file:
        rows = list(csv.DictReader(source_file))

    if len(rows) != 22:
        raise ValueError(f"Expected 22 frozen primary contrasts, found {len(rows)}")
    comparison_counts = {
        reference: sum(row["reference"] == reference for row in rows)
        for reference in REFERENCE_LABELS
    }
    if comparison_counts != {
        "continue": 6,
        "two_gate": 8,
        "full_pipeline_fixed_certification": 8,
    }:
        raise ValueError(f"Unexpected contrast family counts: {comparison_counts}")
    keys = [(row["profile"], row["reference"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate profile/comparator contrast in source results")

    fields = [
        "profile",
        "comparison",
        "streams",
        "mean_paired_expected_utility_difference",
        "bootstrap_ci_low_95_descriptive",
        "bootstrap_ci_high_95_descriptive",
        "holm_adjusted_p",
        "holm_reject_at_0_05",
        "bonferroni_simultaneous_lower_95",
        "interval_note",
    ]
    output_rows: list[dict[str, str]] = []
    for row in rows:
        profile = row["profile"]
        reference = row["reference"]
        if profile not in PROFILE_LABELS:
            raise ValueError(f"Unexpected profile in source results: {profile}")
        if reference not in REFERENCE_LABELS:
            raise ValueError(f"Unexpected reference method in source results: {reference}")
        if row["treatment"] != "full_pipeline" or row["streams"] != "100":
            raise ValueError(f"Unexpected treatment or seed count: {row}")
        output_rows.append(
            {
                "profile": PROFILE_LABELS[profile],
                "comparison": f"Full pipeline vs {REFERENCE_LABELS[reference]}",
                "streams": row["streams"],
                "mean_paired_expected_utility_difference": row[
                    "mean_paired_expected_utility_difference"
                ],
                "bootstrap_ci_low_95_descriptive": row["bootstrap_ci_low_95_descriptive"],
                "bootstrap_ci_high_95_descriptive": row["bootstrap_ci_high_95_descriptive"],
                "holm_adjusted_p": row["holm_adjusted_p"],
                "holm_reject_at_0_05": row["holm_reject_at_0_05"],
                "bonferroni_simultaneous_lower_95": row["bonferroni_simultaneous_lower_95"],
                "interval_note": "Descriptive paired-seed bootstrap 95% CI; not multiplicity-adjusted",
            }
        )

    with DESTINATION.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    with PAPERBANANA_INPUT.open("w", encoding="utf-8", newline="\n") as input_file:
        input_file.write(
            "# PaperBanana input: integrated efficacy forest plot\n\n"
            "Create a publication-style statistical forest plot from the exact data "
            "below. Plot mean paired expected-utility difference on the x-axis; "
            "positive values favor Full pipeline. Use three facets by comparator, "
            "with the eight profiles in the same order in each facet. Plot the "
            "supplied descriptive paired-seed bootstrap 95% intervals as bars and "
            "the mean as a point; add a vertical zero line. Preserve every row and "
            "numeric value exactly. The plotted intervals are descriptive, not "
            "multiplicity-adjusted and not the registered tests. Do not infer or "
            "invent values.\n\n"
            "Caption: Integrated synthetic efficacy confirmation (100 independent "
            "streams per profile). Each point is the mean paired expected-utility "
            "difference of the full monitor–scout–certify–intervene pipeline "
            "relative to the named baseline; positive values favor the full "
            "pipeline. Bars show descriptive paired-seed bootstrap 95% intervals. "
            "The registered 22 one-sided contrasts use Holm adjustment; see the "
            "result table for adjusted tests and simultaneous lower bounds. "
            "Synthetic results under the frozen 640-label cap; not real-data "
            "confirmation.\n\n"
            "Validate every plotted point and interval against the CSV before "
            "publication.\n\n"
            "```csv\n"
        )
        with DESTINATION.open(newline="", encoding="utf-8") as data_file:
            input_file.write(data_file.read())
        input_file.write("```\n")

    print(
        f"Wrote {len(output_rows)} contrasts to {DESTINATION.relative_to(ROOT)} "
        f"and a paste-ready PaperBanana brief to {PAPERBANANA_INPUT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
