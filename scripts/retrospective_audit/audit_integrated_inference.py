"""Recompute integrated confirmation's stored-seed tests and intervals."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT.parent
    / "shift-research-starter"
    / "outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1"
)
DEST = ROOT / "docs/retrospective_audit_2026_11_01/INTEGRATED_INFERENCE_RECOMPUTATION.json"


def run() -> dict[str, object]:
    frame = pd.read_parquet(SOURCE / "integrated_pipeline_seed_metrics.parquet")
    archived = pd.read_csv(SOURCE / "analysis_v3/primary_contrasts.csv")
    wide = frame.pivot(
        index=["scenario", "seed"], columns="method", values="expected_incremental_utility"
    )
    rng = np.random.default_rng(2026104101)
    raw_p = []
    rows = []
    max_error = 0.0
    for record in archived.itertuples(index=False):
        paired = (
            wide.loc[record.profile, record.treatment] - wide.loc[record.profile, record.reference]
        ).to_numpy(dtype=float)
        test = stats.ttest_1samp(paired, popmean=0.0, alternative="greater")
        sample_index = rng.integers(0, 100, size=(20_000, 100))
        boot = paired[sample_index].mean(axis=1)
        values = {
            "mean_paired_expected_utility_difference": float(paired.mean()),
            "paired_sd": float(paired.std(ddof=1)),
            "bootstrap_ci_low_95_descriptive": float(np.quantile(boot, 0.025)),
            "bootstrap_ci_high_95_descriptive": float(np.quantile(boot, 0.975)),
        }
        p = float(test.pvalue)
        raw_p.append(p)
        if np.isfinite(p):
            values["one_sided_p_raw"] = p
        for field, value in values.items():
            expected = float(getattr(record, field))
            error = abs(value - expected)
            max_error = max(max_error, error)
            if error > 1e-10:
                raise AssertionError(f"Inference mismatch: {record.profile}/{field}: {error}")
        if not np.isfinite(p) and not pd.isna(record.one_sided_p_raw):
            raise AssertionError("Degenerate p-value mismatch")
        rows.append(values)
    order = np.argsort(np.asarray(raw_p))
    adjusted = np.empty(len(rows), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(rows) - rank) * raw_p[index])
        adjusted[index] = min(1.0, running)
    critical = float(stats.t.ppf(1 - 0.05 / len(rows), df=99))
    for index, record in enumerate(archived.itertuples(index=False)):
        lower = (
            rows[index]["mean_paired_expected_utility_difference"]
            - critical * rows[index]["paired_sd"] / 10
        )
        for field, value in (
            ("holm_adjusted_p", adjusted[index]),
            ("bonferroni_simultaneous_lower_95", lower),
        ):
            error = abs(float(getattr(record, field)) - value)
            max_error = max(max_error, error)
            if error > 1e-10:
                raise AssertionError(f"Adjusted inference mismatch: {record.profile}/{field}")
    return {
        "scope": "Stored 100-seed paired vectors and registered one-sided t/Holm/Bonferroni/bootstrap formulas; no simulator replay",
        "contrasts": len(rows),
        "max_absolute_numeric_difference": max_error,
        "holm_rejections": int((adjusted < 0.05).sum()),
        "positive_point_contrasts": int(
            sum(row["mean_paired_expected_utility_difference"] > 0 for row in rows)
        ),
        "zero_point_contrasts": int(
            sum(row["mean_paired_expected_utility_difference"] == 0 for row in rows)
        ),
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result)
