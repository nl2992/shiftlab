"""Summarize evaluator-known monitor value for validation-selected context policies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from shiftlab.dive.experiment import finalize_manifest


def analyze(run_root: Path) -> Path:
    detail_path = run_root / "metrics" / "context_budgeted_promotion_streams.parquet"
    if not detail_path.is_file():
        raise FileNotFoundError(f"missing seed-level metrics: {detail_path}")
    detail = pd.read_parquet(detail_path)
    required = {
        "alpha_allocation",
        "budget_rate",
        "context_target_prevalence",
        "context_signal_strength",
        "context_proxy_error",
        "selected_candidate_monitor_expected_net_gain",
        "expected_postpromotion_net_gain",
        "promoted",
        "selected_candidates_by_context",
    }
    missing = required - set(detail.columns)
    if missing:
        raise ValueError(f"metrics are missing required diagnostic columns: {sorted(missing)}")
    composite = detail[detail.alpha_allocation.eq("validation_context_policy")].copy()
    if composite.empty:
        raise ValueError("metrics contain no validation-selected context-policy rows")
    composite["active_contexts_at_selection"] = composite.selected_candidates_by_context.map(
        lambda value: sum(candidate is not None for candidate in json.loads(value).values())
    )
    composite["future_gain_when_promoted"] = composite.expected_postpromotion_net_gain.where(
        composite.promoted
    )
    grouped = composite.groupby(
        [
            "budget_rate",
            "context_target_prevalence",
            "context_signal_strength",
            "context_proxy_error",
        ],
        as_index=False,
        sort=True,
    ).agg(
        n_seeds=("promoted", "size"),
        mean_true_monitor_net_gain_per_event=(
            "selected_candidate_monitor_expected_net_gain",
            "mean",
        ),
        promotion_rate=("promoted", "mean"),
        mean_future_net_gain=("expected_postpromotion_net_gain", "mean"),
        mean_future_gain_when_promoted=("future_gain_when_promoted", "mean"),
        mean_active_contexts=("active_contexts_at_selection", "mean"),
    )
    metrics_path = run_root / "metrics" / "context_policy_selection_diagnostic.parquet"
    report_path = run_root / "reports" / "context_policy_selection_diagnostic.md"
    grouped.to_parquet(metrics_path, index=False)
    report_lines = [
        "# Post-hoc policy-selection diagnostic",
        "",
        "This evaluator-only diagnostic separates the selected policy's true expected net gain on the monitor stream from the later e-process decision. It was run after inspecting the development results, has no inferential intervals, and must not be treated as a registered endpoint or confirmation result.",
        "",
        "A negative `mean_true_monitor_net_gain_per_event` means source-validation selection produced a composite policy whose expected net benefit was nonpositive on the target monitor slice. This points to policy-selection mismatch; it does not by itself distinguish candidate-family limits from source-to-target selection mismatch.",
        "",
        "| Cap | Context prevalence | Signal | Proxy error | Mean true monitor net gain / event | Promotion rate | Mean future net gain | Mean future gain when promoted | Mean active contexts |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in grouped.itertuples(index=False):
        report_lines.append(
            f"| {row.budget_rate:.2f} | {row.context_target_prevalence:.2f} | "
            f"{row.context_signal_strength:.2f} | {row.context_proxy_error:.2f} | "
            f"{row.mean_true_monitor_net_gain_per_event:.4f} | {row.promotion_rate:.3f} | "
            f"{row.mean_future_net_gain:.3f} | "
            f"{(row.mean_future_gain_when_promoted if pd.notna(row.mean_future_gain_when_promoted) else 0.0):.3f} | "
            f"{row.mean_active_contexts:.2f} |"
        )
    report_lines.extend(
        [
            "",
            "These aggregates use simulator evaluator truth, which is not available to a deployed learner. The source-validation policy is frozen before monitoring. A positive true monitor mean with a low promotion rate is consistent with limited monitor power; a nonpositive mean indicates the selected policy itself is not useful under that target profile. Both are descriptive mechanisms for designing the next study.",
            "",
        ]
    )
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    manifest_path = run_root / "reports" / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for artifact in (
            "metrics/context_policy_selection_diagnostic.parquet",
            "reports/context_policy_selection_diagnostic.md",
        ):
            if artifact not in manifest["artifacts"]:
                manifest["artifacts"].append(artifact)
        manifest["artifacts"].sort()
        manifest["posthoc_diagnostic"] = {
            "purpose": "separate selected-policy target value from monitor certification",
            "inferential_status": "descriptive only; selected after inspecting development results",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        finalize_manifest(run_root)
    return report_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    print(analyze(args.run_root), flush=True)


if __name__ == "__main__":
    main()
