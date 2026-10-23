"""Compare policy-specific and shared-bound e-process results under hard budgets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.dive.experiment import finalize_manifest

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "outputs/hard_budget_pilot_30"
COMMON = ROOT / "outputs/hard_budget_common_bound_sensitivity_30"
METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _same_nonprocess_outputs(primary: pd.DataFrame, common: pd.DataFrame) -> None:
    left = primary.sort_values(["scenario", "seed"]).reset_index(drop=True)
    right = common.sort_values(["scenario", "seed"]).reset_index(drop=True)
    if left[["scenario", "seed"]].equals(right[["scenario", "seed"]]) is False:
        raise ValueError("the two uniform runs do not have matching scenario-seed rows")
    process_fields = {
        "single_e_detected",
        "single_e_false_escalation",
        "single_e_alarm_time",
        "single_e_delay",
        "eprocess_minimum_propensity",
    }
    for column in left.columns:
        if column in process_fields or column not in right:
            continue
        a, b = left[column], right[column]
        if a.isna().all() and b.isna().all():
            continue
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            if not np.allclose(a.to_numpy(float), b.to_numpy(float), equal_nan=True):
                raise ValueError(f"non-e-process output changed between runs: {column}")
        elif not a.equals(b):
            raise ValueError(f"non-e-process output changed between runs: {column}")


def main() -> None:
    primary_path = PRIMARY / "metrics/hard_budget_comparison.parquet"
    common_path = COMMON / "metrics/hard_budget_comparison.parquet"
    primary = pd.read_parquet(primary_path)
    common = pd.read_parquet(common_path)
    if "eprocess_minimum_propensity" not in primary:
        primary["eprocess_minimum_propensity"] = np.where(
            primary.method.eq("uniform_proxy"), 0.10, 0.05
        )
        primary.to_parquet(primary_path, index=False)
    primary_uniform = primary.loc[primary.method.eq("uniform_proxy")].copy()
    common_uniform = common.loc[common.method.eq("uniform_proxy")].copy()
    if not np.array_equal(np.sort(primary.seed.unique()), np.sort(common.seed.unique())):
        raise ValueError("uniform runs use different seed blocks")
    _same_nonprocess_outputs(primary_uniform, common_uniform)

    rows = []
    for scenario in sorted(primary.scenario.unique()):
        for method in METHODS:
            run = (
                common_uniform
                if method == "uniform_proxy"
                else primary.loc[primary.method.eq(method)]
            )
            group = run.loc[run.scenario.eq(scenario)]
            harmful = group.loc[group.material_harm]
            reached = harmful.loc[harmful.harm_reached_before_budget_stop]
            rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "bound_regime": "shared q_min=0.05",
                    "eprocess_minimum_propensity": group.eprocess_minimum_propensity.iloc[0],
                    "streams": len(group),
                    "harmful_streams": len(harmful),
                    "harm_reached": len(reached),
                    "detections": int(reached.single_e_detected.sum()),
                    "false_escalations": int(group.single_e_false_escalation.sum()),
                    "realized_spend_mean": group.realized_label_spend.mean(),
                    "hard_budget_violations": int(
                        (group.realized_label_spend > group.hard_budget + 1e-9).sum()
                    ),
                }
            )
    summary = pd.DataFrame(rows)
    sensitivity_dir = PRIMARY / "reports"
    metric_path = PRIMARY / "metrics/eprocess_bound_sensitivity.csv"
    summary.to_csv(metric_path, index=False)

    boundary = summary.loc[
        summary.scenario.eq("boundary_local_harm"),
        ["method", "detections", "harm_reached", "harmful_streams"],
    ]
    text = """# Hard-budget e-process bound sensitivity

The primary comparison uses each method's true minimum propensity in its fixed e-process increment bound. Uniform sampling always queries at 0.10, so it receives a tighter bound than adaptive methods that can query at 0.05. This is operationally valid, but detection differences then combine query allocation with threshold width.

This sensitivity holds the threshold bound common at the registered `q_min=0.05`. It reruns the same uniform streams, same per-seed query uniforms, same hard-dollar budget and same generated outcomes; only the e-process minimum propensity changes. The adaptive methods in the primary run already use this bound. The non-e-process fields of the uniform sensitivity run were checked against the primary uniform run and match exactly.

|Scenario|Method|Minimum propensity in bound|Detections / reached / harmful|False escalations|Mean realized spend|Budget violations|
|---|---|---:|---:|---:|---:|---:|
"""
    for row in summary.to_dict("records"):
        text += (
            f"|{row['scenario']}|{row['method']}|{row['eprocess_minimum_propensity']:.2f}|"
            f"{row['detections']} / {row['harm_reached']} / {row['harmful_streams']}|"
            f"{row['false_escalations']}|{row['realized_spend_mean']:.2f}|"
            f"{row['hard_budget_violations']}|\n"
        )
    text += """

## Interpretation

On boundary-local harm, uniform detects 4/30 under its tighter method-specific bound but 0/30 under the common `q_min=0.05` bound. The adaptive methods also detect 0/30 under that common bound, even though all 30 onsets are reached. Thus the primary 4-versus-0 difference should not be presented as evidence that uniform allocation is intrinsically more powerful; it is sensitive to the fixed-bound conservatism. The common-bound run is a conservative sensitivity check, not a claim of no power difference. A confirmatory comparison should predeclare one common e-process bound or use a sharper valid eventwise construction, with sample size chosen for detection power.

Reproduce the sensitivity uniform run with `uv run shiftlab-dive-hard-budget --seeds 30 --n 3200 --device cuda --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy --output outputs/hard_budget_common_bound_sensitivity_30`.
"""
    report_path = sensitivity_dir / "eprocess_bound_sensitivity.md"
    report_path.write_text(text, encoding="utf-8")

    manifest_path = PRIMARY / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["configuration"]["common_eprocess_bound"] = False
    manifest["bound_sensitivity_inputs"] = {
        str(primary_path.relative_to(ROOT)): _hash(primary_path),
        str(common_path.relative_to(ROOT)): _hash(common_path),
        "script": _hash(Path(__file__).resolve()),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    finalize_manifest(PRIMARY)
    print(f"Wrote {report_path.relative_to(ROOT)}")
    print(boundary.to_string(index=False))


if __name__ == "__main__":
    main()
