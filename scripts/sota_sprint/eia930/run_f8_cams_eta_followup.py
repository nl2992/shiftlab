"""Run a bounded eta-scale screen for CAMS on the fixed EIA F8 development panel."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_cams_eta_followup_20261107"
PROFILE = (
    ROOT
    / "research/scoped_method/pilots/eia930_f8_all_ba_development_20261107/DATASET_PROFILE.json"
)
sys.path.insert(0, str(ROOT / "scripts/sota_sprint/eia930"))
sys.path.insert(0, str(ROOT / "scripts/failure_atlas_v2_flq"))
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

from profile_all_balancing_authorities import load_all
from registry import EXTRA, IMPORT_ERRORS
from run_f8_all_ba_policy_development import (
    ALPHA,
    BUDGET,
    DELAY,
    LABEL_PRICE,
    SWITCH_COST,
    T,
    episodes,
    model_pair,
)
from scaled_cams import EXTRA as ETA_EXTRA
from simulator import run_episode
from suite import build_suite

SEEDS = 5
SEED_BASE = 2026110714
POLICIES = ("cams_adapter", "cams_max_adapter", "cams_eta_1p5", "cams_eta_2", "cams_eta_3")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    records_path = PILOT / "episode_policy_records.jsonl"
    manifest_path = PILOT / "run_manifest.json"
    if records_path.exists() or manifest_path.exists():
        raise SystemExit("follow-up outcomes exist; refusing to overwrite")
    profile = json.loads(PROFILE.read_text())
    if not profile["gate_pass"]:
        raise SystemExit("the frozen profile gate failed")
    data = load_all()
    full_extra = {**EXTRA, **ETA_EXTRA}
    if IMPORT_ERRORS:
        raise RuntimeError(f"registry import errors: {IMPORT_ERRORS}")
    if not set(POLICIES) <= set(full_extra) | {"cams_adapter"}:
        raise RuntimeError("CAMS follow-up factory is missing")
    output = []
    global_episode = 0
    for ba in profile["matching_bas"]:
        times, predictions, labels = model_pair(ba, data[ba])
        expected = profile["profiles"][ba]
        disagreement = predictions[:, 0] != predictions[:, 1]
        if len(times) != expected["eligible_dev_events"]:
            raise RuntimeError(f"eligible row count changed for {ba}")
        if abs(float(disagreement.mean()) - expected["disagreement_frequency"]) > 1e-12:
            raise RuntimeError(f"disagreement rate changed for {ba}")
        conditional = float((predictions[disagreement, 1] == labels[disagreement]).mean())
        if abs(conditional - expected["challenger_correct_on_disagreements"]) > 1e-12:
            raise RuntimeError(f"conditional accuracy changed for {ba}")
        for local_episode, (start_event, start_time, pred_ep, label_ep) in enumerate(
            episodes(times, predictions, labels)
        ):
            for seed_id in range(SEEDS):
                seed = SEED_BASE + seed_id
                suite = build_suite(
                    T,
                    BUDGET,
                    SWITCH_COST,
                    LABEL_PRICE,
                    ALPHA,
                    DELAY,
                    global_episode,
                    seed,
                    names=list(POLICIES),
                    extra=full_extra,
                )
                for policy in suite:
                    res = run_episode(
                        policy,
                        model_predictions=pred_ep,
                        labels=label_ep,
                        delay=DELAY,
                        budget=BUDGET,
                        label_price=LABEL_PRICE,
                        switch_cost=SWITCH_COST,
                        trace=True,
                    )
                    trace = res.records
                    output.append(
                        {
                            "ba": ba,
                            "episode": global_episode,
                            "local_episode": local_episode,
                            "start_event_in_eligible_run": int(start_event),
                            "start_time_utc": start_time.isoformat(),
                            "policy_seed": seed_id,
                            "policy": policy.name,
                            "net_cost": res.net_cost,
                            "prediction_loss": res.prediction_loss,
                            "labels": res.requested_labels,
                            "label_cost": LABEL_PRICE * res.requested_labels,
                            "switches": res.deployment_switches,
                            "switch_cost": SWITCH_COST * res.deployment_switches,
                            "promotions": sum(
                                trace[i].get("deployed_model", 0) == 1
                                and (i == 0 or trace[i - 1].get("deployed_model", 0) == 0)
                                for i in range(len(trace))
                            ),
                            "rollbacks": sum(
                                trace[i].get("deployed_model", 0) == 0
                                and i > 0
                                and trace[i - 1].get("deployed_model", 0) == 1
                                for i in range(len(trace))
                            ),
                            "first_promotion": next(
                                (
                                    i
                                    for i, row in enumerate(trace)
                                    if row.get("deployed_model", 0) == 1
                                ),
                                None,
                            ),
                        }
                    )
            global_episode += 1
    records_path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in output)
    )
    source_paths = (
        Path(__file__),
        Path(__file__).with_name("scaled_cams.py"),
        ROOT / "scripts/promising_directions/sota/competitors/cams.py",
        ROOT / "scripts/failure_atlas_v2_flq/suite.py",
        ROOT / "scripts/sota_sprint/fam_d.py",
        ROOT / "scripts/sota_sprint/registry.py",
        ROOT / "scripts/promising_directions/sota/simulator.py",
    )
    manifest = {
        "protocol": "eia930_f8_cams_eta_followup_20261107/PROTOCOL.md",
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in source_paths},
        "raw_file_sha256": json.loads(
            (
                ROOT
                / "research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json"
            ).read_text()
        )["raw_file_sha256"],
        "bas": profile["matching_bas"],
        "policies": POLICIES,
        "seeds": SEEDS,
        "seed_base": SEED_BASE,
        "episodes": global_episode,
        "rows": len(output),
        "contract": {
            "T": T,
            "B": BUDGET,
            "delay": DELAY,
            "label_price": LABEL_PRICE,
            "switch_cost": SWITCH_COST,
            "alpha": ALPHA,
        },
        "note": "Bounded development-only hyperparameter screen on 2022-2023; no 2024+ data used.",
    }
    PILOT.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {"episodes": global_episode, "rows": len(output), "bas": len(profile["matching_bas"])},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
