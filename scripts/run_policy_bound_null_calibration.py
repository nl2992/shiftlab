"""Run the frozen CUDA calibration of method-specific monitor support bounds."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from shiftlab.dive.hard_budget import HardBudgetConfig, run_hard_budget

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/policy_bound_null_calibration_500"
PROTOCOL = Path("docs/policy_bound_null_calibration_protocol.md")
METHODS = (
    "uniform_proxy",
    "variance_proxy",
    "decision_value_proxy",
    "cost_variance_proxy",
    "cost_stabilized_proxy",
)
SCENARIOS = ("stationary", "benign_nuisance")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite frozen run directory: {OUTPUT}")
    try:
        protocol_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("run the committed protocol from a Git checkout") from exc

    config = HardBudgetConfig(
        n=3200,
        d=16,
        seeds=500,
        seed_offset=54_000_000,
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
        "source_git_commit_at_run": protocol_commit,
        "simulation_method_streams_expected": len(METHODS) * len(SCENARIOS) * 500,
        "visuals_generated": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
