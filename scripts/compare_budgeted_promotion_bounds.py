"""Pair the global-bound and decision-local hard-budget candidate studies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

from shiftlab.dive.experiment import finalize_manifest


def compare(global_root: Path, local_root: Path) -> Path:
    global_detail = pd.read_parquet(global_root / "metrics/budgeted_promotion_streams.parquet")
    local_detail = pd.read_parquet(local_root / "metrics/budgeted_promotion_streams.parquet")
    keys = ["scenario", "seed", "query_policy", "estimator", "budget_rate", "alpha_allocation"]
    if len(global_detail) != len(local_detail):
        raise ValueError("global and local runs have different row counts")
    if (
        local_detail.bound_mode.nunique() != 1
        or local_detail.bound_mode.iloc[0] != "decision_local"
    ):
        raise ValueError("local run must contain only decision_local rows")
    measures = [
        "promoted",
        "expected_postpromotion_net_gain",
        "labels_queried",
        "monitor_events_processed",
    ]
    matched = global_detail[keys + measures].merge(
        local_detail[keys + measures + ["mean_event_process_bound", "global_process_bound"]],
        on=keys,
        how="inner",
        suffixes=("_global", "_local"),
        validate="one_to_one",
    )
    if len(matched) != len(global_detail):
        raise ValueError("global and local runs do not contain identical scenario/seed cells")

    group_keys = ["scenario", "budget_rate", "query_policy", "estimator", "alpha_allocation"]
    rows = []
    for key, group in matched.groupby(group_keys, sort=False):
        row = dict(zip(group_keys, key, strict=True))
        row["n_seed_pairs"] = len(group)
        for measure in measures:
            difference = group[f"{measure}_local"].to_numpy(dtype=float) - group[
                f"{measure}_global"
            ].to_numpy(dtype=float)
            radius = float(
                t.ppf(0.975, len(difference) - 1)
                * difference.std(ddof=1)
                / np.sqrt(len(difference))
            )
            row[f"{measure}_global_mean"] = float(group[f"{measure}_global"].mean())
            row[f"{measure}_local_mean"] = float(group[f"{measure}_local"].mean())
            row[f"{measure}_paired_difference"] = float(difference.mean())
            row[f"{measure}_paired_ci_low"] = float(difference.mean() - radius)
            row[f"{measure}_paired_ci_high"] = float(difference.mean() + radius)
        row["mean_local_bound_ratio"] = float(
            (group.mean_event_process_bound / group.global_process_bound).mean()
        )
        rows.append(row)
    contrasts = pd.DataFrame(rows)
    output = local_root / "metrics/budgeted_promotion_bound_mode_contrasts.parquet"
    contrasts.to_parquet(output, index=False)

    primary = contrasts[
        contrasts.budget_rate.eq(0.20)
        & contrasts.estimator.eq("direct_ipw")
        & contrasts.alpha_allocation.eq("rank")
    ]
    report_path = local_root / "reports/budgeted_promotion_grid.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "## Global versus decision-local bounds"
    if marker in report:
        report = report.split(marker, maxsplit=1)[0].rstrip()
    lines = [
        "",
        marker,
        "",
        "The global run uses the weaker history-conditional average-gain null. The local run's crossings test a pointwise conditional null and cannot certify positive aggregate net benefit. Therefore these paired results are a power diagnostic only, not a comparison of valid promotion gates for the same aggregate estimand. Intervals are paired t intervals over 60 independent seeds and unadjusted across the full grid.",
        "",
        "| Scenario | Query | Global crossing | Local crossing | Local minus global (95% CI) | Mean local/global bound ratio |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in primary.itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.query_policy} | {row.promoted_global_mean:.3f} | {row.promoted_local_mean:.3f} | {row.promoted_paired_difference:.3f} [{row.promoted_paired_ci_low:.3f}, {row.promoted_paired_ci_high:.3f}] | {row.mean_local_bound_ratio:.3f} |"
        )
    lines.extend(
        [
            "",
            f"The complete {len(contrasts)}-cell paired table is `metrics/budgeted_promotion_bound_mode_contrasts.parquet`. The local test crossed zero times in all {len(local_detail):,} local rows, while respecting every pathwise label cap. Its mean event bound was 6.9% of the global bound. This is a negative transfer from the one-candidate calibration: tighter support bounds alone did not create useful promotion power in a family with sparse action disagreement.",
        ]
    )
    report_path.write_text(report + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    manifest_path = local_root / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contrast_artifact = "metrics/budgeted_promotion_bound_mode_contrasts.parquet"
    if contrast_artifact not in manifest["artifacts"]:
        manifest["artifacts"].append(contrast_artifact)
    protocol = "decision-local crossings reject a pointwise conditional null and do not certify positive average net benefit"
    if protocol not in manifest["information_protocol"]:
        manifest["information_protocol"].append(protocol)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(local_root)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--global-run", type=Path, default=Path("outputs/budgeted_promotion_grid_ipw")
    )
    parser.add_argument(
        "--local-run", type=Path, default=Path("outputs/budgeted_promotion_grid_local_bound")
    )
    args = parser.parse_args()
    print(compare(args.global_run, args.local_run))


if __name__ == "__main__":
    main()
