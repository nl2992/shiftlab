"""Validate and finalize records from the completed EIA policy run after manifest-write failure."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_all_ba_policy_development_20261107"
RUN_COMMIT = "b3e8bfb27cadee8e0180df9051b916805f9ea74f"
POLICIES = (
    "PFA-SR:gated_deployment",
    "rmm:gated_deployment+RMM",
    "SMCS+retain-incumbent",
    "xu_acquisition_only",
    "gated_deployment",
    "gated_adaptive_range",
    "E_rb:gated_deployment",
    "cams_adapter",
    "online_llm_picker",
    "model_selector_causal",
    "model_picker_adapter",
    "gong_zhang_paid_obs",
    "qiu_delayed_movement",
    "variance_min_ipw",
    "economic_replacement",
    "CONTROL_never_switch",
)


def commit_bytes(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{RUN_COMMIT}:{path}"], cwd=ROOT)


def main() -> None:
    records_path = PILOT / "episode_policy_records.jsonl"
    manifest_path = PILOT / "run_manifest.json"
    if manifest_path.exists():
        raise SystemExit("manifest already exists; refusing to overwrite")
    profile = json.loads(
        (PILOT.parent / "eia930_f8_all_ba_development_20261107/DATASET_PROFILE.json").read_text()
    )
    rows = [json.loads(line) for line in records_path.read_text().splitlines()]
    expected_bas = set(profile["matching_bas"])
    expected_keys = {
        (ba, ep, seed, policy)
        for ba, ep, seed in {(row["ba"], row["episode"], row["policy_seed"]) for row in rows}
        for policy in POLICIES
    }
    actual_keys = {(row["ba"], row["episode"], row["policy_seed"], row["policy"]) for row in rows}
    if len(rows) != len(actual_keys) or actual_keys != expected_keys:
        raise RuntimeError("duplicate or missing BA/episode/seed/policy outcome rows")
    if {row["ba"] for row in rows} != expected_bas:
        raise RuntimeError("recorded BA panel differs from frozen profile matches")
    if {row["policy"] for row in rows} != set(POLICIES):
        raise RuntimeError("recorded policy panel differs from frozen protocol")
    if {row["policy_seed"] for row in rows} != set(range(5)):
        raise RuntimeError("recorded paired seed set differs from protocol")
    expected_episodes = sum(
        profile["profiles"][ba]["complete_contiguous_2000_hour_blocks"] for ba in expected_bas
    )
    actual_episodes = len({(row["ba"], row["episode"]) for row in rows})
    if actual_episodes != expected_episodes:
        raise RuntimeError(
            f"recorded episode count {actual_episodes} != profile blocks {expected_episodes}"
        )
    residual = max(
        abs(row["net_cost"] - row["prediction_loss"] - row["label_cost"] - row["switch_cost"])
        for row in rows
    )
    if residual > 1e-10:
        raise RuntimeError(f"cost accounting residual {residual}")
    if max(int(row["start_time_utc"][:4]) for row in rows) > 2023:
        raise RuntimeError("outcomes include time beyond the development window")
    source_manifest = json.loads(
        (
            ROOT
            / "research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json"
        ).read_text()
    )
    script_paths = (
        "scripts/sota_sprint/eia930/run_f8_all_ba_policy_development.py",
        "scripts/sota_sprint/eia930/profile_all_balancing_authorities.py",
        "scripts/failure_atlas_v2_flq/suite.py",
        "scripts/sota_sprint/registry.py",
        "scripts/promising_directions/sota/simulator.py",
        "scripts/sota_sprint/pfa_srr_baseline.py",
        "scripts/sota_sprint/fam_e.py",
        "scripts/failure_atlas_v2_flq/strong_hosts.py",
    )
    tree = subprocess.check_output(
        ["git", "rev-parse", f"{RUN_COMMIT}^{{tree}}"], cwd=ROOT, text=True
    ).strip()
    manifest = {
        "protocol": "eia930_f8_all_ba_policy_development_20261107/PROTOCOL.md",
        "run_source_commit": RUN_COMMIT,
        "run_source_tree": tree,
        "respondents": sorted(expected_bas),
        "periods": source_manifest["periods"],
        "raw_file_sha256": source_manifest["raw_file_sha256"],
        "source_sha256_at_run_commit": {
            path: hashlib.sha256(commit_bytes(path)).hexdigest() for path in script_paths
        },
        "policies": POLICIES,
        "contract": {
            "T": 2000,
            "B": 200,
            "label_price": 0.05,
            "switch_cost": 5.0,
            "alpha": 0.05,
            "delay": 1,
            "paired_seeds_per_episode": 5,
            "seed_base": 2026110711,
        },
        "episodes": actual_episodes,
        "rows": len(rows),
        "cost_identity_max_abs_residual": residual,
        "runtime_environment_at_finalization": {
            "python": subprocess.check_output(
                ["uv", "run", "python", "--version"], cwd=ROOT, text=True
            ).strip(),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "finalization_note": (
            "The policy simulations and episode records completed. Initial runner exit was nonzero "
            "only after writing all 6,480 rows, while hashing a nonexistent scripts/sota_sprint/strong_hosts.py. "
            "The executed policy module is scripts/failure_atlas_v2_flq/strong_hosts.py. This manifest "
            "was reconstructed from the recorded rows and immutable run commit; no outcomes were rerun or changed."
        ),
        "feedback_note": "Revised historical EIA values; simulated one-hour release; no 2024+ outcomes used.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "rows": len(rows),
                "episodes": manifest["episodes"],
                "cost_residual": residual,
                "run_commit": RUN_COMMIT,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
