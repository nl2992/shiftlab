"""Evaluate fixed incumbent/challenger controls on the already-run EIA F8 episodes."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/scoped_method/pilots/eia930_f8_static_challenger_control_20261107"
PROFILE = (
    ROOT
    / "research/scoped_method/pilots/eia930_f8_all_ba_development_20261107/DATASET_PROFILE.json"
)
PANEL_RECORDS = (
    ROOT
    / "research/scoped_method/pilots/eia930_f8_all_ba_policy_development_20261107/episode_policy_records.jsonl"
)
sys.path.insert(0, str(ROOT / "scripts/sota_sprint/eia930"))
sys.path.insert(0, str(ROOT / "scripts/failure_atlas_v2_flq"))
sys.path.insert(0, str(ROOT / "scripts/sota_sprint"))

from profile_all_balancing_authorities import load_all
from run_f8_all_ba_policy_development import episodes, model_pair

T, SWITCH_COST = 2000, 5.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    records = PILOT / "fixed_control_records.jsonl"
    manifest_path = PILOT / "run_manifest.json"
    if records.exists() or manifest_path.exists():
        raise SystemExit("static-control records exist; refusing to overwrite")
    profile = json.loads(PROFILE.read_text())
    data = load_all()
    panel = pd.read_json(PANEL_RECORDS, lines=True)
    cams = (
        panel[panel.policy == "cams_adapter"]
        .groupby(["ba", "episode"], as_index=False)
        .agg(
            net_cost=("net_cost", "mean"),
            prediction_loss=("prediction_loss", "mean"),
            labels=("labels", "mean"),
            label_cost=("label_cost", "mean"),
            switches=("switches", "mean"),
            switch_cost=("switch_cost", "mean"),
        )
    )
    rows = []
    global_episode = 0
    for ba in profile["matching_bas"]:
        times, preds, labels = model_pair(ba, data[ba])
        expected = profile["profiles"][ba]
        dis = preds[:, 0] != preds[:, 1]
        if len(times) != expected["eligible_dev_events"]:
            raise RuntimeError(f"eligible event count mismatch: {ba}")
        if abs(float(dis.mean()) - expected["disagreement_frequency"]) > 1e-12:
            raise RuntimeError(f"disagreement rate mismatch: {ba}")
        accuracy = float((preds[dis, 1] == labels[dis]).mean())
        if abs(accuracy - expected["challenger_correct_on_disagreements"]) > 1e-12:
            raise RuntimeError(f"conditional accuracy mismatch: {ba}")
        for local_ep, (start_event, start_time, p_ep, y_ep) in enumerate(
            episodes(times, preds, labels)
        ):
            incumbent_loss = float((p_ep[:, 0] != y_ep).sum())
            challenger_loss = float((p_ep[:, 1] != y_ep).sum())
            rows.extend(
                [
                    {
                        "ba": ba,
                        "episode": global_episode,
                        "local_episode": local_ep,
                        "start_time_utc": start_time.isoformat(),
                        "policy": "fixed_incumbent",
                        "net_cost": incumbent_loss,
                        "prediction_loss": incumbent_loss,
                        "labels": 0,
                        "label_cost": 0.0,
                        "switches": 0,
                        "switch_cost": 0.0,
                    },
                    {
                        "ba": ba,
                        "episode": global_episode,
                        "local_episode": local_ep,
                        "start_time_utc": start_time.isoformat(),
                        "policy": "fixed_challenger",
                        "net_cost": challenger_loss + SWITCH_COST,
                        "prediction_loss": challenger_loss,
                        "labels": 0,
                        "label_cost": 0.0,
                        "switches": 1,
                        "switch_cost": SWITCH_COST,
                    },
                ]
            )
            global_episode += 1
    df = pd.DataFrame(rows)
    if global_episode != 81 or df.groupby(["ba", "episode"]).size().ne(2).any():
        raise RuntimeError("static controls do not cover the full frozen 81-episode panel")
    cams_keys = set(map(tuple, cams[["ba", "episode"]].to_numpy()))
    static_keys = set(map(tuple, df[["ba", "episode"]].drop_duplicates().to_numpy()))
    if cams_keys != static_keys:
        raise RuntimeError("CAMS and fixed controls do not cover identical episode keys")
    df.to_json(records, orient="records", lines=True)
    source_manifest = json.loads(
        (
            ROOT
            / "research/scoped_method/pilots/eia930_f8_development_20261107/source_manifest.json"
        ).read_text()
    )
    scripts = [
        Path(__file__),
        ROOT / "scripts/sota_sprint/eia930/profile_all_balancing_authorities.py",
        ROOT / "scripts/sota_sprint/eia930/run_f8_all_ba_policy_development.py",
    ]
    manifest_path.write_text(
        json.dumps(
            {
                "protocol": "eia930_f8_static_challenger_control_20261107/PROTOCOL.md",
                "git_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "tree": subprocess.check_output(
                    ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
                ).strip(),
                "script_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in scripts},
                "raw_file_sha256": source_manifest["raw_file_sha256"],
                "bas": profile["matching_bas"],
                "episodes": global_episode,
                "rows": len(df),
                "switch_cost": SWITCH_COST,
                "comparison": "fixed controls versus CAMS episode means from the frozen 2022-2023 development replay",
                "holdout_opened": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {"bas": len(profile["matching_bas"]), "episodes": global_episode, "rows": len(df)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
