"""Run the disjoint harmful-stream comparison after its null-calibration gate passes."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "outputs/policy_bound_null_calibration_500"
OUTPUT = ROOT / "outputs/policy_bound_harm_confirmation_200"
PROTOCOL = Path("docs/policy_bound_harm_confirmation_protocol.md")
METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)
SCENARIOS = ("boundary_local_harm", "recurring_regimes", "harmful_adaptation")
CALIBRATION_METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)
CALIBRATION_SCENARIOS = ("stationary", "benign_nuisance")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calibration_passes(calibration_dir: Path) -> bool:
    """Return true only for the complete, registered ten-cell calibration pass."""
    manifest_path = calibration_dir / "reports/manifest.json"
    summary_path = calibration_dir / "analysis/policy_bound_null_calibration.csv"
    report_path = calibration_dir / "reports/policy_bound_null_calibration.md"
    if not manifest_path.is_file() or not summary_path.is_file() or not report_path.is_file():
        return False
    if "criterion is **PASS**" not in report_path.read_text(encoding="utf-8"):
        return False
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest.get("configuration", {})
    if (
        config.get("seeds") != 500
        or config.get("seed_offset") != 54_000_000
        or config.get("common_eprocess_bound") is not False
        or set(config.get("scenario_subset", ())) != set(CALIBRATION_SCENARIOS)
        or set(config.get("method_subset", ())) != set(CALIBRATION_METHODS)
        or manifest.get("resolved_device") != "cuda"
    ):
        return False
    summary = pd.read_csv(summary_path)
    primary = summary.loc[summary.monitor.eq("fixed_mixture")]
    if not {"scenario", "method", "primary_familywise_95_upper"} <= set(primary.columns):
        return False
    cells = set(zip(primary.scenario, primary.method, strict=True))
    expected = {
        (scenario, method) for scenario in CALIBRATION_SCENARIOS for method in CALIBRATION_METHODS
    }
    return bool(
        len(primary) == 10
        and cells == expected
        and primary.primary_familywise_95_upper.notna().all()
        and (primary.primary_familywise_95_upper < 0.05).all()
    )


def git_revision(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    if not calibration_passes(CALIBRATION):
        raise RuntimeError(
            "the 10-cell fixed-mixture null calibration is missing or did not pass; "
            "run the locked analyzer and review its report before this confirmation"
        )
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite frozen run directory: {OUTPUT}")

    source_commit = git_revision("rev-parse", "HEAD")
    protocol_commit = git_revision("log", "-1", "--format=%H", "--", PROTOCOL.as_posix())
    config = HardBudgetConfig(
        n=3200,
        d=16,
        seeds=200,
        seed_offset=55_000_000,
        alpha=0.05,
        harm_margin=0.10,
        budget_rate=0.20,
        q_min=0.10,
        q_max=0.80,
        monitor_comparators=("variance_adaptive", "pm_eb"),
        common_eprocess_bound=False,
        generate_figure=False,
        record_event_traces=False,
        device="cuda",
        workers=2,
        scenario_subset=SCENARIOS,
        method_subset=METHODS,
    ).validate()
    output = run_hard_budget(config, OUTPUT)
    manifest_path = output / "reports/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("resolved_device") != "cuda":
        raise RuntimeError(
            f"protocol requires CUDA; run resolved to {manifest.get('resolved_device')!r}"
        )
    manifest["run_provenance"] = {
        "protocol": PROTOCOL.as_posix(),
        "protocol_commit": protocol_commit,
        "protocol_sha256": sha256(ROOT / PROTOCOL),
        "run_script_sha256": sha256(Path(__file__).resolve()),
        "source_git_commit_at_run": source_commit,
        "calibration_report_sha256": sha256(
            CALIBRATION / "reports/policy_bound_null_calibration.md"
        ),
        "expected_stream_policy_rows": len(SCENARIOS) * len(METHODS) * 200,
        "visuals_generated": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
