"""Summarize the registered empirical-Bernstein OPE scout development run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("outputs/scout_context_ope_eb_markov_development_v1")
METHOD = "scout_context_policy_eventwise_propensity_bound"
EXPECTED_ROWS = 25_920
EXPECTED_STREAMS = 6_480
BOOTSTRAP_DRAWS = 10_000
BOOTSTRAP_SEED = 21_900_180


def main() -> None:
    detail_path = ROOT / "metrics/scout_context_markov_development_streams.parquet"
    manifest_path = ROOT / "reports/manifest.json"
    if not detail_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(f"development artifacts are incomplete under {ROOT}")
    detail = pd.read_parquet(detail_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if len(detail) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, received {len(detail)}")
    if detail.duplicated(["scenario", "budget_rate", "seed", "alpha_allocation"]).any():
        raise ValueError("duplicate stream/method rows")
    if (detail["labels_queried"] > detail["label_budget"]).any():
        raise ValueError("hard label budget was exceeded")
    ope = detail.loc[detail["alpha_allocation"].eq(METHOD)].copy()
    if len(ope) != EXPECTED_STREAMS:
        raise ValueError(f"expected {EXPECTED_STREAMS} eventwise rows, received {len(ope)}")
    required = [
        "ope_eb_promoted",
        "ope_eb_lower_final",
        "ope_eb_width_final",
        "ope_lil_promoted",
        "ope_lil_lower_final",
        "ope_lil_width_final",
        "ope_eb_expected_postpromotion_net_gain",
    ]
    if ope[required].isna().any().any():
        raise ValueError("OPE comparison fields contain missing values")
    protocol = manifest["protocol"]
    protocol_path = Path(protocol["path"])
    if hashlib.sha256(protocol_path.read_bytes()).hexdigest() != protocol["sha256"]:
        raise ValueError("frozen protocol hash mismatch")

    rows: list[dict[str, object]] = []
    for name, subset in (
        ("null", ope.loc[ope["context_signal_strength"].eq(0)]),
        ("positive", ope.loc[ope["context_signal_strength"].gt(0)]),
        ("all", ope),
    ):
        rows.append(
            {
                "slice": name,
                "streams": len(subset),
                "fixed_promotion_rate": float(subset["promoted"].mean()),
                "ope_lil_promotion_rate": float(subset["ope_lil_promoted"].mean()),
                "ope_eb_promotion_rate": float(subset["ope_eb_promoted"].mean()),
                "fixed_expected_future_gain": float(
                    subset["expected_postpromotion_net_gain"].mean()
                ),
                "ope_lil_expected_future_gain": float(
                    subset["ope_lil_expected_postpromotion_net_gain"].mean()
                ),
                "ope_eb_expected_future_gain": float(
                    subset["ope_eb_expected_postpromotion_net_gain"].mean()
                ),
                "ope_lil_mean_lower": float(subset["ope_lil_lower_final"].mean()),
                "ope_eb_mean_lower": float(subset["ope_eb_lower_final"].mean()),
                "ope_lil_mean_width": float(subset["ope_lil_width_final"].mean()),
                "ope_eb_mean_width": float(subset["ope_eb_width_final"].mean()),
                "mean_labels": float(subset["labels_queried"].mean()),
            }
        )
    positive = ope.loc[ope["context_signal_strength"].gt(0)].copy()
    positive["eb_minus_fixed_gain"] = (
        positive["ope_eb_expected_postpromotion_net_gain"]
        - positive["expected_postpromotion_net_gain"]
    )
    seed_means = positive.groupby("seed")["eb_minus_fixed_gain"].mean().to_numpy()
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    boot = rng.choice(seed_means, size=(BOOTSTRAP_DRAWS, len(seed_means)), replace=True).mean(
        axis=1
    )
    contrast = {
        "positive_seed_cluster_eb_minus_fixed_gain": float(seed_means.mean()),
        "positive_seed_cluster_ci95_low": float(np.quantile(boot, 0.025)),
        "positive_seed_cluster_ci95_high": float(np.quantile(boot, 0.975)),
        "seed_clusters": len(seed_means),
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }
    output = ROOT / "reports/empirical_bernstein_comparison.md"
    output.write_text(
        "\n".join(
            [
                "# Scout OPE empirical-Bernstein development comparison",
                "",
                "Exploratory comparison only. Zero-signal promotion rates are diagnostics, not null calibration.",
                "The EB-CS targets average conditional certification-period value; future utility is evaluator-known and requires transport assumptions.",
                "",
                f"Protocol SHA-256: `{protocol['sha256']}`. Seed block: {manifest['configuration']['seed_offset']}–{manifest['configuration']['seed_end_inclusive']}.",
                "",
                pd.DataFrame(rows).to_markdown(index=False, floatfmt=".5f"),
                "",
                "## Paired positive-signal future-utility contrast",
                "",
                pd.DataFrame([contrast]).to_markdown(index=False, floatfmt=".5f"),
                "",
                f"Integrity: {len(detail):,} expected rows; {len(ope):,} eventwise rows; 0 label-cap violations.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(output)
    print(pd.DataFrame(rows).to_string(index=False))
    print(contrast)


if __name__ == "__main__":
    main()
