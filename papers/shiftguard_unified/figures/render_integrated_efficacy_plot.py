"""Render the frozen integrated-efficacy contrasts in PaperBanana style.

The visual styling follows PaperBanana's NeurIPS plot guide
(`style_guides/neurips2025_plot_style_guide.md` in the official repository),
with a white canvas, muted palette and geometry-coded categories. The plot is
rendered from exact tabular results; no generative image model alters values.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
FIGURE_DIR = Path(__file__).resolve().parent
SOURCE = (
    ROOT
    / "outputs"
    / "shiftguard_unified"
    / "integrated_confirmation"
    / "efficacy_100_v1"
    / "analysis_v3"
    / "primary_contrasts.csv"
)
AGGREGATE = FIGURE_DIR / "integrated_efficacy_contrasts.csv"
PNG = FIGURE_DIR / "integrated_efficacy_forest.png"
PDF = FIGURE_DIR / "integrated_efficacy_forest.pdf"

PROFILE_ORDER = [
    "Stationary",
    "Benign nuisance shift",
    "Boundary-local harm",
    "Post-promotion reversal",
    "Recurring regimes",
    "Residual-variance shift",
    "Adaptation begins during monitor",
    "Adaptation begins after monitor",
]
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
COMPARATORS = {
    "continue": {
        "title": "Continue",
        "color": "#4C78A8",
        "marker": "o",
    },
    "two_gate": {
        "title": "Two-gate",
        "color": "#D47A61",
        "marker": "s",
    },
    "full_pipeline_fixed_certification": {
        "title": "Fixed-candidate pipeline",
        "color": "#4F927D",
        "marker": "^",
    },
}


def load_and_validate() -> list[dict[str, str]]:
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        source_rows = list(csv.DictReader(stream))
    with AGGREGATE.open(newline="", encoding="utf-8") as stream:
        plotted_rows = list(csv.DictReader(stream))
    if len(source_rows) != 22 or len(plotted_rows) != 22:
        raise ValueError("Expected exactly 22 source contrasts and 22 plotted rows")

    profile_to_label = PROFILE_LABELS
    reference_to_label = {
        reference: f"Full pipeline vs {details['title']}"
        for reference, details in COMPARATORS.items()
    }
    source_by_key = {(row["profile"], row["reference"]): row for row in source_rows}
    if len(source_by_key) != 22:
        raise ValueError("Source contrast keys are not unique")

    plotted_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for row in plotted_rows:
        profile = row["profile"]
        comparison = row["comparison"]
        matches = [
            reference for reference, label in reference_to_label.items() if comparison == label
        ]
        if profile not in PROFILE_ORDER or len(matches) != 1:
            raise ValueError(f"Unexpected plotted category: {profile}, {comparison}")
        key = (profile, matches[0])
        if key in plotted_by_key:
            raise ValueError(f"Duplicate plotted contrast: {key}")
        plotted_by_key[key] = row

    if set(plotted_by_key) != {
        (profile_to_label[row["profile"]], row["reference"]) for row in source_rows
    }:
        raise ValueError("Aggregate plot rows do not cover exactly the source contrasts")

    field_pairs = [
        ("mean_paired_expected_utility_difference", "mean_paired_expected_utility_difference"),
        ("bootstrap_ci_low_95_descriptive", "bootstrap_ci_low_95_descriptive"),
        ("bootstrap_ci_high_95_descriptive", "bootstrap_ci_high_95_descriptive"),
        ("streams", "streams"),
    ]
    for source_key, source_row in source_by_key.items():
        output = plotted_by_key[(profile_to_label[source_key[0]], source_key[1])]
        for output_field, source_field in field_pairs:
            if output[output_field] != source_row[source_field]:
                raise ValueError(
                    f"Source mismatch for {source_key}, {output_field}: "
                    f"{source_row[source_field]} != {output[output_field]}"
                )
    return plotted_rows


def render(rows: list[dict[str, str]]) -> None:
    by_comparison = {reference: [] for reference in COMPARATORS}
    for row in rows:
        for reference, details in COMPARATORS.items():
            if row["comparison"] == f"Full pipeline vs {details['title']}":
                by_comparison[reference].append(row)
                break

    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 11,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )
    fig, axes = plt.subplots(
        nrows=1,
        ncols=3,
        figsize=(14.2, 6.0),
        sharex=True,
        sharey=True,
        constrained_layout=False,
    )
    y_by_profile = {profile: len(PROFILE_ORDER) - 1 - i for i, profile in enumerate(PROFILE_ORDER)}
    x_min, x_max = -260.0, 220.0

    for panel_index, (ax, (reference, details)) in enumerate(
        zip(axes, COMPARATORS.items(), strict=True)
    ):
        panel_rows = by_comparison[reference]
        present_profiles = {row["profile"] for row in panel_rows}
        for profile in PROFILE_ORDER:
            y = y_by_profile[profile]
            if profile not in present_profiles:
                ax.text(
                    0.985,
                    y,
                    "not tested",
                    transform=ax.get_yaxis_transform(),
                    ha="right",
                    va="center",
                    fontsize=7,
                    color="#7A7A7A",
                    style="italic",
                )
        for row in panel_rows:
            y = y_by_profile[row["profile"]]
            mean = float(row["mean_paired_expected_utility_difference"])
            low = float(row["bootstrap_ci_low_95_descriptive"])
            high = float(row["bootstrap_ci_high_95_descriptive"])
            ax.errorbar(
                mean,
                y,
                xerr=np.array([[mean - low], [high - mean]]),
                fmt=details["marker"],
                markersize=5.5,
                markerfacecolor=details["color"],
                markeredgecolor="#263442",
                markeredgewidth=0.55,
                ecolor="#37424D",
                elinewidth=1.15,
                capsize=2.8,
                capthick=1.15,
                zorder=4,
            )
        ax.axvline(0, color="#505862", linestyle="--", linewidth=1.0, zorder=2)
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(-0.65, len(PROFILE_ORDER) - 0.35)
        ax.set_title(
            f"Full pipeline vs {details['title']}\n(n={len(panel_rows)} contrasts)", pad=11
        )
        ax.set_yticks(range(len(PROFILE_ORDER)))
        ax.set_yticklabels(list(reversed(PROFILE_ORDER)))
        ax.set_xticks([-200, -100, 0, 100, 200])
        ax.set_axisbelow(True)
        ax.grid(axis="x", linestyle=":", color="#D9DDE2", linewidth=0.75)
        ax.tick_params(axis="both", direction="in", length=3, color="#727A83")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#9DA4AB")
        ax.spines["bottom"].set_color("#9DA4AB")
        if panel_index:
            ax.tick_params(axis="y", labelleft=False)

    fig.supylabel("Shift profile", x=0.015, fontsize=10)
    fig.supxlabel(
        "Mean paired expected-utility difference (full pipeline − comparator); positive favors full pipeline",
        y=0.065,
        fontsize=9,
    )
    fig.text(
        0.5,
        0.025,
        "Dots are means; bars are descriptive paired-seed bootstrap 95% intervals "
        "(not multiplicity-adjusted). Each profile uses 100 independent synthetic streams.",
        ha="center",
        va="center",
        fontsize=8,
        color="#4E565E",
    )
    fig.subplots_adjust(left=0.205, right=0.99, top=0.87, bottom=0.19, wspace=0.06)
    fig.savefig(PNG, dpi=300, bbox_inches="tight")
    fig.savefig(PDF, bbox_inches="tight")
    plt.close(fig)
    print(f"Validated and rendered {len(rows)} source-matched contrasts to PNG and PDF")


if __name__ == "__main__":
    render(load_and_validate())
