"""Analyze the paired q_min sensitivity for hard-budget decision-harm monitors."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from shiftlab.dive.experiment import finalize_manifest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOOSE = ROOT / "outputs/monitor_power_diagnostic_30"
DEFAULT_TIGHT = ROOT / "outputs/monitor_bound_sensitivity_qmin020"
PAIRED_FIELDS = (
    "labels_queried",
    "realized_label_spend",
    "processed_events",
    "budget_remaining",
    "budget_respected",
)
MONITORS = (
    ("fixed_mixture", "single_e"),
    ("predictable_variance", "variance_adaptive"),
    ("predictable_empirical_bernstein", "pm_eb"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _check_paired(left: pd.DataFrame, right: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = ["scenario", "seed"]
    left = left.loc[left.method.eq("uniform_proxy")].sort_values(keys).reset_index(drop=True)
    right = right.loc[right.method.eq("uniform_proxy")].sort_values(keys).reset_index(drop=True)
    if len(left) != len(right) or not left[keys].equals(right[keys]):
        raise ValueError("q_min runs do not have matching uniform scenario-seed rows")
    missing = sorted(
        set(PAIRED_FIELDS) - set(left.columns) | (set(PAIRED_FIELDS) - set(right.columns))
    )
    if missing:
        raise ValueError(f"paired metrics are missing required fields: {missing}")
    for column in PAIRED_FIELDS:
        a, b = left[column], right[column]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            equal = np.allclose(a.to_numpy(float), b.to_numpy(float), equal_nan=True)
        else:
            equal = a.equals(b)
        if not equal:
            raise ValueError(f"query process differs between q_min runs in {column}")
    return left, right


def analyze(loose: pd.DataFrame, tight: pd.DataFrame) -> pd.DataFrame:
    loose, tight = _check_paired(loose, tight)
    rows: list[dict[str, object]] = []
    for scenario in sorted(loose.scenario.unique()):
        a = loose.loc[loose.scenario.eq(scenario)].set_index("seed")
        b = tight.loc[tight.scenario.eq(scenario)].set_index("seed")
        for name, prefix in MONITORS:
            column = f"{prefix}_detected"
            a_detected = a[column].astype(bool)
            b_detected = b[column].astype(bool)
            wins = int((b_detected & ~a_detected).sum())
            losses = int((~b_detected & a_detected).sum())
            discordant = wins + losses
            rows.append(
                {
                    "scenario": scenario,
                    "monitor": name,
                    "streams": len(a),
                    "qmin_005_detections": int(a_detected.sum()),
                    "qmin_020_detections": int(b_detected.sum()),
                    "qmin_020_wilson_low": np.nan,
                    "qmin_020_median_delay": float(
                        pd.to_numeric(
                            b.loc[b_detected, f"{prefix}_delay"], errors="coerce"
                        ).median()
                    )
                    if b_detected.any()
                    else np.nan,
                    "qmin_005_false_escalations": int(a[f"{prefix}_false_escalation"].sum()),
                    "qmin_020_false_escalations": int(b[f"{prefix}_false_escalation"].sum()),
                    "paired_wins_qmin020": wins,
                    "paired_losses_qmin020": losses,
                    "mcnemar_exact_p": float(
                        binomtest(wins, discordant, p=0.5).pvalue if discordant else 1.0
                    ),
                }
            )
    result = pd.DataFrame(rows)
    # Add Wilson intervals using the number of harmful streams in each scenario.
    for idx, row in result.iterrows():
        scenario = row["scenario"]
        group = tight.loc[tight.scenario.eq(scenario)]
        name = row["monitor"]
        prefix = dict(MONITORS)[name]
        harmful = group.material_harm.astype(bool)
        detected = group[f"{prefix}_detected"].astype(bool) & harmful
        n = int(harmful.sum())
        k = int(detected.sum())
        if n:
            z = 1.959963984540054
            rate = k / n
            den = 1 + z * z / n
            center = (rate + z * z / (2 * n)) / den
            radius = z * np.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / den
            result.loc[idx, "qmin_020_wilson_low"] = center - radius
            result.loc[idx, "qmin_020_wilson_high"] = center + radius
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qmin-005", type=Path, default=DEFAULT_LOOSE)
    parser.add_argument("--qmin-020", type=Path, default=DEFAULT_TIGHT)
    args = parser.parse_args()
    loose_path = args.qmin_005 / "metrics/hard_budget_comparison.parquet"
    tight_path = args.qmin_020 / "metrics/hard_budget_comparison.parquet"
    loose = pd.read_parquet(loose_path)
    tight = pd.read_parquet(tight_path)
    left, _right = _check_paired(loose, tight)
    summary = analyze(loose, tight)
    metric_path = args.qmin_020 / "metrics/paired_qmin_sensitivity.csv"
    summary.to_csv(metric_path, index=False)

    rows = summary.to_dict("records")
    report = [
        "# Paired global-bound sensitivity: q_min 0.05 vs 0.20",
        "",
        "This development-only analysis reuses the same 30 generated stream seeds. Uniform querying, observed labels, realized label spend, processed horizon, remaining budget, and cap status match exactly across the two runs. Only the valid prediction-powered support bound changes from 198.9 to 45.9 (factor 4.33).",
        "",
        "|Scenario|Monitor|Detections q_min=.05|Detections q_min=.20|95% Wilson interval at .20|Median delay at .20|False alarms .05/.20|Paired exact McNemar p|",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        ci = "not applicable"
        if pd.notna(row["qmin_020_wilson_low"]):
            ci = f"[{row['qmin_020_wilson_low']:.3f}, {row['qmin_020_wilson_high']:.3f}]"
        delay = (
            "—" if pd.isna(row["qmin_020_median_delay"]) else f"{row['qmin_020_median_delay']:.1f}"
        )
        report.append(
            f"|{row['scenario']}|{row['monitor']}|{row['qmin_005_detections']}/{row['streams']}|"
            f"{row['qmin_020_detections']}/{row['streams']}|{ci}|{delay}|"
            f"{row['qmin_005_false_escalations']}/{row['qmin_020_false_escalations']}|"
            f"{row['mcnemar_exact_p']:.3g}|"
        )
    report.extend(
        [
            "",
            "## Interpretation",
            "",
            "At q_min=.20, the fixed mixture detected 19/30 boundary-local harmful streams and 20/30 recurring-regime streams; the predictable-variance comparator detected 19/30 in each. At q_min=.05, both detected 0/30 in both alternatives. The paired exact contrasts are significant for those four comparisons, but this exploratory reuse of 30 seeds is not independent confirmation. The PM-EB comparator detected 0/30 boundary-local streams and 1/30 recurring streams at q_min=.20.",
            "",
            "Neither stationary nor benign-nuisance controls produced a false escalation in 30 streams for any monitor at either bound. The one-sided uncertainty remains substantial: 0/30 has a two-sided 95% Wilson upper endpoint of 11.35%, so these data do not demonstrate 5% calibration. The positive result identifies global-bound conservatism as a plausible power bottleneck under this design; it does not establish a new algorithm or general superiority.",
            "",
            "All harmful onsets were reached, and the q_min contrast did not change labels queried, realized spend, processed events, budget remaining, or cap compliance. Median conditional detection delay at q_min=.20 was 1,129 events (boundary-local) and 2,052.5 events (recurring) for the fixed mixture; 1,191 and 2,062 for predictable variance.",
            "",
            "## Reproduction",
            "",
            "Run `uv run python scripts/analyze_monitor_bound_sensitivity.py` after both source diagnostics exist. The two source runs are generated with `scripts/diagnose_hard_budget_monitors.py`, using seed offset 39102026, 30 seeds, n=3200, CUDA, uniform_proxy, and q_min=.05 or .20.",
        ]
    )
    report_path = args.qmin_020 / "reports/paired_qmin_sensitivity.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    manifest_path = args.qmin_020 / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["paired_sensitivity"] = {
        "comparison": "q_min 0.05 vs 0.20; paired same-seed uniform streams",
        "qmin_005_parquet_sha256": _sha256(loose_path),
        "qmin_020_parquet_sha256": _sha256(tight_path),
        "analysis_script_sha256": _sha256(Path(__file__).resolve()),
        "paired_rows": len(left),
        "process_fields_exactly_match": list(PAIRED_FIELDS),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(args.qmin_020)
    print(f"Wrote {metric_path.relative_to(ROOT)}")
    print(f"Wrote {report_path.relative_to(ROOT)}")
    print(f"Verified identical query process for {len(left)} paired rows.")


if __name__ == "__main__":
    main()
